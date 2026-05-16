#!/usr/bin/env bash
set -euo pipefail

count="${1:-20}"
correlation_prefix="s005-$(date +%s)"

success_count=0
failure_count=0
correlation_ids=""

for i in $(seq 1 "$count"); do
  correlation_id="${correlation_prefix}-${i}"
  payload="{\"customerId\":\"cust-s005-${i}\",\"amount\":19.99,\"currency\":\"USD\"}"

  http_code=$(curl -sS -o /tmp/s005-order-${i}.json -w "%{http_code}" \
    -X POST "http://localhost:8080/api/orders" \
    -H "Content-Type: application/json" \
    -H "X-Correlation-Id: ${correlation_id}" \
    -d "${payload}" || true)

  if [[ "${http_code}" == "201" || "${http_code}" == "200" ]]; then
    success_count=$((success_count + 1))
  else
    failure_count=$((failure_count + 1))
  fi

  echo "request_index=${i} correlation_id=${correlation_id} http_status=${http_code}"
  correlation_ids+="${correlation_id} "
done

echo "count=${count}"
echo "success_count=${success_count}"
echo "failure_count=${failure_count}"
echo "correlation_prefix=${correlation_prefix}"
echo "correlation_ids=${correlation_ids}"
