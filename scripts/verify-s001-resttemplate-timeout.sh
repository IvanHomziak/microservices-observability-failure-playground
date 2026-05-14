#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s001-resttemplate-timeout.sh"
cd "$ROOT_DIR"

if [[ ! -x "${TRIGGER_SCRIPT}" ]]; then
  chmod +x "${TRIGGER_SCRIPT}"
fi

echo "[INFO] Starting stack with deterministic S001 payments delay override"
docker compose -f docker-compose.yml -f docker-compose.s001.yml up -d --build --force-recreate payments-service

echo "[INFO] Ensuring core services are healthy"
wait_for_health() {
  local name="$1" url="$2"
  for _ in {1..60}; do
    local body
    body="$(curl -sS "$url" || true)"
    if printf %s "$body" | grep -q '"status"\s*:\s*"UP"'; then
      echo "[OK] ${name} is healthy"
      return 0
    fi
    sleep 3
  done
  echo "[FAIL] ${name} did not become healthy at ${url}" >&2
  docker compose logs --tail=120 api-gateway orders-service payments-service >&2 || true
  exit 1
}

wait_for_health "api-gateway" "http://localhost:8080/actuator/health"
wait_for_health "orders-service" "http://localhost:8081/actuator/health"
wait_for_health "payments-service" "http://localhost:8082/actuator/health"

OUTPUT="$(${TRIGGER_SCRIPT})"
printf '%s\n' "$OUTPUT"

STATUS="$(printf '%s\n' "$OUTPUT" | awk '/response \(HTTP [0-9]{3}\):/ {gsub(/[^0-9]/, "", $0); print $0; exit}')"
if [[ "$STATUS" != "504" ]]; then
  echo "[FAIL] expected HTTP status 504, got '${STATUS:-missing}'" >&2
  exit 1
fi

if ! printf '%s\n' "$OUTPUT" | grep -q 'PAYMENT_TIMEOUT'; then
  echo "[FAIL] response does not contain PAYMENT_TIMEOUT" >&2
  exit 1
fi

if ! printf '%s\n' "$OUTPUT" | grep -q 'correlationId'; then
  echo "[FAIL] response does not contain correlationId" >&2
  exit 1
fi

echo "[PASS] S001 verified: HTTP 504 with PAYMENT_TIMEOUT and correlationId"
echo "[INFO] Logs command: docker compose logs -f api-gateway orders-service payments-service"
