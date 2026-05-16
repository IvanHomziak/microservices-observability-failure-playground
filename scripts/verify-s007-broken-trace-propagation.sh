#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s007-broken-trace-propagation.sh"

cleanup() {
  local exit_code=$?
  set +e
  docker compose -f docker-compose.yml up -d orders-service >/dev/null 2>&1
  set -e
  return "$exit_code"
}
trap cleanup EXIT

[[ -x "${TRIGGER_SCRIPT}" ]] || chmod +x "${TRIGGER_SCRIPT}"

echo "[1/5] Starting S007 stack with tracing break override"
docker compose -f docker-compose.yml -f docker-compose.s007.yml up -d --build --force-recreate

echo "[2/5] Waiting for services"
for service in api-gateway orders-service payments-service; do
  echo "  - waiting for ${service}"
  docker compose wait "${service}" >/dev/null
  for _ in {1..40}; do
    if docker compose exec -T "${service}" sh -lc 'wget -q -O - http://localhost:8080/actuator/health >/dev/null 2>&1 || wget -q -O - http://localhost:8081/actuator/health >/dev/null 2>&1 || wget -q -O - http://localhost:8082/actuator/health >/dev/null 2>&1'; then
      break
    fi
    sleep 2
  done

done

echo "[3/5] Triggering business request"
output="$(${TRIGGER_SCRIPT})"
printf '%s\n' "$output"

status="$(printf '%s\n' "$output" | awk -F': ' '/^HTTP status:/ {print $2}' | tail -n1)"
if [[ ! "$status" =~ ^2[0-9][0-9]$ ]]; then
  echo "[FAIL] expected 2xx business response, got '${status:-missing}'" >&2
  exit 1
fi

if ! printf '%s\n' "$output" | grep -Eq '"correlationId"[[:space:]]*:'; then
  echo "[FAIL] expected response body to contain correlationId" >&2
  exit 1
fi

correlation_id="$(printf '%s\n' "$output" | awk -F': ' '/^correlation ID:/ {print $2}' | tail -n1)"
[[ -n "${correlation_id}" ]] || { echo "[FAIL] unable to extract correlation ID" >&2; exit 1; }

echo "[4/5] Verifying propagation evidence from logs"
orders_logs="$(docker compose logs orders-service --since=3m 2>/dev/null | grep -E "${correlation_id}" || true)"
payments_logs="$(docker compose logs payments-service --since=3m 2>/dev/null || true)"

if ! printf '%s\n' "$orders_logs" | grep -Eq "${correlation_id}"; then
  echo "[FAIL] orders-service logs do not contain request correlation ID ${correlation_id}" >&2
  exit 1
fi

if ! docker compose logs orders-service --since=3m 2>/dev/null | grep -Eq 'operation=trace_propagation_intentionally_broken target_service=payments-service'; then
  echo "[FAIL] orders-service missing explicit intentional trace break marker" >&2
  exit 1
fi

if printf '%s\n' "$payments_logs" | grep -Eq "operation=payment_authorize_received.*correlation_id=${correlation_id}.*traceparent=missing"; then
  echo "[PASS] evidence: payments-service received request with same correlation_id but traceparent=missing"
elif printf '%s\n' "$payments_logs" | grep -Eq 'operation=payment_authorize_received.*traceparent=missing'; then
  echo "[PASS] evidence: payments-service shows traceparent=missing"
elif ! printf '%s\n' "$payments_logs" | grep -Eq "${correlation_id}"; then
  echo "[PASS] evidence: payments-service does not contain same correlation ID (propagation broken)"
else
  echo "[FAIL] unable to prove broken propagation from payments-service logs" >&2
  exit 1
fi

echo "[PASS] S007 verified: business flow succeeds but downstream observability propagation is broken"
echo "logs command: docker compose logs -f api-gateway orders-service payments-service"
