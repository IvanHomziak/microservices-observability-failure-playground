# S005 — Kafka consumer lag growth

## Scenario ID
S005

## Status
Implemented

## Description
Simulates deterministic consumer-side slowdown in `inventory-service` so produced `order-created` events accumulate and consumer lag/backlog becomes observable.

## Services involved
- `orders-service` (event producer in normal flow)
- `inventory-service` (slow consumer under simulation)
- Redpanda / Kafka broker
- Redpanda Console (lag inspection)

## Config toggles
Set on `inventory-service`:
- `inventory.failure-simulation.consumer-lag-mode-enabled` (default `false`)
- `inventory.failure-simulation.processing-delay-ms` (default `0`)

Optional existing toggle (unrelated to lag mode):
- `inventory.failure-simulation.poison-message-enabled`

Example env vars:
- `INVENTORY_FAILURE_SIMULATION_CONSUMER_LAG_MODE_ENABLED=true`
- `INVENTORY_FAILURE_SIMULATION_PROCESSING_DELAY_MS=1200`

## How to trigger
1. Start stack with lag mode enabled on `inventory-service`.
2. Run burst producer script:
   - `./scripts/trigger-s005-kafka-consumer-lag.sh 40`
3. Optionally run end-to-end verification:
   - `./scripts/verify-s005-kafka-consumer-lag.sh 25`

## Expected metrics
From `inventory-service`:
- `inventory.kafka.messages.consumed`
- `inventory.kafka.messages.failed`
- `inventory.kafka.processing.duration`
- `inventory.kafka.processing.delay`

During S005, expect rising processing duration/delay and observable group lag while burst is being drained.

## Expected logs
`inventory-service` logs include:
- `operation=kafka_processing_delay_simulated`
- `delay_ms`
- `event_id`
- `order_id`
- `correlation_id`

Also expect normal consume/reservation logs for same correlation ids.

## How to inspect lag in Redpanda Console
Open:
- `http://localhost:8081/topics/order-created/consumer-groups/inventory-service`

While delay mode is enabled and burst is running, monitor consumer group lag/backlog on `order-created`.

## Expected root cause
Consumer throughput is intentionally reduced by processing delay; producer outpaces consumer, creating lag.

## What the AI diagnostics agent should conclude
Backlog/consumer-lag incident caused by intentional consumer slowdown in `inventory-service`, not broker outage or message schema corruption.

## Determinism / safety
- Deterministic when lag mode is enabled with non-zero delay and burst count > consumer instantaneous capacity.
- Normal Kafka flow remains unaffected when `inventory.failure-simulation.consumer-lag-mode-enabled=false`.
