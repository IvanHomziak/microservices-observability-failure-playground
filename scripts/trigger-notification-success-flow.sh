#!/usr/bin/env bash
set -euo pipefail

URL="http://localhost:8080/api/orders"
CORRELATION_ID="notif-success-$(date +%s)"
PAYLOAD='{"customerId":"customer-456","amount":29.99,"currency":"USD"}'

HTTP_CODE=$(curl -sS -o /tmp/notification-flow-response.json -w "%{http_code}" \
  -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -H "X-Correlation-Id: ${CORRELATION_ID}" \
  -d "$PAYLOAD")

echo "http_code=${HTTP_CODE}"
echo "correlation_id=${CORRELATION_ID}"
echo "response:"
cat /tmp/notification-flow-response.json; echo
