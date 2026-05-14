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
- Local stack is running.
- Notifications are enabled and publish-failure simulation is enabled.

## 6. Configuration toggles
Primary properties:
- `orders.notifications.enabled=true`
- `orders.notifications.publish-failure-enabled=true`

Backward-compatible property:
- `orders.failures.publish-notification-failure=true`

## 7. How to run
```bash
./scripts/trigger-s006-pubsub-publish-failure.sh
```
Optional verification:
```bash
./scripts/verify-s006-pubsub-publish-failure.sh
```

## 8. Request/event payload
HTTP request to exact endpoint:
- `POST /api/orders` (`http://localhost:8080/api/orders`)

## 9. Expected HTTP response if applicable
- Status: `503 Service Unavailable`
- Body includes:
  - `code=NOTIFICATION_PUBLISH_FAILED`
  - `message`
  - `correlationId`
  - `timestamp`

## 10. Expected logs
`orders-service` error log includes:
- `operation=notification_publish_failed`
- `event_id`
- `order_id`
- `correlation_id`
- `trace_id`

## 11. Expected metrics
- No scenario-specific metric contract is guaranteed in this document.

## 12. Expected traces
- If tracing is enabled, publish path/error span should show failure in `orders-service` notification step.

## 13. Expected root cause
Configuration-driven publish failure simulation in `orders-service` notification publisher.

## 14. What the AI diagnostics agent should conclude
`NOTIFICATION_PUBLISH_FAILED` responses are deterministic and caused by enabled publish-failure simulation, not by external GCP Pub/Sub dependency.

## 15. Known limitations
- Local scenario does not require real GCP Pub/Sub.
- Trace evidence depends on runtime tracing setup.

## 16. Troubleshooting
- Verify `orders.notifications.enabled` and `orders.notifications.publish-failure-enabled` values in runtime config.
- Ensure no stale containers are running with old env values.
