# S005 — Kafka consumer lag growth

## 1. Scenario ID
S005

## 2. Status
Implemented

## 3. Purpose
Create deterministic Kafka backlog behavior by slowing `inventory-service` consumer processing while `orders-service` publishes many order-created events quickly.

## 4. Services involved
- `api-gateway`
- `orders-service`
- `payments-service`
- `inventory-service`
- `redpanda`

## 5. Required override/profile
- Compose files: `docker-compose.yml` + `docker-compose.s005.yml`
- Profile: `--profile kafka`
- Deterministic consumer delay toggle:
  - `INVENTORY_FAILURE_SIMULATION_CONSUMER_LAG_MODE_ENABLED=true`
  - `INVENTORY_FAILURE_SIMULATION_PROCESSING_DELAY_MS=1500`
- Kafka publish toggle:
  - `ORDERS_EVENTS_KAFKA_ENABLED=true`

## 6. Trigger command
```bash
./scripts/trigger-s005-kafka-consumer-lag.sh 20
```

## 7. Verify command
```bash
./scripts/verify-s005-kafka-consumer-lag.sh 20
```

## 8. Evidence model
Verifier requires all of the following:
1. Multiple order API requests succeed.
2. `orders-service` logs include multiple `operation=kafka_event_published` records for `s005-*` correlation IDs.
3. `inventory-service` logs include multiple `operation=kafka_processing_delay_simulated` records for same `s005-*` burst.
4. Optional stronger proof: `rpk group describe inventory-service` reports lag `> 0` for `order-created` during active processing.

If step 4 is unavailable or snapshots at zero, verifier still asserts deterministic delay/backlog evidence from steps 1-3 and prints that limitation explicitly.

## 9. Known flakiness controls
- Uses deterministic fixed consumer delay instead of uncontrolled load spikes.
- Produces burst through API quickly with shared `s005-` correlation prefix for exact log filtering.
- Requires minimum successful request count before assertions.
- Uses bounded wait + explicit service health checks before trigger.

## 11. Expected HTTP result
- Trigger burst requests return `2xx` (typically `201`) for accepted orders while backlog accumulates asynchronously.

## 12. Expected logs
- `orders-service`: repeated `operation=kafka_event_published` for `s005-*` correlation IDs.
- `inventory-service`: repeated `operation=kafka_processing_delay_simulated` for same burst window.

## 13. Known limitations
- Real-time lag snapshots may briefly report `0` depending on timing of group-state sampling.

## 14. Expected AI diagnostics conclusion
Root cause is deterministic slow consumer behavior in inventory-service creating Kafka backlog/lag symptoms.
