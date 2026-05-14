#!/usr/bin/env bash
set -euo pipefail

count="${1:-25}"
delay_ms="${S005_DELAY_MS:-1200}"

echo "Set inventory delay config before running (if not already):"
echo "  INVENTORY_FAILURE_SIMULATION_CONSUMER_LAG_MODE_ENABLED=true"
echo "  INVENTORY_FAILURE_SIMULATION_PROCESSING_DELAY_MS=${delay_ms}"

output=$(./scripts/trigger-s005-kafka-consumer-lag.sh "${count}")
correlation_prefix=$(printf '%s\n' "$output" | rg '^correlation_prefix=' | sed 's/correlation_prefix=//')

echo "$output"
sleep 8

docker compose logs inventory-service --since=10m | rg "operation=kafka_processing_delay_simulated" | rg "${correlation_prefix}" >/dev/null

if docker compose exec -T redpanda rpk group describe inventory-service >/tmp/s005-group.txt 2>/dev/null; then
  lag_line=$(rg 'order-created' /tmp/s005-group.txt | head -n 1 || true)
  if [[ -n "${lag_line}" ]]; then
    echo "consumer_group_lag_snapshot=${lag_line}"
  fi
fi

echo "S005 verified for correlation_prefix=${correlation_prefix}"
