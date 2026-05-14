#!/usr/bin/env bash
set -euo pipefail

count="${1:-30}"
correlation_prefix="s005-lag-$(date +%s)"
created_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

for i in $(seq 1 "$count"); do
  event_id="evt-${correlation_prefix}-${i}"
  order_id="ord-${correlation_prefix}-${i}"
  correlation_id="${correlation_prefix}-${i}"
  payload=$(cat <<JSON
{"eventId":"${event_id}","orderId":"${order_id}","customerId":"cust-s005","amount":19.99,"currency":"USD","correlationId":"${correlation_id}","traceId":"trace-s005-${i}","createdAt":"${created_at}"}
JSON
)
  printf '%s\n' "${payload}" | docker compose exec -T redpanda rpk topic produce order-created -H "correlation_id:${correlation_id}" >/dev/null
 done

echo "count=${count}"
echo "correlation_prefix=${correlation_prefix}"
echo "redpanda_console_url=http://localhost:8081/topics/order-created/consumer-groups/inventory-service"
echo "logs_command=docker compose logs inventory-service --since=10m | rg 'operation=kafka_processing_delay_simulated|${correlation_prefix}'"
