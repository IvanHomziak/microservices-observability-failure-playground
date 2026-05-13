# microservices-observability-failure-playground

## Milestone 1 (stable, runnable)

### Implemented now
- `api-gateway`, `orders-service`, `payments-service`, PostgreSQL.
- Docker Compose end-to-end order flow.
- Successful order path through `POST /api/orders`.
- S001 (`RestTemplate` timeout from orders -> payments).
- Correlation ID propagation and error contract with correlation ID.
- Kafka publishing feature-flagged OFF by default for this milestone.
- Notification publishing implemented as local simulated log publish (no external Pub/Sub dependency).

### Deferred (not required in Milestone 1)
- Real Kafka/Redpanda integration as a runtime dependency.
- Real Pub/Sub integration.
- Grafana/Loki/Tempo/Prometheus production-ready stack.
- Other scenarios (`S002+`) as complete E2E flows.

## Run
```bash
docker compose up -d --build
```

## Deterministic Milestone 1 verification
```bash
./scripts/verify-milestone-1.sh
```
This runs the full local Milestone 1 contract verification (stack startup, health checks, SUCCESS flow assertions, and S001 timeout assertions) without requiring Kafka, Pub/Sub, or the observability stack.

## Health checks
```bash
curl http://localhost:8080/actuator/health
curl http://localhost:8081/actuator/health
curl http://localhost:8082/actuator/health
```

## Successful flow
```bash
./scripts/trigger-successful-order.sh
```
Expected: HTTP 2xx with JSON similar to:
```json
{
  "orderId": "<uuid>",
  "status": "PAYMENT_CONFIRMED",
  "correlationId": "success-...",
  "traceId": "..."
}
```

## S001 timeout flow
```bash
./scripts/trigger-s001-resttemplate-timeout.sh
```
Expected: HTTP `504` with JSON similar to:
```json
{
  "code": "PAYMENT_TIMEOUT",
  "message": "Timeout while calling payment service",
  "correlationId": "s001-...",
  "timestamp": "2026-...Z"
}
```

## Known limitations
- `traceId` can be empty if no active tracing span context is present for a specific response path.
- S001 depends on timeout/delay settings; timing can vary slightly by host performance.
- Placeholder services (`inventory-service`, `notification-service`, `audit-service`) are outside the stable Milestone 1 E2E path.
