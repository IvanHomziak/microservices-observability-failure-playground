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

## Run (first pass)

### 1) Start infrastructure + services
```bash
docker compose up -d --build
```

### 2) Verify actuator health
```bash
curl http://localhost:8080/actuator/health
curl http://localhost:8081/actuator/health
curl http://localhost:8082/actuator/health
```

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
