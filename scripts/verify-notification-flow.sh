#!/usr/bin/env bash
set -euo pipefail

./scripts/trigger-notification-success-flow.sh >/tmp/notification-flow-trigger.txt
correlation_id=$(rg "correlation_id=" /tmp/notification-flow-trigger.txt | sed 's/correlation_id=//')

sleep 3

docker compose logs orders-service --since=2m | rg "operation=notification_publish_succeeded" | rg "${correlation_id}" >/dev/null
docker compose logs notification-service --since=2m | rg "operation=notification_event_received" | rg "${correlation_id}" >/dev/null
docker compose logs notification-service --since=2m | rg "operation=notification_sent" | rg "${correlation_id}" >/dev/null

echo "Notification flow verified for correlation_id=${correlation_id}"
