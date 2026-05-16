#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

count="${1:-20}"

cleanup_runtime() {
  local rc=0
  echo "[INFO] Restoring default orders-service and inventory-service runtime"
  if docker compose -f docker-compose.yml up -d --build --force-recreate orders-service inventory-service; then
    return 0
  fi
  rc=$?
  echo "[WARN] Failed to restore default service runtime (exit=${rc})." >&2
}
trap cleanup_runtime EXIT

wait_for_health() {
  local name="$1" url="$2"
  for _ in {1..80}; do
    body="$(curl -sS "$url" || true)"
    if printf '%s' "$body" | rg '"status"\s*:\s*"UP"' >/dev/null; then
      echo "[OK] ${name} is healthy"
      return 0
    fi
    sleep 3
  done
  echo "[FAIL] ${name} did not become healthy at ${url}" >&2
  docker compose logs --tail=200 api-gateway orders-service payments-service inventory-service redpanda >&2 || true
  exit 1
}

echo "[INFO] Starting S005 deterministic kafka lag runtime"
docker compose -f docker-compose.yml -f docker-compose.s005.yml --profile kafka up -d --build --force-recreate

wait_for_health "api-gateway" "http://localhost:8080/actuator/health"
wait_for_health "orders-service" "http://localhost:8081/actuator/health"
wait_for_health "payments-service" "http://localhost:8082/actuator/health"
wait_for_health "inventory-service" "http://localhost:8083/actuator/health"

output="$(./scripts/trigger-s005-kafka-consumer-lag.sh "${count}")"
printf '%s\n' "$output"

correlation_prefix="$(printf '%s\n' "$output" | rg '^correlation_prefix=' | sed 's/correlation_prefix=//')"
success_count="$(printf '%s\n' "$output" | rg '^success_count=' | sed 's/success_count=//')"

if [[ -z "$correlation_prefix" ]]; then
  echo "[FAIL] could not extract correlation_prefix" >&2
  exit 1
fi

if [[ -z "$success_count" || "$success_count" -lt 5 ]]; then
  echo "[FAIL] insufficient successful orders for backlog test (success_count=${success_count:-unset})" >&2
  exit 1
fi

sleep 5

published_count=$(docker compose logs orders-service --since=5m | rg "operation=kafka_event_published" | rg "${correlation_prefix}" | wc -l | tr -d ' ')
if [[ "$published_count" -lt 5 ]]; then
  echo "[FAIL] expected multiple kafka_event_published logs, got ${published_count}" >&2
  exit 1
fi

delay_count=$(docker compose logs inventory-service --since=10m | rg "operation=kafka_processing_delay_simulated" | rg "${correlation_prefix}" | wc -l | tr -d ' ')
if [[ "$delay_count" -lt 3 ]]; then
  echo "[FAIL] expected delayed consumer processing logs, got ${delay_count}" >&2
  exit 1
fi

lag_asserted=false
if docker compose exec -T redpanda rpk group describe inventory-service >/tmp/s005-group.txt 2>/tmp/s005-group.err; then
  lag_sum=$(awk '/order-created/ {sum += $NF} END {print sum+0}' /tmp/s005-group.txt)
  if [[ "$lag_sum" -gt 0 ]]; then
    lag_asserted=true
    echo "[OK] consumer_group_lag_detected lag_sum=${lag_sum}"
  else
    echo "[WARN] consumer group command succeeded but lag snapshot was 0"
  fi
else
  echo "[WARN] unable to query consumer group lag with rpk"
  cat /tmp/s005-group.err || true
fi

echo "[PASS] S005 verified for correlation_prefix=${correlation_prefix}"
if [[ "$lag_asserted" == "true" ]]; then
  echo "[PASS] Kafka consumer group lag > 0 was asserted"
else
  echo "[PASS] Deterministic delay/backlog evidence asserted (kafka_event_published + kafka_processing_delay_simulated)"
fi

echo "[INFO] Debug logs command: docker compose logs -f orders-service inventory-service redpanda"
