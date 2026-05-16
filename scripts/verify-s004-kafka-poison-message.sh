#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

cleanup_orders_runtime() {
  local cleanup_rc=0
  echo "[INFO] Restoring default orders-service runtime"
  docker compose up -d --build --force-recreate orders-service
  cleanup_rc=$?
  if [[ $cleanup_rc -eq 0 ]]; then
    return 0
  fi
  echo "[WARN] Failed to restore default orders-service runtime (exit=${cleanup_rc})." >&2
}

trap cleanup_orders_runtime EXIT

wait_for_health() {
  local name="$1" url="$2"
  for _ in {1..60}; do
    local body
    body="$(curl -sS "$url" || true)"
    if printf '%s' "$body" | rg -q '"status"\s*:\s*"UP"'; then
      echo "[OK] ${name} is healthy"
      return 0
    fi
    sleep 3
  done

  echo "[FAIL] ${name} did not become healthy at ${url}" >&2
  docker compose logs --tail=120 api-gateway orders-service payments-service inventory-service redpanda >&2 || true
  exit 1
}

echo "[verify-s004] starting deterministic kafka poison runtime"
docker compose -f docker-compose.yml -f docker-compose.s004.yml --profile kafka up -d --build --force-recreate

wait_for_health "api-gateway" "http://localhost:8080/actuator/health"
wait_for_health "orders-service" "http://localhost:8081/actuator/health"
wait_for_health "payments-service" "http://localhost:8082/actuator/health"
wait_for_health "inventory-service" "http://localhost:8083/actuator/health"

output="$(./scripts/trigger-s004-kafka-poison-message.sh)"
printf '%s\n' "$output"

correlation_id="$(printf '%s\n' "$output" | rg '^correlation_id=' | sed 's/correlation_id=//')"
http_status="$(printf '%s\n' "$output" | rg '^http_status=' | sed 's/http_status=//')"

if [[ -z "$correlation_id" ]]; then
  echo "[FAIL] could not extract correlation_id from trigger output" >&2
  exit 1
fi

if [[ ! "$http_status" =~ ^2[0-9][0-9]$ ]]; then
  echo "[FAIL] expected 2xx order API status but got ${http_status}" >&2
  exit 1
fi

sleep 5

docker compose logs orders-service --since=3m | rg 'operation=kafka_event_published' | rg "$correlation_id" >/dev/null || {
  echo "[FAIL] missing orders-service kafka publish evidence for correlation_id=${correlation_id}" >&2
  exit 1
}

docker compose logs inventory-service --since=3m | rg 'operation=kafka_processing_failed' | rg "$correlation_id" >/dev/null || {
  echo "[FAIL] missing inventory-service kafka processing failure for correlation_id=${correlation_id}" >&2
  exit 1
}

docker compose logs inventory-service --since=3m | rg 'PoisonMessageException|Simulated poison message' | rg "$correlation_id" >/dev/null || {
  echo "[FAIL] missing poison-message exception evidence for correlation_id=${correlation_id}" >&2
  exit 1
}

if docker compose logs inventory-service --since=3m | rg 'operation=kafka_dlq_published' | rg "$correlation_id" >/dev/null; then
  echo "[OK] DLQ publish evidence found in inventory-service logs"
else
  if docker compose exec -T redpanda rpk topic consume order-created-dlq -n 20 -f '%h\\n%v\\n' 2>/dev/null | rg "$correlation_id" >/dev/null; then
    echo "[OK] DLQ topic evidence found in order-created-dlq"
  else
    echo "[WARN] No explicit DLQ evidence found in logs or topic sample"
  fi
fi

echo "[PASS] S004 verified for correlation_id=${correlation_id}"
echo "[INFO] Logs command: docker compose logs -f orders-service inventory-service redpanda"
