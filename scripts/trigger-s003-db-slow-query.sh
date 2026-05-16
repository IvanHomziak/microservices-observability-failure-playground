#!/usr/bin/env bash
set -euo pipefail

URL="http://localhost:8080/api/orders"
CORRELATION_ID="s003-$(date +%s)-$RANDOM"
PAYLOAD='{"customerId":"customer-123","amount":19.99,"currency":"USD"}'

TMP_BODY="$(mktemp)"
trap 'rm -f "$TMP_BODY"' EXIT

echo "deterministic runtime setup is handled by ./scripts/verify-s003-db-slow-query.sh"
echo "sending request to: ${URL}"

START_MS=$(date +%s%3N)
HTTP_STATUS=$(curl -sS -o "$TMP_BODY" -w "%{http_code}" \
  -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -H "X-Correlation-Id: ${CORRELATION_ID}" \
  -d "$PAYLOAD")
END_MS=$(date +%s%3N)
ELAPSED_MS=$((END_MS - START_MS))

echo "correlation ID: ${CORRELATION_ID}"
echo "HTTP status: ${HTTP_STATUS}"
echo "elapsed time ms: ${ELAPSED_MS}"
echo "response body:"
cat "$TMP_BODY"
echo
