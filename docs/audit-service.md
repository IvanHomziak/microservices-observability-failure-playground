# audit-service

`audit-service` is a lightweight observability validation service.

## Responsibilities
- receives audit lifecycle events over HTTP (`POST /audit/events`)
- optionally consumes `audit-events` from Kafka when `audit.kafka.enabled=true`
- emits structured logs for correlation checks
- exposes actuator health/metrics/prometheus endpoints

## AuditEvent contract
```json
{
  "eventId": "...",
  "eventType": "...",
  "orderId": "...",
  "sourceService": "...",
  "correlationId": "...",
  "traceId": "...",
  "createdAt": "..."
}
```

## Required log fields
Each received event emits:
- `operation=audit_event_received`
- `event_id`
- `event_type`
- `order_id`
- `source_service`
- `correlation_id`
- `trace_id`

## orders-service integration
`orders-service` publishes audit events when `orders.audit.enabled=true` for:
- `ORDER_CREATED`
- `PAYMENT_CONFIRMED`
- `PAYMENT_FAILED`

Configuration:
- local default: `orders.audit.enabled=false`
- docker profile default: `orders.audit.enabled=true`
- URL: `orders.audit.url` (default `http://audit-service:8085/audit/events` in docker)

## Verification
Run:
```bash
./scripts/verify-audit-flow.sh
```
The script triggers a successful order and verifies that `audit-service` logs contain the same `correlation_id`.
