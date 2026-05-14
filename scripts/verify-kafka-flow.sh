#!/usr/bin/env bash
set -euo pipefail

./scripts/trigger-kafka-success-flow.sh >/tmp/kafka-flow-response.txt
correlation_id=$(rg "correlation_id=" /tmp/kafka-flow-response.txt | sed 's/correlation_id=//')

sleep 3

docker compose logs orders-service --since=2m | rg "operation=kafka_event_published" | rg "${correlation_id}" >/dev/null

docker compose logs inventory-service --since=2m | rg "operation=kafka_event_consumed" | rg "${correlation_id}" >/dev/null

echo "Kafka flow verified for correlation_id=${correlation_id}"
