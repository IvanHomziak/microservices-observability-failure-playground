#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIGGER_SCRIPT="${ROOT_DIR}/scripts/trigger-s003-db-slow-query.sh"

chmod +x "${TRIGGER_SCRIPT}"

export ORDERS_FAILURES_DATABASE_SLOW_QUERY_ENABLED=true
export ORDERS_FAILURES_DATABASE_SLOW_QUERY_DELAY_MS=750

echo "Applying S003 config and ensuring services are running..."
docker compose up -d --build orders-service api-gateway >/dev/null

START_MS=$(date +%s%3N)
OUTPUT="$(${TRIGGER_SCRIPT})"
END_MS=$(date +%s%3N)
ELAPSED_MS=$((END_MS - START_MS))

printf '%s\n' "$OUTPUT"
echo "measured latency ms: ${ELAPSED_MS}"

STATUS="$(printf '%s\n' "$OUTPUT" | awk -F': ' '/^HTTP status:/ {print $2}' | tail -n1)"
if [[ "$STATUS" != "200" ]]; then
  echo "[FAIL] expected HTTP status 200, got '${STATUS:-missing}'" >&2
  exit 1
fi

if (( ELAPSED_MS < 700 )); then
  echo "[FAIL] expected latency >= 700ms, got ${ELAPSED_MS}ms" >&2
  exit 1
fi

echo "[PASS] S003 verified: deterministic DB latency observed"
echo "logs command: docker compose logs orders-service --since=5m | grep 'operation=db_query_'"
