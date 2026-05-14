#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s006-pubsub-publish-failure.sh"

if ! curl -fsS "http://localhost:8080/actuator/health" >/dev/null 2>&1; then
  echo "[FAIL] orders-service is not reachable at localhost:8080" >&2
  exit 1
fi

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

if ! printf '%s\n' "$output" | rg -q 'timestamp'; then
  echo "[FAIL] expected timestamp in response" >&2
  exit 1
fi

echo "[PASS] S006 verified: deterministic notification publish failure returns HTTP 503"
