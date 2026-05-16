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
  docker compose logs --tail=120 api-gateway orders-service payments-service audit-service >&2 || true
  exit 1
}

CORRELATION_ID="audit-$(date +%s)"

echo "[verify-audit-flow] starting deterministic audit runtime"
docker compose -f docker-compose.yml -f docker-compose.audit.yml --profile async up -d --build --force-recreate

wait_for_health "api-gateway" "http://localhost:8080/actuator/health"
wait_for_health "orders-service" "http://localhost:8081/actuator/health"
wait_for_health "payments-service" "http://localhost:8082/actuator/health"
wait_for_health "audit-service" "http://localhost:8085/actuator/health"

echo "[verify-audit-flow] triggering successful order"
RESPONSE=$(curl -sS -X POST http://localhost:8080/api/orders \
  -H 'Content-Type: application/json' \
  -H "X-Correlation-Id: ${CORRELATION_ID}" \
  -d '{"customerId":"audit-check","amount":42.00,"currency":"USD"}')

echo "$RESPONSE"

echo "[verify-audit-flow] checking audit logs"
docker compose logs audit-service --since=2m | grep -E 'operation=audit_event_received' | grep -E "correlation_id=${CORRELATION_ID}" >/dev/null

echo "[PASS] Audit flow verified for correlation_id=${CORRELATION_ID}"
echo "[INFO] Logs command: docker compose logs -f orders-service audit-service"
