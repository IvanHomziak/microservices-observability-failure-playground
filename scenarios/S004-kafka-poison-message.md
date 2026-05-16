# S004 — Kafka poison message

## 1. Scenario ID
S004

## 2. Status
Implemented

## 3. Purpose
Validate deterministic poison-message handling in the `inventory-service` Kafka consumer.

## 4. Runtime override
- Override: `docker-compose.s004.yml`
- Profile: `kafka`

## 5. Services involved
- `api-gateway`
- `orders-service`
- `payments-service`
- `inventory-service`
- `redpanda`

## 6. Deterministic configuration
This scenario enables deterministic poison-mode behavior for Kafka consumption.

- `orders-service`: `ORDERS_EVENTS_KAFKA_ENABLED=true`
- `inventory-service`: `INVENTORY_FAILURE_SIMULATION_POISON_MESSAGE_ENABLED=true`

## 7. Trigger script
```bash
./scripts/trigger-s004-kafka-poison-message.sh
```

The trigger sends `POST /api/orders` through `api-gateway` and prints:
- `correlation_id` (prefixed with `s004-`)
- `http_status`
- `response_body`

Deterministic environment setup is handled by the verify script.

## 8. Verify script
```bash
./scripts/verify-s004-kafka-poison-message.sh
```

The verifier:
1. Starts runtime with:
   - `docker compose -f docker-compose.yml -f docker-compose.s004.yml --profile kafka up -d --build --force-recreate`
2. Waits for health of:
   - `api-gateway`, `orders-service`, `payments-service`, `inventory-service`
3. Runs trigger script and extracts `correlation_id`
4. Asserts:
   - order API response status is `2xx`
   - `orders-service` has `operation=kafka_event_published`
   - `inventory-service` has `operation=kafka_processing_failed`
   - `inventory-service` has `PoisonMessageException` or `Simulated poison message`
   - DLQ evidence via `operation=kafka_dlq_published` and/or `order-created-dlq` topic sample
5. Prints debug command:
   - `docker compose logs -f orders-service inventory-service redpanda`
6. Restores default `orders-service` runtime on exit.

## 9. Expected logs
For matching `correlation_id`:
- `orders-service`: `operation=kafka_event_published`
- `inventory-service`: `operation=kafka_processing_failed`
- `inventory-service`: `PoisonMessageException` or `Simulated poison message`
- Optional/expected when DLQ path executes: `operation=kafka_dlq_published`

## 10. Expected DLQ behavior
If DLQ is functioning, failed records are published to `order-created-dlq` after retries.

## 11. Known limitations
DLQ assertion may be log-format/runtime dependent; verifier falls back to sampling DLQ topic content.

## 12. AI diagnostics expected conclusion
Root cause is deterministic poison message handling in inventory-service Kafka consumer.
