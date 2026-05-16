#!/usr/bin/env bash
set -euo pipefail

correlation_id="s004-$(date +%s)-$RANDOM"

response_file="$(mktemp)"
http_status=$(curl -sS -o "$response_file" -w '%{http_code}' -X POST "http://localhost:8080/api/orders" \
  -H "Content-Type: application/json" \
  -H "X-Correlation-Id: ${correlation_id}" \
  -d '{"customerId":"cust-s004-001","amount":19.99,"currency":"USD"}')
response_body="$(cat "$response_file")"
rm -f "$response_file"

echo "info=deterministic_runtime_is_managed_by_verify_script"
echo "correlation_id=${correlation_id}"
echo "http_status=${http_status}"
echo "response_body=${response_body}"
