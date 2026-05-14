#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s007-broken-trace-propagation.sh"

if [[ ! -x "${TRIGGER_SCRIPT}" ]]; then
  chmod +x "${TRIGGER_SCRIPT}"
fi

if ! curl -fsS "http://localhost:8080/actuator/health" >/dev/null 2>&1; then
  echo "[FAIL] stack is not healthy at localhost:8080" >&2
  exit 1
fi

output="$(${TRIGGER_SCRIPT})"
printf '%s\n' "$output"

status="$(printf '%s\n' "$output" | awk -F': ' '/^HTTP status:/ {print $2}' | tail -n1)"
if [[ "$status" != "201" ]]; then
  echo "[FAIL] expected HTTP status 201, got '${status:-missing}'" >&2
  exit 1
fi

if ! printf '%s\n' "$output" | rg -q 'correlationId'; then
  echo "[FAIL] expected correlationId in response" >&2
  exit 1
fi

correlation_id="$(printf '%s\n' "$output" | awk -F': ' '/^correlation ID:/ {print $2}' | tail -n1)"
if [[ -z "${correlation_id}" ]]; then
  echo "[FAIL] unable to extract correlation ID" >&2
  exit 1
fi

logs="$(docker compose logs orders-service payments-service --since=3m 2>/dev/null | rg "${correlation_id}" || true)"

if ! printf '%s\n' "$logs" | rg -q 'operation=trace_propagation_intentionally_broken target_service=payments-service'; then
  echo "[FAIL] orders-service log missing intentional trace break marker" >&2
  exit 1
fi

if ! printf '%s\n' "$logs" | rg -q 'operation=payment_authorize_received.*traceparent=missing'; then
  echo "[FAIL] payments-service log missing traceparent=missing evidence" >&2
  exit 1
fi

echo "[PASS] S007 verified: business request succeeds, correlationId propagates, and trace propagation is intentionally broken"
