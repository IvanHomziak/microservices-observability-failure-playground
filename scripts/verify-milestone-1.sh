#!/usr/bin/env bash
set -euo pipefail

COMPOSE_CMD="docker compose"
HEALTH_TIMEOUT_SECONDS="${HEALTH_TIMEOUT_SECONDS:-180}"
HEALTH_POLL_SECONDS="${HEALTH_POLL_SECONDS:-3}"

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

wait_for_health() {
  local name="$1"
  local url="$2"
  local start now code body

  echo "[INFO] Waiting for ${name} health: ${url}"
  start="$(date +%s)"

  while true; do
    code="$(curl -sS -o /tmp/verify-health-body.$$ -w '%{http_code}' "$url" || true)"
    body="$(cat /tmp/verify-health-body.$$ 2>/dev/null || true)"

    if [[ "$code" == "200" ]] && echo "$body" | grep -q '"status"\s*:\s*"UP"'; then
      echo "[OK] ${name} is healthy"
      rm -f /tmp/verify-health-body.$$
      return 0
    fi

    now="$(date +%s)"
    if (( now - start >= HEALTH_TIMEOUT_SECONDS )); then
      rm -f /tmp/verify-health-body.$$
      fail "Timed out waiting for ${name} health at ${url}. Last HTTP=${code}, body=${body}"
    fi

    sleep "$HEALTH_POLL_SECONDS"
  done
}

extract_http_code() {
  awk '/response \(HTTP [0-9]{3}\):/ {gsub(/[^0-9]/, "", $0); print $0; exit}'
}

extract_response_body() {
  awk '
    /response \(HTTP [0-9]{3}\):/ {in_body=1; next}
    in_body && /^correlation ID:/ {exit}
    in_body {print}
  '
}

extract_correlation_id() {
  awk -F': ' '/^correlation ID:/ {print $2; exit}'
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local message="$3"
  if ! grep -q "$needle" <<<"$haystack"; then
    fail "$message. Missing: ${needle}. Body: ${haystack}"
  fi
}

run_and_verify_success() {
  local output http body corr

  echo "[INFO] Triggering SUCCESS scenario"
  output="$(./scripts/trigger-successful-order.sh 2>&1)" || fail "trigger-successful-order.sh failed to execute"
  echo "$output"

  http="$(echo "$output" | extract_http_code)"
  body="$(echo "$output" | extract_response_body)"
  corr="$(echo "$output" | extract_correlation_id)"

  [[ -n "$http" ]] || fail "Could not parse HTTP status for SUCCESS scenario"
  [[ "$http" =~ ^2[0-9][0-9]$ ]] || fail "SUCCESS scenario expected 2xx but got ${http}"

  assert_contains "$body" '"orderId"' "SUCCESS scenario response missing orderId"
  assert_contains "$body" '"status"' "SUCCESS scenario response missing status"
  assert_contains "$body" '"correlationId"' "SUCCESS scenario response missing correlationId"

  echo "[VERIFY] scenario ID: SUCCESS"
  echo "[VERIFY] correlation ID: ${corr:-not found}"
  echo "[VERIFY] response body: ${body}"
  echo "[VERIFY] logs command: docker compose logs -f api-gateway orders-service payments-service"
}

run_and_verify_s001() {
  local output http body corr

  echo "[INFO] Triggering S001 scenario"
  output="$(./scripts/trigger-s001-resttemplate-timeout.sh 2>&1)" || fail "trigger-s001-resttemplate-timeout.sh failed to execute"
  echo "$output"

  http="$(echo "$output" | extract_http_code)"
  body="$(echo "$output" | extract_response_body)"
  corr="$(echo "$output" | extract_correlation_id)"

  [[ -n "$http" ]] || fail "Could not parse HTTP status for S001 scenario"
  [[ "$http" == "504" ]] || fail "S001 scenario expected 504 but got ${http}"

  assert_contains "$body" 'PAYMENT_TIMEOUT' "S001 response missing PAYMENT_TIMEOUT"
  assert_contains "$body" '"correlationId"' "S001 response missing correlationId"

  echo "[VERIFY] scenario ID: S001"
  echo "[VERIFY] correlation ID: ${corr:-not found}"
  echo "[VERIFY] response body: ${body}"
  echo "[VERIFY] logs command: docker compose logs -f api-gateway orders-service payments-service"
}

echo "[INFO] Starting Milestone 1 stack"
$COMPOSE_CMD up -d --build

wait_for_health "api-gateway" "http://localhost:8080/actuator/health"
wait_for_health "orders-service" "http://localhost:8081/actuator/health"
wait_for_health "payments-service" "http://localhost:8082/actuator/health"

run_and_verify_success
run_and_verify_s001

echo "[PASS] Milestone 1 verification completed successfully"
