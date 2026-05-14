#!/usr/bin/env bash
set -euo pipefail

correlation_id="kafka-success-$(date +%s)"

curl -sS -X POST "http://localhost:8080/api/orders" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: ${correlation_id}" \
  -d '{"customerId":"cust-kafka-001","amount":19.99,"currency":"USD"}' | jq '.'

echo "correlation_id=${correlation_id}"
