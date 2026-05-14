#!/usr/bin/env bash
set -euo pipefail

SCENARIO_ID="S001"
URL="http://localhost:8080/api/orders"
CORRELATION_ID="s001-$(date +%s)"
PAYLOAD='{"customerId":"customer-123","amount":19.99,"currency":"USD"}'
TMP_HEADERS="$(mktemp)"
TMP_BODY="$(mktemp)"
trap 'rm -f "$TMP_HEADERS" "$TMP_BODY"' EXIT

echo "[NOTE] This script only triggers S001 by sending a normal order request."
echo "[NOTE] S001 requires payments-service delay to be greater than orders-service read timeout."
echo "[NOTE] Use ./scripts/verify-s001-resttemplate-timeout.sh for deterministic S001 setup."

HTTP_CODE=$(curl -sS -D "$TMP_HEADERS" -o "$TMP_BODY" -w "%{http_code}" \
  -X POST "$URL" \
  -H 'Content-Type: application/json' \
  -H "X-Correlation-Id: ${CORRELATION_ID}" \
  -d "$PAYLOAD")

TRACE_ID=$(awk 'BEGIN{IGNORECASE=1} /^traceparent:/ {print $2}' "$TMP_HEADERS" | tr -d '\r' | awk -F- '{print $2}' | tail -n1)
RESP_CORRELATION_ID=$(awk 'BEGIN{IGNORECASE=1} /^x-correlation-id:/ {print $2}' "$TMP_HEADERS" | tr -d '\r' | tail -n1)
if [[ -z "${RESP_CORRELATION_ID}" ]]; then RESP_CORRELATION_ID="$CORRELATION_ID"; fi

echo "scenario ID: ${SCENARIO_ID}"
echo "request payload: ${PAYLOAD}"
echo "response (HTTP ${HTTP_CODE}):"
cat "$TMP_BODY"; echo

echo "correlation ID: ${RESP_CORRELATION_ID:-not found}"
echo "trace ID: ${TRACE_ID:-not found}"
echo "where to look in Grafana/Loki/Tempo:"
echo "- Grafana: http://localhost:3000 (Explore)"
echo "- Loki query: {service_name=~\"api-gateway|orders-service|payments-service\"} |= \"${RESP_CORRELATION_ID}\" |= \"PAYMENT_TIMEOUT\""
echo "- Tempo: find the failing client span from orders-service to payments-service using trace ID '${TRACE_ID:-<copy-from-logs>}'"
