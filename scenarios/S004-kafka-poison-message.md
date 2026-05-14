# S004 — Kafka poison message

## Scenario ID
S004

## Status
Implemented

## Description
Publishes a semantically invalid `OrderCreatedEvent` (`amount=-10.00`) to `order-created`. The `inventory-service` deterministically rejects it, retries according to Kafka error handler configuration, and then routes it to `order-created-dlq`.

## Services involved
- `redpanda` (Kafka broker)
- `inventory-service` (consumer + DLQ publisher)

## How to enable the scenario
No additional toggle required for the deterministic invalid payload path.

Optional config knobs in `inventory-service/src/main/resources/application.yml`:
- `app.kafka.retry.max-attempts` (default `3`)
- `app.kafka.retry.interval-ms` (default `1000`)
- `app.kafka.topics.order-created-dlq` (default `order-created-dlq`)

## How to trigger it
```bash
./scripts/trigger-s004-kafka-poison-message.sh
```

The script publishes an event with negative `amount`, which is always treated as poison.

## Verification
```bash
./scripts/verify-s004-kafka-poison-message.sh
```

The verification script:
1. Triggers S004.
2. Confirms `inventory-service` logged `operation=kafka_processing_failed`.
3. Confirms `inventory-service` logged `operation=kafka_dlq_published`.
4. Confirms `order-created-dlq` contains message/header content with the same `correlation_id`.

It exits non-zero if any check fails.

## Expected logs
- `operation=kafka_processing_failed`
- `operation=kafka_dlq_published`

Both logs include:
- `topic`
- `partition`
- `offset`
- `event_id` (if present)
- `order_id` (if present)
- `correlation_id`
- `exception_type`
- `exception_message`

## Expected DLQ behavior
Topic: `order-created-dlq`

DLQ record preserves/contains:
- original event payload (forwarded by dead-letter recoverer)
- error reason headers (`error_reason`, `error_type`)
- original location headers (`original_topic`, `original_partition`, `original_offset`)
- `correlation_id`

## Expected root cause
Consumer-side semantic validation fails because `amount <= 0`, causing deterministic `PoisonMessageException`.

## What the AI diagnostics agent should conclude
A poison message was consumed from `order-created`, repeatedly failed semantic validation in `inventory-service`, exhausted retries, and was successfully quarantined to `order-created-dlq` without permanently blocking consumption.
