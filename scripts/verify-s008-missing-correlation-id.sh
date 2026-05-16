#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s008-missing-correlation-id.sh"

wait_for_http() {
  local service_name="$1"
  local url="$2"
  local attempts=60
  local sleep_seconds=2

  echo "[INFO] waiting for ${service_name} at ${url}"
  for ((i=1; i<=attempts; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[INFO] ${service_name} is ready"
      return 0
    fi
    sleep "$sleep_seconds"
  done

  echo "[FAIL] ${service_name} did not become ready at ${url}" >&2
  return 1
}

echo "[INFO] starting default Milestone 1 stack"
docker compose up -d --build --force-recreate

wait_for_http "api-gateway" "http://localhost:8080/actuator/health"
wait_for_http "orders-service" "http://localhost:8081/actuator/health"
wait_for_http "payments-service" "http://localhost:8082/actuator/health"

output="$(${TRIGGER_SCRIPT})"
printf '%s\n' "$output"

status="$(printf '%s\n' "$output" | awk -F': ' '/^HTTP status:/ {print $2}' | tail -n1)"
if [[ -z "$status" ]] || [[ ! "$status" =~ ^2[0-9][0-9]$ ]]; then
  echo "[FAIL] expected HTTP status 2xx, got '${status:-missing}'" >&2
  exit 1
fi

correlation_id="$(printf '%s\n' "$output" | awk -F': ' '/^extracted correlation ID:/ {print $2}' | tail -n1)"
if [[ -z "$correlation_id" ]]; then
  echo "[FAIL] unable to extract generated correlation ID from response header/body" >&2
  exit 1
fi

gateway_logs="$(docker compose logs api-gateway --since=5m 2>/dev/null | grep -F "$correlation_id" || true)"
orders_logs="$(docker compose logs orders-service --since=5m 2>/dev/null | grep -F "$correlation_id" || true)"
payments_logs="$(docker compose logs payments-service --since=5m 2>/dev/null | grep -F "$correlation_id" || true)"

if [[ -z "$gateway_logs" ]]; then
  echo "[FAIL] api-gateway logs do not contain generated correlation ID: $correlation_id" >&2
  exit 1
fi

if [[ -z "$orders_logs" ]]; then
  echo "[FAIL] orders-service logs do not contain propagated correlation ID: $correlation_id" >&2
  exit 1
fi

if [[ -z "$payments_logs" ]]; then
  echo "[FAIL] payments-service logs do not contain propagated correlation ID: $correlation_id" >&2
  exit 1
fi

echo "[PASS] S008 verified: gateway generated missing correlation ID and propagated it to downstream services"
echo "[INFO] correlation ID evidence: ${correlation_id}"
echo "[INFO] inspect logs with: docker compose logs -f api-gateway orders-service payments-service"
