# microservices-observability-failure-playground

## Project purpose
This repository is a deterministic playground for practicing incident diagnosis in a microservices environment. The current stable scope is intentionally small so failures are reproducible and evidence is easy to correlate across HTTP responses, logs, and service boundaries.

## Milestone 1 scope (current truth)
Milestone 1 is the first stable vertical slice:
- Synchronous HTTP request flow through `api-gateway -> orders-service -> payments-service`.
- PostgreSQL persistence used by `orders-service`.
- Two fully implemented failure scenarios: **S001 RestTemplate timeout** and **S002 payments HTTP 500**.
- Correlation ID propagation and stable error contract for timeout failures.

## Implemented services (Milestone 1)
- `api-gateway`
- `orders-service`
- `payments-service`
- `postgres`

## Deferred services/features (not part of Milestone 1 acceptance)
- Kafka end-to-end runtime flow (producer/consumer topology is not required for this milestone).
- Real Pub/Sub integration.
- Full observability stack validation (Grafana/Loki/Tempo/Prometheus are present as config/assets, but not part of the required runnable contract in Milestone 1).
- Scenarios `S002`–`S008` as fully working end-to-end implementations.

## How an AI diagnostics agent should use this playground
The intended loop for an AI diagnostics agent in Milestone 1 is:
1. Trigger a known scenario (`SUCCESS` or `S001`).
2. Read the API symptom from the gateway response.
3. Pivot by `correlationId` through `api-gateway`, `orders-service`, and `payments-service` logs.
4. Confirm service boundary behavior (`orders-service` timeout while calling `payments-service`).
5. Produce a root-cause conclusion and confidence statement.

Because S001 is deterministic, the agent can be validated against expected conclusions, not just generic anomaly detection.

## Run locally
```bash
docker compose up -d --build
```

Optional teardown:
```bash
./scripts/stop-local.sh
```

## Verify Milestone 1
Use the deterministic verifier script:
```bash
./scripts/verify-milestone-1.sh
```

This script:
- starts the stack,
- waits for health checks on `8080`, `8081`, `8082`,
- verifies a successful order flow,
- verifies S001 timeout flow returns the expected contract.

## Trigger successful flow
```bash
./scripts/trigger-successful-order.sh
```
Endpoint used: `POST /api/orders` via `http://localhost:8080/api/orders`.

### Expected SUCCESS response
HTTP: `2xx`

Representative body shape:
```json
{
  "orderId": "<uuid>",
  "status": "PAYMENT_CONFIRMED",
  "correlationId": "success-...",
  "traceId": "..."
}
```

## Trigger S002 (payments HTTP 500)
```bash
./scripts/trigger-s002-payments-http-500.sh
```

### Expected S002 response
HTTP: `502 Bad Gateway`

Representative body shape:
```json
{
  "code": "PAYMENT_5XX",
  "message": "Payment service returned 5xx status",
  "correlationId": "s002-...",
  "timestamp": "2026-...Z"
}
```

## Trigger S001 (RestTemplate timeout)
```bash
./scripts/trigger-s001-resttemplate-timeout.sh
```
Endpoint used: `POST /api/orders` via `http://localhost:8080/api/orders`.

### Expected S001 response
HTTP: `504 Gateway Timeout`

Representative body shape:
```json
{
  "code": "PAYMENT_TIMEOUT",
  "message": "Timeout while calling payment service",
  "correlationId": "s001-...",
  "timestamp": "2026-...Z"
}
```

## Known limitations
- `S001` depends on timeout-vs-delay timing and can vary slightly by host performance.
- `traceId` may be empty in some response paths even when `correlationId` is present.
- Placeholder services (`inventory-service`, `notification-service`, `audit-service`) are not part of the stable Milestone 1 E2E contract.
- Do not treat Kafka/PubSub/observability UI assets as validated runtime features for Milestone 1 unless you explicitly enable and test them.

## Next recommended milestone
**Milestone 2 recommendation:** implement and stabilize **S002 (payments HTTP 500)** as the second deterministic synchronous failure, then add automated verification for S001 + S002 together before expanding asynchronous infrastructure.

## Observability stack (local runnable)
The repository now includes a local observability stack for `api-gateway`, `orders-service`, `payments-service`, and PostgreSQL:
- OTel Collector receives OTLP traces from all three Spring services.
- Prometheus scrapes `/actuator/prometheus` from each service.
- Promtail ships container logs to Loki.
- Tempo stores distributed traces.
- Grafana provisions Prometheus/Loki/Tempo datasources and a `Microservices Overview` dashboard.

Run verification:
```bash
./scripts/verify-observability-stack.sh
```

### How logs, metrics, traces connect
- Use `correlationId` from API response to search logs in Loki.
- From matching log lines, copy `trace_id` to inspect full trace in Tempo.
- Use dashboard panels for request rate, error rate, p95 latency, and service health.

### Prometheus targets
- `api-gateway:8080/actuator/prometheus`
- `orders-service:8081/actuator/prometheus`
- `payments-service:8082/actuator/prometheus`

### AI diagnostics agent workflow
1. Trigger SUCCESS or S001.
2. Capture `correlationId` and `traceId`.
3. Query Loki by correlation ID.
4. Query Tempo by trace ID.
5. Confirm impact via Prometheus metrics and Grafana dashboard.

## Kafka async order-created flow (Redpanda)
Milestone 1 default remains `orders.events.kafka.enabled=false` in `orders-service` config. In Docker Compose we explicitly enable Kafka publishing for local async flow validation.

### New runtime components
- `redpanda` broker on `localhost:9092`
- `redpanda-console` on `http://localhost:8088`
- `inventory-service` consuming `order-created` with group `inventory-service`

### Topics
- `order-created`
- `order-created-dlq`

### Scripts
```bash
./scripts/trigger-kafka-success-flow.sh
./scripts/verify-kafka-flow.sh
```
