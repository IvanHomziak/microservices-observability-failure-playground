#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

wait_for_health() {
  local name="$1" url="$2"
  for _ in {1..60}; do
    local body
    body="$(curl -sS "$url" || true)"
    if printf '%s' "$body" | grep -Eq '"status"\s*:\s*"UP"'; then
      echo "[OK] ${name} is healthy"
      return 0
    fi
    sleep 3
  done

  echo "[FAIL] ${name} did not become healthy at ${url}" >&2
  docker compose logs --tail=120 api-gateway orders-service payments-service inventory-service redpanda >&2 || true
  exit 1
}

echo "[verify-kafka-flow] starting deterministic kafka runtime"
docker compose -f docker-compose.yml -f docker-compose.kafka.yml --profile kafka up -d --build --force-recreate

wait_for_health "api-gateway" "http://localhost:8080/actuator/health"
wait_for_health "orders-service" "http://localhost:8081/actuator/health"
wait_for_health "payments-service" "http://localhost:8082/actuator/health"
wait_for_health "inventory-service" "http://localhost:8083/actuator/health"

./scripts/trigger-kafka-success-flow.sh >/tmp/kafka-flow-response.txt
correlation_id=$(grep -Eo 'correlation_id=[^[:space:]]+' /tmp/kafka-flow-response.txt | head -n1 | sed 's/correlation_id=//')

if [[ -z "${correlation_id}" ]]; then
  echo "[FAIL] could not extract correlation_id from trigger output" >&2
  cat /tmp/kafka-flow-response.txt >&2
  exit 1
fi

sleep 3

docker compose logs orders-service --since=2m | grep -E 'operation=kafka_event_published' | grep -E "${correlation_id}" >/dev/null
docker compose logs inventory-service --since=2m | grep -E 'operation=kafka_event_consumed' | grep -E "${correlation_id}" >/dev/null

echo "[PASS] Kafka flow verified for correlation_id=${correlation_id}"
echo "[INFO] Logs command: docker compose logs -f orders-service inventory-service redpanda"
