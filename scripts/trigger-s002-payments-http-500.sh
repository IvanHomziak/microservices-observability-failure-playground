#!/usr/bin/env bash
set -euo pipefail

SCENARIO_ID="S002"
URL="http://localhost:8080/api/orders"
CORRELATION_ID="s002-$(date +%s)"
PAYLOAD='{"customerId":"customer-123","amount":19.99,"currency":"USD"}'
TMP_HEADERS="$(mktemp)"
TMP_BODY="$(mktemp)"
trap 'rm -f "$TMP_HEADERS" "$TMP_BODY"' EXIT

HTTP_CODE=$(curl -sS -D "$TMP_HEADERS" -o "$TMP_BODY" -w "%{http_code}" \
  -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -H "X-Correlation-Id: ${CORRELATION_ID}" \
  -d "$PAYLOAD")

echo "scenario ID: ${SCENARIO_ID}"
echo "request payload: ${PAYLOAD}"
echo "HTTP status: ${HTTP_CODE}"
echo "response body:"
cat "$TMP_BODY"; echo

echo "correlation ID: ${CORRELATION_ID}"
echo "logs command: ./scripts/show-logs-by-correlation-id.sh ${CORRELATION_ID}"
