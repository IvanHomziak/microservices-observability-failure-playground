#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s008-missing-correlation-id.sh"

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

generated_correlation_id="$(printf '%s\n' "$output" | awk -F': ' '/^generated correlation ID:/ {print $2}' | tail -n1)"
response_body="$(printf '%s\n' "$output" | awk 'f{print} /^response body:/{f=1}')"

if [[ -z "${generated_correlation_id}" ]] && ! printf '%s\n' "$response_body" | rg -q '"correlationId"\s*:\s*"[^"]+'; then
  echo "[FAIL] expected generated X-Correlation-Id header or body correlationId" >&2
  exit 1
fi

if [[ -z "${generated_correlation_id}" ]]; then
  generated_correlation_id="$(printf '%s\n' "$response_body" | sed -n 's/.*"correlationId"\s*:\s*"\([^"]\+\)".*/\1/p' | head -n1)"
fi

if [[ -z "${generated_correlation_id}" ]]; then
  echo "[FAIL] unable to extract generated correlation ID" >&2
  exit 1
fi

echo "log verification command: docker compose logs api-gateway orders-service payments-service --since=3m | rg '${generated_correlation_id}'"
echo "[PASS] S008 verified request path generated correlation ID and surfaced it in the response"
