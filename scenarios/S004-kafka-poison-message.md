# S004 — Kafka poison message

## 1. Scenario ID
S004

## 2. Status
Implemented

## 3. Purpose
Validate deterministic poison-message handling with retries and dead-letter routing for Kafka consumers.

## 4. Services involved
- `redpanda` (Kafka broker)
- `inventory-service`

## 5. Preconditions
- Local stack is running with Kafka path enabled.
- `inventory-service` is consuming from topic `order-created`.

## 6. Configuration toggles
No special failure toggle is required for the invalid payload path.
Relevant properties:
- `app.kafka.retry.max-attempts`
- `app.kafka.retry.interval-ms`
- `app.kafka.topics.order-created-dlq`

## 7. How to run
```bash
./scripts/trigger-s004-kafka-poison-message.sh
```
Optional verification:
```bash
./scripts/verify-s004-kafka-poison-message.sh
```

## 8. Request/event payload
Script publishes invalid `OrderCreatedEvent` with negative amount (`amount=-10.00`) to topic `order-created`.

## 9. Expected HTTP response if applicable
Not applicable (Kafka event scenario).

## 10. Expected logs
`inventory-service` logs include:
- `operation=kafka_processing_failed`
- `operation=kafka_dlq_published`
With metadata such as topic/partition/offset and `correlation_id`.

## 11. Expected metrics
- No scenario-specific metric contract is guaranteed in this document.
- Consumer failure/retry counters may increase if runtime metrics are enabled.

## 12. Expected traces
- If tracing is enabled for messaging, failed consumer processing and DLQ publish spans may appear.

## 13. Expected root cause
Semantic validation failure (`amount <= 0`) causes deterministic poison-message exception in `inventory-service`.

## 14. What the AI diagnostics agent should conclude
A poison message on `order-created` repeatedly failed in `inventory-service` and was quarantined to `order-created-dlq` after retries.

## 15. Known limitations
- Trace/metric visibility depends on runtime observability configuration.
- Exact retry timing depends on configured backoff values.

## 16. Troubleshooting
- Confirm consumer is subscribed and running.
- Confirm `app.kafka.topics.order-created-dlq` topic exists and is readable.
