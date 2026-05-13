# notification-service

This service simulates **Google Pub/Sub-like** notification processing without requiring cloud credentials.

## Transport mode used

- Default and currently implemented mode: **local in-memory fake Pub/Sub adapter** (`InMemoryPubSubAdapter`).
- Real Google Pub/Sub credentials are **not required**.
- A real emulator-backed adapter can be added later behind the same `PubSubPort` interface without changing API handlers.

## Supported event

`NotificationRequestedEvent`

```json
{
  "eventId": "evt-1",
  "orderId": "order-100",
  "userId": "user-42",
  "channel": "EMAIL",
  "destination": "user@example.com",
  "message": "Your order was confirmed"
}
```

## Failure simulation modes

Set mode with:

```bash
curl -X PUT http://localhost:8084/api/notifications/failure-mode/ACK_TIMEOUT
```

Modes:

- `NONE`
- `INVALID_TOPIC`
- `PUBLISH_FAILURE`
- `ACK_TIMEOUT`
- `DUPLICATE_DELIVERY`
- `PROCESSING_DELAY`
- `MALFORMED_PAYLOAD`

## Trigger a notification event

```bash
curl -X POST http://localhost:8084/api/notifications/events \
  -H 'Content-Type: application/json' \
  -d '{
    "eventId":"evt-1",
    "orderId":"order-100",
    "userId":"user-42",
    "channel":"EMAIL",
    "destination":"user@example.com",
    "message":"Your order was confirmed"
  }'
```
