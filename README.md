# microservices-observability-failure-playground

First-pass, stability-first implementation for a Spring Boot microservices failure playground.

## First-pass scope

### Fully implemented
- repository structure
- `api-gateway`
- `orders-service`
- `payments-service`
- PostgreSQL for `orders-service`
- Docker Compose (reduced runtime stack)
- **S001** RestTemplate timeout
- successful order flow
- structured correlation ID logging
- actuator endpoints
- scripts for successful flow and S001
- README and S001 scenario documentation

### Skeleton / placeholders only
- `inventory-service`
- `notification-service`
- `audit-service`
- Kafka configuration
- Pub/Sub abstraction
- remaining scenario docs (`S002`–`S008`)
- `observability/` folder

> This pass intentionally avoids fully implementing Kafka/PubSub/Loki/Prometheus/Grafana/Tempo to keep the E2E path stable.

## Repository structure

```text
microservices-observability-failure-playground/
  README.md
  docs/
  scenarios/
  docker-compose.yml
  observability/               # placeholder for later passes
  scripts/
  api-gateway/                 # implemented
  orders-service/              # implemented
  payments-service/            # implemented
  inventory-service/           # skeleton
  notification-service/        # skeleton
  audit-service/               # skeleton
```

## Implementation summary (requested)

### 1) Summary of what was created
- End-to-end HTTP flow across `api-gateway -> orders-service -> payments-service`.
- `orders-service` persistence with PostgreSQL and order status updates.
- Failure simulation for **S001** where downstream payment response delay exceeds client timeout.
- Local helper scripts for startup, shutdown, success flow, S001 trigger, and log inspection.
- Initial scenario docs and architecture notes to support observability/failure drills.

### 2) How to run locally
Option A (recommended):
```bash
./scripts/run-local.sh
```

Option B (equivalent manual command):
```bash
docker compose up -d --build
```

Health checks:
```bash
curl http://localhost:8080/actuator/health
curl http://localhost:8081/actuator/health
curl http://localhost:8082/actuator/health
```

Stop:
```bash
./scripts/stop-local.sh
```

### 3) How to trigger successful request
```bash
./scripts/trigger-successful-order.sh
```

### 4) How to trigger S001 RestTemplate timeout
```bash
./scripts/trigger-s001-resttemplate-timeout.sh
```

Expected behavior: request fails from `orders-service` perspective due to `RestTemplate` read timeout while `payments-service` intentionally delays.

### 5) Known limitations
- Only S001 is fully implemented end-to-end in this first pass.
- Kafka/PubSub and most asynchronous workflows are placeholders.
- Full observability stack assets exist but are not positioned as production-ready.
- Failure scenarios `S002`–`S008` are partially or fully deferred.
- Current setup is local-development focused (no hardening/production concerns yet).

### 6) Next recommended task
Implement **S002 payments HTTP 500** end-to-end with:
- deterministic failure toggle in `payments-service`,
- explicit error mapping and status propagation in `orders-service`,
- scenario-specific assertions/tests,
- docs + script parity matching S001 ergonomics.

## Scenarios in this pass

### Successful order flow
```bash
./scripts/trigger-successful-order.sh
```

### S001 RestTemplate timeout
```bash
./scripts/trigger-s001-resttemplate-timeout.sh
```

Expected result: timeout response caused by `payments-service` delay exceeding `orders-service` RestTemplate timeout.

## Notes

- Correlation ID is propagated via `X-Correlation-Id` and emitted in structured logs.
- Actuator endpoints are exposed for health/metrics visibility.
- Additional scenarios and full observability stack are deferred to later passes.
