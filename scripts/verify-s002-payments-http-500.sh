#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s002-payments-http-500.sh"
cd "$ROOT_DIR"

if [[ ! -x "${TRIGGER_SCRIPT}" ]]; then
  chmod +x "${TRIGGER_SCRIPT}"
fi

echo "[INFO] Starting S002 stack with deterministic payments HTTP 500 override"
docker compose -f docker-compose.yml -f docker-compose.s002.yml up -d --build

wait_for_health() {
  local name="$1" url="$2"
  for _ in {1..40}; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[OK] ${name} is healthy"
      return 0
    fi
    sleep 3
  done
  echo "[FAIL] ${name} did not become healthy at ${url}" >&2
  docker compose logs --tail=100 api-gateway orders-service payments-service >&2 || true
  exit 1
}

wait_for_health "api-gateway" "http://localhost:8080/actuator/health"
wait_for_health "orders-service" "http://localhost:8081/actuator/health"
wait_for_health "payments-service" "http://localhost:8082/actuator/health"

OUTPUT="$("${TRIGGER_SCRIPT}")"
printf '%s\n' "$OUTPUT"

STATUS="$(printf '%s\n' "$OUTPUT" | awk -F': ' '/^HTTP status:/ {print $2}' | tail -n1)"
if [[ "$STATUS" != "502" ]]; then
  echo "[FAIL] expected HTTP status 502, got '${STATUS:-missing}'" >&2
  exit 1
fi

if ! printf '%s\n' "$OUTPUT" | grep -q 'PAYMENT_5XX'; then
  echo "[FAIL] response does not contain PAYMENT_5XX" >&2
  exit 1
fi

if ! printf '%s\n' "$OUTPUT" | grep -q 'correlationId'; then
  echo "[FAIL] response does not contain correlationId" >&2
  exit 1
fi

echo "[PASS] S002 verified: HTTP 502 with PAYMENT_5XX and correlationId"
echo "[INFO] Logs command: docker compose logs -f api-gateway orders-service payments-service"
