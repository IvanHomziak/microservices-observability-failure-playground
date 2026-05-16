#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s003-db-slow-query.sh"
COMPOSE_FILES=(-f "${ROOT_DIR}/docker-compose.yml" -f "${ROOT_DIR}/docker-compose.s003.yml")
FAILED=0

cleanup() {
  echo "Restoring default orders-service runtime..."
  if ! docker compose -f "${ROOT_DIR}/docker-compose.yml" up -d --build --force-recreate orders-service; then
    echo "[WARN] failed to restore default orders-service runtime" >&2
  fi

  if (( FAILED != 0 )); then
    exit "$FAILED"
  fi
}
trap cleanup EXIT

wait_for_health() {
  local url="$1"
  local name="$2"
  local retries=60
  local sleep_seconds=2

  echo "Waiting for ${name} health: ${url}"
  for _ in $(seq 1 "$retries"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "${name} is healthy"
      return 0
    fi
    sleep "$sleep_seconds"
  done

  echo "[FAIL] ${name} did not become healthy in time" >&2
  return 1
}

echo "Starting stack with S003 deterministic override..."
docker compose "${COMPOSE_FILES[@]}" up -d --build --force-recreate

wait_for_health "http://localhost:8080/actuator/health" "api-gateway"
wait_for_health "http://localhost:8081/actuator/health" "orders-service"
wait_for_health "http://localhost:8082/actuator/health" "payments-service"

TRIGGER_OUTPUT="$(${TRIGGER_SCRIPT})"
printf '%s\n' "$TRIGGER_OUTPUT"

HTTP_STATUS="$(printf '%s\n' "$TRIGGER_OUTPUT" | awk -F': ' '/^HTTP status:/ {print $2}' | tail -n1)"
ELAPSED_MS="$(printf '%s\n' "$TRIGGER_OUTPUT" | awk -F': ' '/^elapsed time ms:/ {print $2}' | tail -n1)"
CORRELATION_ID="$(printf '%s\n' "$TRIGGER_OUTPUT" | awk -F': ' '/^correlation ID:/ {print $2}' | tail -n1)"
RESPONSE_BODY="$(printf '%s\n' "$TRIGGER_OUTPUT" | awk 'f{print} /^response body:/{f=1;next}')"

if [[ -z "$HTTP_STATUS" || ! "$HTTP_STATUS" =~ ^2[0-9][0-9]$ ]]; then
  echo "[FAIL] expected HTTP status to be 2xx, got '${HTTP_STATUS:-missing}'" >&2
  FAILED=1
fi

if [[ "$RESPONSE_BODY" != *"correlationId"* ]]; then
  echo "[FAIL] expected response body to include correlationId" >&2
  FAILED=1
fi

if [[ -z "$ELAPSED_MS" || ! "$ELAPSED_MS" =~ ^[0-9]+$ ]]; then
  echo "[FAIL] elapsed time is missing or invalid" >&2
  FAILED=1
elif (( ELAPSED_MS < 2500 )); then
  echo "[FAIL] expected elapsed time >= 2500ms, got ${ELAPSED_MS}ms" >&2
  FAILED=1
fi

if [[ -z "$CORRELATION_ID" ]]; then
  echo "[FAIL] missing correlation ID in trigger output" >&2
  FAILED=1
else
  LOGS="$(docker compose "${COMPOSE_FILES[@]}" logs orders-service --since=10m 2>&1 || true)"

  if [[ "$LOGS" != *"${CORRELATION_ID}"* ]]; then
    echo "[FAIL] orders-service logs do not contain correlation ID ${CORRELATION_ID}" >&2
    FAILED=1
  fi

  if [[ "$LOGS" != *"operation=db_query_slow_simulated"* ]]; then
    echo "[FAIL] orders-service logs do not contain slow-query simulation evidence" >&2
    FAILED=1
  fi
fi

echo "Debug command: docker compose logs -f api-gateway orders-service payments-service"

if (( FAILED != 0 )); then
  echo "[FAIL] S003 verification failed" >&2
  exit "$FAILED"
fi

echo "[PASS] S003 verification passed"
