# S004 — Kafka poison message

## Scenario ID
S004

## Description
Simulates a malformed or semantically invalid Kafka event that repeatedly fails consumer processing.

## Services involved
- Event producer (likely `orders-service`)
- Consumer (`inventory-service` and/or `audit-service`)
- Kafka broker

## How to enable the scenario
Placeholder:
- Add producer/fixture route that emits invalid schema or unsupported payload.
- Configure consumer retry/DLQ behavior for deterministic replay.

## How to trigger it
- Publish one intentionally malformed event to target topic.

## Expected logs
- Deserialization/validation exceptions on consumer side.
- Repeated processing attempts for same offset/key.

## Expected traces
- Error spans in consumer processing pipeline.
- Potentially missing downstream spans due to early deserialization failure.

## Expected metrics
- Consumer error counter increases.
- Retry count and/or DLQ publish metrics increase.
- Consumer lag may grow.

## Expected root cause
Poison event payload cannot be processed by consumer contract.

## What the AI diagnostics agent should conclude
A specific Kafka message is toxic; durable remediation is schema/validation alignment and DLQ handling.

## Known limitations
- DLQ and deterministic poison-message fixture may be incomplete.
