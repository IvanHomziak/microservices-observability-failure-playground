#!/usr/bin/env bash
set -euo pipefail

correlation_id="s006-$(date +%s)"
payload='{"customerId":"cust-s006","amount":49.99,"currency":"USD"}'

response_file="$(mktemp)"
http_status="$(curl -sS -o "${response_file}" -w '%{http_code}' \
  -X POST 'http://localhost:8080/api/orders' \
  -H 'Content-Type: application/json' \
  -H "X-Correlation-Id: ${correlation_id}" \
  -d "${payload}")"

printf 'Correlation ID: %s\n' "${correlation_id}"
printf 'HTTP status: %s\n' "${http_status}"
printf 'Response body: %s\n' "$(cat "${response_file}")"
rm -f "${response_file}"
