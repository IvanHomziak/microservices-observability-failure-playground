#!/usr/bin/env bash
set -euo pipefail

SCENARIO_ID="S008"
URL="http://localhost:8080/api/orders"
PAYLOAD='{"customerId":"customer-123","amount":19.99,"currency":"USD"}'
TMP_HEADERS="$(mktemp)"
TMP_BODY="$(mktemp)"
trap 'rm -f "$TMP_HEADERS" "$TMP_BODY"' EXIT

HTTP_CODE=$(curl -sS -D "$TMP_HEADERS" -o "$TMP_BODY" -w "%{http_code}" \
  -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -d "$PAYLOAD")

GENERATED_CORRELATION_ID="$(awk 'BEGIN{IGNORECASE=1} /^X-Correlation-Id:/ {gsub("\r", "", $2); print $2}' "$TMP_HEADERS" | tail -n1)"

echo "scenario ID: ${SCENARIO_ID}"
echo "request payload: ${PAYLOAD}"
echo "HTTP status: ${HTTP_CODE}"
echo "response headers:"
cat "$TMP_HEADERS"
echo "response body:"
cat "$TMP_BODY"; echo

echo "generated correlation ID: ${GENERATED_CORRELATION_ID}"
echo "logs command: ./scripts/show-logs-by-correlation-id.sh ${GENERATED_CORRELATION_ID}"
