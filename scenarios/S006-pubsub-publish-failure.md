# S006 — Pub/Sub publish failure

## Scenario ID
S006

## Status
Implemented

## Description
Simulates deterministic failure when `orders-service` attempts to publish `NotificationRequestedEvent` to `notification-service` in the local Pub/Sub-style flow.

## Behavior decision
**A. Notification is required**: order request fails with a controlled error response.

HTTP status selected: **503 Service Unavailable** (dependency path unavailable/degraded).

## Services involved
- `orders-service`
- `notification-service`
- Local HTTP/in-memory Pub/Sub-style adapter flow (no real GCP required)

## Config toggles
Primary toggles on `orders-service`:
- `orders.notifications.enabled=true`
- `orders.notifications.publish-failure-enabled=true`

Backward-compatible equivalent toggle:
- `orders.failures.publish-notification-failure=true`

Environment variable examples:
- `ORDERS_NOTIFICATIONS_ENABLED=true`
- `ORDERS_NOTIFICATIONS_PUBLISH_FAILURE_ENABLED=true`

## How to trigger
1. Start stack with notification publish failure enabled on `orders-service`.
2. Run:
   - `./scripts/trigger-s006-pubsub-publish-failure.sh`
3. Or run verification:
   - `./scripts/verify-s006-pubsub-publish-failure.sh`

## Expected response
`POST /api/orders` returns:
- HTTP `503`
- `code=NOTIFICATION_PUBLISH_FAILED`
- error `message`
- `correlationId`
- `timestamp`

## Expected logs
`orders-service` error log includes:
- `operation=notification_publish_failed`
- `event_id`
- `order_id`
- `correlation_id`
- `trace_id`
- `exception_type`
- `exception_message`

## Expected root cause
Notification publish simulation is enabled, so `orders-service` intentionally fails on notification publish and treats notification as required for successful order processing.

## Expected AI diagnostics agent conclusion
Incident is a deterministic, configuration-driven notification publish failure in `orders-service` (`orders.notifications.publish-failure-enabled=true`), causing controlled HTTP 503 responses with `NOTIFICATION_PUBLISH_FAILED`; no external GCP dependency is involved.

## Determinism / safety
- Deterministic when failure toggle is enabled.
- No real GCP required.
- Returns to normal by setting `orders.notifications.publish-failure-enabled=false`.
