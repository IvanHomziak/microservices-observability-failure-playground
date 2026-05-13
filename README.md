# microservices-observability-failure-playground

A hands-on incident simulation repository built with **Java 21** and **Spring Boot 3.x**.

This playground is intentionally designed to create realistic microservice failures, then make those failures observable through logs, metrics, and traces so humans and AI agents can practice diagnosis.

## Project purpose

The goal is to provide a repeatable environment where you can:
- trigger known failure modes,
- observe system behavior across service boundaries,
- practice root-cause analysis,
- evaluate how well an AI diagnostics agent can reason over telemetry.

## Functional and observability goals

The playground is expected to support the following:

1. Generate both successful and failing end-to-end requests.
2. Propagate trace IDs across HTTP, Kafka, and Pub/Sub-like flows where possible.
3. Emit structured logs with `service_name`, `trace_id`, `span_id`, `correlation_id`, `request_id`, and domain IDs.
4. Expose metrics via Spring Boot Actuator and Micrometer.
5. Produce distributed traces through OpenTelemetry.
6. Provide deterministic failure toggles.
7. Provide documented scenarios with expected root causes.
8. Allow an external AI diagnostics agent to query telemetry and return an evidence-based diagnostic report.

The system should remain intentionally simple from a business perspective while being strong from an observability and failure-analysis perspective.

## High-level architecture

Client traffic enters through `api-gateway`, then fans out to domain services. The domain flow is centered around order processing:

1. `orders-service` receives order requests.
2. `orders-service` calls `payments-service` and `inventory-service`.
3. `orders-service` emits events for `notification-service` and `audit-service`.
4. All services emit telemetry to the observability stack.

## Repository structure

```text
microservices-observability-failure-playground/
  README.md
  docs/
  scenarios/
  docker-compose.yml
  observability/
  scripts/
  api-gateway/
  orders-service/
  payments-service/
  inventory-service/
  notification-service/
  audit-service/
```

Each service is a **standalone Maven Spring Boot project** (not a complex multi-module parent build), to keep local execution simple and explicit.

## Services

- `api-gateway` (HTTP entrypoint, trace context propagation) - default port `8080`
- `orders-service` (orchestration) - default port `8081`
- `payments-service` (payment authorization/capture simulation) - default port `8082`
- `inventory-service` (reservation/stock simulation) - default port `8083`
- `notification-service` (async user communication simulation) - default port `8084`
- `audit-service` (immutable operational audit events) - default port `8085`

## Failure scenarios

The `scenarios/` folder contains predefined incident playbooks, for example:
- downstream timeout and retry storms,
- inventory consistency mismatches,
- queue backlog / delayed notifications,
- poison messages and consumer lag,
- connectivity failures (DNS/refused connection),
- auth/publish failures on external integrations.

Each scenario will include:
- setup steps,
- trigger command(s),
- expected user-visible impact,
- expected telemetry signatures,
- recovery/rollback guidance.

## Observability stack

`docker-compose.yml` provisions local tooling for cross-signal analysis:
- **Prometheus** for metrics scraping,
- **Grafana** for dashboards and investigation,
- **Tempo** for distributed tracing,
- **Loki** for centralized logs,
- plus supporting messaging infrastructure (Kafka/Zookeeper).

Observability configuration files live under `observability/`.

## How an AI diagnostics agent uses this playground

A diagnostics agent can run the following loop:
1. detect an incident signal (e.g., elevated 5xx, latency spikes),
2. discover candidate failing requests,
3. extract `traceId` from logs,
4. pivot to traces and map cross-service causal chains,
5. correlate metrics/logs/traces to infer likely root cause,
6. return a diagnosis with confidence and remediation suggestions.

Because scenarios are deterministic, the diagnosis can be validated against expected outcomes.

## Run locally

### 1) Start shared infrastructure

```bash
docker compose up -d
```

### 2) Start each Spring Boot service

Open a terminal per service:

```bash
cd api-gateway && mvn spring-boot:run
cd orders-service && mvn spring-boot:run
cd payments-service && mvn spring-boot:run
cd inventory-service && mvn spring-boot:run
cd notification-service && mvn spring-boot:run
cd audit-service && mvn spring-boot:run
```

### 3) Verify readiness

```bash
curl http://localhost:8080/actuator/health
curl http://localhost:8081/actuator/health
```

## How to trigger incidents

Use scripts from `scripts/` (to be expanded per scenario) and scenario playbooks in `scenarios/`:

```bash
./scripts/trigger-payment-timeout.sh
```

## How to find trace IDs

1. Send a request through `api-gateway`.
2. Locate the request in service logs and copy `traceId`.
3. In Grafana Explore, query logs in Loki for that `traceId`.
4. Pivot to Tempo trace view to inspect spans and error boundaries.

## Trace and correlation propagation status

- **HTTP**
  - `traceparent` is propagated by Spring/Micrometer instrumentation on normal flows.
  - `X-Correlation-Id` is preserved from gateway to downstream services when supplied.
  - Scenario `S007` can intentionally break trace propagation on `orders-service -> payments-service`.
- **Kafka**
  - `orders-service` includes `correlation_id` and `trace_id` in the event payload.
  - `orders-service` also includes `correlation_id` and `traceparent` in Kafka headers.
  - Current consumers primarily rely on payload fields; header-based trace continuation is logged but not fully rehydrated into a consumer span context.
- **Pub/Sub-like flow (`notification-service` in-memory adapter)**
  - Correlation and trace fields are included in emitted notification payload logs.
  - Because the adapter is in-memory and not a real broker client, distributed trace context is not automatically continued as broker spans end-to-end.

## Expected outputs from each scenario

Every scenario should produce all of the following:
- **Application symptom**: e.g., HTTP 500/504, slow response, delayed async completion.
- **Telemetry pattern**: correlated error logs, span error status, and metric anomalies.
- **Root-cause target**: one primary failing dependency/service with supporting evidence.
- **Validation signal**: a trace-level and/or metric-level condition that confirms the diagnosis.

This makes the playground suitable for both training and benchmarking operational diagnostics.
