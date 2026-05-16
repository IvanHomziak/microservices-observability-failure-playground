# S006 — Pub/Sub publish failure

## 1. Scenario ID
S006

## 2. Status
Implemented

## 3. Purpose
Validate deterministic notification publish failure behavior in `orders-service` for local Pub/Sub-style flow.

## 4. Services involved
- `orders-service`
- `notification-service`

## 5. Preconditions
- Local stack is running with S006 override.
- Notification path is enabled in `orders-service`.
- Deterministic publish failure simulation is enabled in `orders-service`.

## 6. Configuration toggles
Compose override (`docker-compose.s006.yml`) sets:
- `ORDERS_EVENTS_NOTIFICATION_ENABLED=true`
- `ORDERS_NOTIFICATIONS_ENABLED=true`
- `ORDERS_NOTIFICATIONS_PUBLISH_FAILURE_ENABLED=true`

Equivalent property behavior in `orders-service`:
- `orders.notifications.enabled=true`
- `orders.notifications.publish-failure-enabled=true`
- (`orders.failures.publish-notification-failure=true` is also supported by fallback wiring)

## 7. How to run
```bash
./scripts/trigger-s006-pubsub-publish-failure.sh
```
Deterministic verifier:
```bash
./scripts/verify-s006-pubsub-publish-failure.sh
```

## 8. Request/event payload
HTTP request:
- `POST /api/orders` via `api-gateway` (`http://localhost:8080/api/orders`)

## 9. Expected HTTP contract
From current production code in `orders-service`:
- When `NotificationPublisher` throws `NotificationPublishException`, global exception mapping returns `503 Service Unavailable`.
- Response body includes:
  - `code=NOTIFICATION_PUBLISH_FAILED`
  - `message`
  - `correlationId`
  - `timestamp`

## 10. Expected logs
`orders-service` logs include failure evidence:
- `operation=notification_publish_failed`
- `event_id`
- `order_id`
- `correlation_id`
- `trace_id`

## 11. Expected metrics
- No scenario-specific metric contract is guaranteed in this document.

## 12. Expected traces
- If tracing is enabled, the notification publish path/error span shows failure in `orders-service` notification step.

## 13. Expected root cause
Configuration-driven deterministic publish failure simulation in `orders-service` notification publisher.

## 14. What the AI diagnostics agent should conclude
Root cause is deterministic notification/PubSub publish failure in orders-service notification path.

## 15. Known limitations
- Local scenario does not require real GCP Pub/Sub.
- Trace evidence depends on runtime tracing setup.

## 16. Troubleshooting
- Verify S006 override env values are active in running `orders-service` container.
- Ensure no stale containers are running with old env values.
