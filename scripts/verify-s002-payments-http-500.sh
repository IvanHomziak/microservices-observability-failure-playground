#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s002-payments-http-500.sh"

if [[ ! -x "${TRIGGER_SCRIPT}" ]]; then
  chmod +x "${TRIGGER_SCRIPT}"
fi

if ! curl -fsS "http://localhost:8080/actuator/health" >/dev/null 2>&1; then
  echo "Stack not healthy on localhost:8080. Starting docker compose stack..."
  docker compose up -d --build
  sleep 10
fi

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
