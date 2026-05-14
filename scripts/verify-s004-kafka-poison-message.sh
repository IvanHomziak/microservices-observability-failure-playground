#!/usr/bin/env bash
set -euo pipefail

output=$(./scripts/trigger-s004-kafka-poison-message.sh)
correlation_id=$(printf '%s\n' "$output" | rg '^correlation_id=' | sed 's/correlation_id=//')

echo "$output"
sleep 8

docker compose logs inventory-service --since=3m | rg "operation=kafka_processing_failed" | rg "${correlation_id}" >/dev/null

docker compose logs inventory-service --since=3m | rg "operation=kafka_dlq_published" | rg "${correlation_id}" >/dev/null

# confirm DLQ topic has message with correlation id
(docker compose exec -T redpanda rpk topic consume order-created-dlq -n 20 -f '%h\\n%v\\n' | rg "${correlation_id}") >/dev/null

echo "S004 verified for correlation_id=${correlation_id}"
