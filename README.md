# microservices-observability-failure-playground

## Project purpose
This repository is a deterministic playground for practicing incident diagnosis in a microservices environment. It is designed to generate reproducible production-like failures so an AI diagnostics agent can reason over HTTP symptoms, logs, metrics, traces, and service boundaries.

## Runtime contract

### Default stack: Milestone 1
The default command starts only the stable synchronous slice:

```bash
docker compose up -d --build
```

Default services:
- `postgres`
- `api-gateway`
- `orders-service`
- `payments-service`

Default stack intentionally does **not** start Kafka, notification, audit, or observability services. This keeps the first acceptance path deterministic and avoids failures caused by optional infrastructure.

### Optional profiles
Use profiles when testing broader flows:

```bash
# Kafka / Redpanda + inventory-service
docker compose --profile kafka up -d --build

# notification-service + audit-service
docker compose --profile async up -d --build

# OTel Collector + Prometheus + Grafana + Loki + Tempo
docker compose --profile observability up -d --build

# everything
docker compose --profile full up -d --build
```

## Milestone 1 scope
Milestone 1 is the first stable vertical slice:
- synchronous HTTP request flow through `api-gateway -> orders-service -> payments-service`;
- PostgreSQL persistence used by `orders-service`;
- implemented failure scenarios: **S001 RestTemplate timeout** and **S002 payments HTTP 500**;
- correlation ID propagation and stable error contracts.

## Implemented services
- `api-gateway`
- `orders-service`
- `payments-service`
- `inventory-service`
- `notification-service`
- `audit-service`

Only `api-gateway`, `orders-service`, `payments-service`, and `postgres` are part of the default Milestone 1 runtime contract. Other services are opt-in via profiles.

## How an AI diagnostics agent should use this playground
The intended loop for an AI diagnostics agent is:
1. Trigger a known scenario.
2. Read the API symptom from the gateway response.
3. Pivot by `correlationId` through service logs.
4. Use traces and metrics when the observability profile is enabled.
5. Produce an evidence-based root-cause conclusion and confidence statement.

Because scenarios are deterministic, the agent can be evaluated against expected conclusions, not just generic anomaly detection.

## Run locally

### Start default Milestone 1 stack
```bash
docker compose up -d --build
```

### Stop stack
```bash
./scripts/stop-local.sh
```

## Verify Milestone 1
Use the deterministic verifier script:

```bash
./scripts/verify-milestone-1.sh
```

This script:
- starts the default stack;
- waits for health checks on `8080`, `8081`, `8082`;
- verifies a successful order flow;
- verifies S001 timeout flow returns the expected contract.

## Trigger successful flow
```bash
./scripts/trigger-successful-order.sh
```

Endpoint used: `POST /api/orders` via `http://localhost:8080/api/orders`.

Expected HTTP: `2xx`

Representative body shape:
```json
{
  "orderId": "<uuid>",
  "status": "PAYMENT_CONFIRMED",
  "correlationId": "success-...",
  "traceId": "..."
}
```

## Trigger S001: RestTemplate timeout
```bash
./scripts/trigger-s001-resttemplate-timeout.sh
```

Expected HTTP: `504 Gateway Timeout`

Representative body shape:
```json
{
  "code": "PAYMENT_TIMEOUT",
  "message": "Timeout while calling payment service",
  "correlationId": "s001-...",
  "timestamp": "2026-...Z"
}
```

## Verify S002: payments HTTP 500
S002 requires a deterministic payments-service override. Use the verifier, not only the trigger script:

```bash
./scripts/verify-s002-payments-http-500.sh
```

The verifier starts:

```bash
docker compose -f docker-compose.yml -f docker-compose.s002.yml up -d --build
```

Expected HTTP: `502 Bad Gateway`

Representative body shape:
```json
{
  "code": "PAYMENT_5XX",
  "message": "Payment service returned 5xx status",
  "correlationId": "s002-...",
  "timestamp": "2026-...Z"
}
```

## Observability stack
The observability stack is opt-in:

```bash
./scripts/verify-observability-stack.sh
```

This uses the `observability` profile and starts:
- OTel Collector;
- Prometheus;
- Grafana;
- Loki;
- Promtail;
- Tempo.

Notes:
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`
- Loki: `http://localhost:3100`
- Tempo: `http://localhost:3200`

Current limitation: Promtail is configured as an opt-in observability component. The compose file does not mount the host Docker socket in this stabilization PR, so log shipping behavior may need follow-up runtime verification depending on the target environment.

## Kafka async order-created flow
Kafka is opt-in:

```bash
docker compose --profile kafka up -d --build
./scripts/verify-kafka-flow.sh
```

Runtime components:
- `redpanda` broker on `localhost:9092`;
- `redpanda-console` on `http://localhost:8088`;
- `inventory-service` consuming `order-created`.

Topics:
- `order-created`
- `order-created-dlq`

## Notification flow
Notification and audit services are opt-in through the `async` or `full` profile.

Docs:
- `docs/pubsub-style-notification-flow.md`
- `docs/audit-service.md`

Scripts:
```bash
./scripts/verify-notification-flow.sh
./scripts/verify-audit-flow.sh
```

## Scenario documentation
Scenario index:

```text
scenarios/README.md
```

Rule for implementation status:
A scenario should be considered implemented only if it has:
1. code path;
2. deterministic config toggle;
3. trigger script;
4. verification script;
5. scenario documentation matching actual behavior.

## AI diagnostics artifacts
- Contract: `docs/ai-diagnostics-contract.md`
- Evidence schema: `docs/evidence-pack-schema.md`
- Sample agent reports: `docs/sample-agent-reports/`

## Continuous Integration
A CI workflow is defined at `.github/workflows/ci.yml` and runs on pushes to `main` and on pull requests.

It validates:
- Maven tests for each service;
- shell script syntax via `bash -n scripts/*.sh`;
- Docker Compose syntax via `docker compose config`.

## Known limitations
- Runtime verification still depends on local Docker and Maven availability.
- Some Maven runs in previous automated tasks were blocked by Maven Central `403` responses in the execution environment.
- `traceId` may be empty in some response paths even when `correlationId` is present.
- Optional profiles should be validated independently; the default stack is intentionally small.
