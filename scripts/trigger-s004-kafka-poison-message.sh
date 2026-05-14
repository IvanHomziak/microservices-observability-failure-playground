#!/usr/bin/env bash
set -euo pipefail

correlation_id="s004-poison-$(date +%s)"
event_id="evt-s004-$(date +%s)"

payload=$(cat <<JSON
{"eventId":"${event_id}","orderId":"ord-s004-poison","customerId":"cust-s004","amount":-10.00,"currency":"USD","correlationId":"${correlation_id}","traceId":"trace-s004","createdAt":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
JSON
)

printf '%s\n' "${payload}" | docker compose exec -T redpanda rpk topic produce order-created -H "correlation_id:${correlation_id}" >/dev/null

echo "correlation_id=${correlation_id}"
echo "event_id=${event_id}"
