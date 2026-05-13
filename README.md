# microservices-observability-failure-playground

A production-style incident playground built with **Java 21** and **Spring Boot 3.x** to generate repeatable cross-service failures for AI-assisted diagnostics.

## Project purpose

This repository provides deterministic failure scenarios (timeouts, dependency errors, message-delivery issues, and bad data paths) with full telemetry. It enables validation of whether an AI diagnostics agent can correlate logs, metrics, and traces to identify root causes quickly.

## High-level architecture

- `api-gateway` fronts client requests and propagates trace context.
- `orders-service` orchestrates order lifecycle.
- `payments-service`, `inventory-service`, and `notification-service` are downstream dependencies.
- `audit-service` captures immutable operational events.
- Shared infrastructure in Docker Compose provides observability and messaging dependencies.

## Services

- `api-gateway` (port 8080)
- `orders-service` (port 8081)
- `payments-service` (port 8082)
- `inventory-service` (port 8083)
- `notification-service` (port 8084)
- `audit-service` (port 8085)

Each service is an **independent Maven Spring Boot project** for simple local execution.

## Failure scenarios

Scenario playbooks are under `scenarios/`:

1. Downstream payment timeout causing order failures.
2. Inventory stale-read or oversell path causing compensations.
3. Notification queue backlog and delayed delivery.
4. Kafka consumer lag / poison-message behavior.
5. Google Pub/Sub publish/auth failure path.
6. RestTemplate DNS/connection errors between services.

## Observability stack

- Spring Boot Actuator + Micrometer metrics
- OpenTelemetry tracing via OTLP exporter
- Prometheus (metrics scrape)
- Tempo (trace backend)
- Grafana (dashboards + trace pivot)
- Loki + Promtail (log aggregation)

Configuration lives in `observability/` and is wired by `docker-compose.yml`.

## AI diagnostics agent workflow

The playground is designed for an agent to:

1. Receive an incident signal (error-rate spike, latency SLO breach, queue lag).
2. Retrieve candidate trace IDs from logs/metrics.
3. Traverse distributed traces to isolate the failing span/service.
4. Correlate infrastructure and runtime symptoms (JVM pressure, retries, circuit behavior).
5. Produce a root-cause statement plus confidence and remediation suggestions.

## Run locally

1. Start observability and shared dependencies:
   ```bash
   docker compose up -d
   ```
2. Start each service in a separate terminal:
   ```bash
   cd <service>
   mvn spring-boot:run
   ```
3. Validate health endpoints:
   ```bash
   curl http://localhost:8080/actuator/health
   ```

## Trigger incidents

Use helper scripts in `scripts/` and scenario instructions in `scenarios/`.
Example (future):
```bash
./scripts/trigger-payment-timeout.sh
```

## Find trace IDs

1. Trigger traffic through `api-gateway`.
2. Inspect logs for `traceId` fields.
3. Open Grafana Explore and query logs for a failing request.
4. Pivot from logs to the corresponding Tempo trace.

## Expected outputs from each scenario

For every scenario, expect:
- a predictable user-facing symptom (HTTP 5xx, delayed async confirmation, etc.),
- a known failing component,
- specific telemetry signatures (error logs, span status/error tag, metric deltas),
- an unambiguous root cause that can be validated by trace ID.
