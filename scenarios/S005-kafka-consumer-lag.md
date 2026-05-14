# S005 — Kafka consumer lag growth

## 1. Scenario ID
S005

## 2. Status
Implemented

## 3. Purpose
Simulate deterministic consumer slowdown in `inventory-service` so backlog and consumer lag become observable.

## 4. Services involved
- `orders-service`
- `inventory-service`
- `redpanda`
- `redpanda-console`

## 5. Preconditions
- Local stack is running.
- `inventory-service` lag mode is enabled with non-zero delay.

## 6. Configuration toggles
- `inventory.failure-simulation.consumer-lag-mode-enabled=true`
- `inventory.failure-simulation.processing-delay-ms` (for example `1200`)

## 7. How to run
```bash
./scripts/trigger-s005-kafka-consumer-lag.sh 40
```
Optional verification:
```bash
./scripts/verify-s005-kafka-consumer-lag.sh 25
```

## 8. Request/event payload
Burst of order-created events produced by script argument count (for example `40`).

## 9. Expected HTTP response if applicable
Not applicable (Kafka lag scenario).

## 10. Expected logs
`inventory-service` includes delay simulation entries such as:
- `operation=kafka_processing_delay_simulated`
- `delay_ms`
- event/order/correlation fields

## 11. Expected metrics
From `inventory-service`:
- `inventory.kafka.messages.consumed`
- `inventory.kafka.messages.failed`
- `inventory.kafka.processing.duration`
- `inventory.kafka.processing.delay`

## 12. Expected traces
If tracing is enabled, consumer processing spans should show longer durations while lag mode is active.

## 13. Expected root cause
Intentional per-message processing delay in consumer path reduces throughput and creates lag.

## 14. What the AI diagnostics agent should conclude
Observed lag is caused by deterministic consumer slowdown in `inventory-service`, not by broker outage.

## 15. Known limitations
- Requires enough produced load to exceed current consumer throughput.
- Lag visualization depends on Redpanda Console availability.

## 16. Troubleshooting
- Verify `inventory.failure-simulation.consumer-lag-mode-enabled=true` in runtime.
- Increase event burst count if lag is not visible.
