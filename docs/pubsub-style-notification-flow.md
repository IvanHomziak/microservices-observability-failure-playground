# Pub/Sub-style Notification Flow (Local-first)

## Overview
This project includes a local Pub/Sub-style notification flow that does not require GCP credentials.

- `orders-service` publishes `NotificationRequestedEvent` via HTTP in local/default mode.
- `notification-service` receives the event at `POST /api/notifications/events` and passes it to a `PubSubPort` abstraction.
- `InMemoryPubSubAdapter` simulates Pub/Sub topic publish/subscribe and ack behavior.
- Extension point: replace `InMemoryPubSubAdapter` with a future Google Pub/Sub emulator/real adapter implementing `PubSubPort`.

## Event contract
```json
{
  "eventId": "...",
  "orderId": "...",
  "customerId": "...",
  "channel": "EMAIL",
  "correlationId": "...",
  "traceId": "...",
  "createdAt": "..."
}
```

## Key logs
Orders service:
- `operation=notification_publish_requested`
- `operation=notification_publish_succeeded`
- `operation=notification_publish_failed`

Notification service:
- `operation=notification_event_received`
- `operation=notification_sent`
- `operation=notification_failed`

## Local run and verify
- Trigger flow: `./scripts/trigger-notification-success-flow.sh`
- Verify end-to-end: `./scripts/verify-notification-flow.sh`
