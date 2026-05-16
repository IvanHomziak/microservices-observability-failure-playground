#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s006-pubsub-publish-failure.sh"

cleanup() {
  docker compose -f "${ROOT_DIR}/docker-compose.yml" -f "${ROOT_DIR}/docker-compose.s006.yml" --profile async down -v --remove-orphans || true
}
trap cleanup EXIT

echo "[INFO] Starting S006 deterministic runtime"
docker compose -f "${ROOT_DIR}/docker-compose.yml" -f "${ROOT_DIR}/docker-compose.s006.yml" --profile async up -d --build --force-recreate

wait_for_health() {
  local name="$1"
  local url="$2"
  local retries=60

  for _ in $(seq 1 "$retries"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[INFO] ${name} is healthy"
      return 0
    fi
    sleep 2
  done

  echo "[FAIL] ${name} did not become healthy: ${url}" >&2
  return 1
}

wait_for_health "api-gateway" "http://localhost:8080/actuator/health"
wait_for_health "orders-service" "http://localhost:8081/actuator/health"
wait_for_health "payments-service" "http://localhost:8082/actuator/health"
wait_for_health "notification-service" "http://localhost:8084/actuator/health"

output="$(${TRIGGER_SCRIPT})"
printf '%s\n' "$output"

status="$(printf '%s\n' "$output" | awk -F': ' '/^HTTP status:/ {print $2}' | tail -n1)"

if [[ "$status" != "503" ]]; then
  echo "[FAIL] expected HTTP status 503, got '${status:-missing}'" >&2
  exit 1
fi

if ! printf '%s\n' "$output" | rg -q 'NOTIFICATION_PUBLISH_FAILED'; then
  echo "[FAIL] expected NOTIFICATION_PUBLISH_FAILED in response" >&2
  exit 1
fi

if ! printf '%s\n' "$output" | rg -q 'correlationId'; then
  echo "[FAIL] expected correlationId in response" >&2
  exit 1
fi

correlation_id="$(printf '%s\n' "$output" | awk -F': ' '/^Correlation ID:/ {print $2}' | tail -n1)"
if [[ -z "$correlation_id" ]]; then
  echo "[FAIL] missing correlation ID in trigger output" >&2
  exit 1
fi

if ! docker compose -f "${ROOT_DIR}/docker-compose.yml" -f "${ROOT_DIR}/docker-compose.s006.yml" logs --since=2m orders-service \
  | rg -q "operation=notification_publish_failed.*${correlation_id}"; then
  echo "[FAIL] expected orders-service notification_publish_failed log for correlation ${correlation_id}" >&2
  exit 1
fi

echo "[PASS] S006 verified: deterministic notification publish failure returns HTTP 503 with NOTIFICATION_PUBLISH_FAILED"
echo "[INFO] Logs command: docker compose logs -f orders-service notification-service"
