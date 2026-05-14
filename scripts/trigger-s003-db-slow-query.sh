#!/usr/bin/env bash
set -euo pipefail

SCENARIO_ID="S003"
URL="http://localhost:8080/api/orders"
CORRELATION_ID="s003-$(date +%s)"
PAYLOAD='{"customerId":"customer-123","amount":19.99,"currency":"USD"}'
TMP_HEADERS="$(mktemp)"
TMP_BODY="$(mktemp)"
trap 'rm -f "$TMP_HEADERS" "$TMP_BODY"' EXIT

HTTP_CODE=$(curl -sS -D "$TMP_HEADERS" -o "$TMP_BODY" -w "%{http_code}" \
  -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -H "X-Correlation-Id: ${CORRELATION_ID}" \
  -d "$PAYLOAD")

LATENCY_MS=$(awk 'BEGIN{IGNORECASE=1} /^x-response-time-ms:/ {print $2}' "$TMP_HEADERS" | tr -d '\r' | tail -n1)

echo "scenario ID: ${SCENARIO_ID}"
echo "request payload: ${PAYLOAD}"
echo "HTTP status: ${HTTP_CODE}"
echo "response body:"
cat "$TMP_BODY"; echo

echo "correlation ID: ${CORRELATION_ID}"
echo "response latency hint ms: ${LATENCY_MS:-not available}"
echo "logs command: ./scripts/show-logs-by-correlation-id.sh ${CORRELATION_ID}"
