# Observability model

## What is currently verified
- `./scripts/verify-observability-stack.sh` starts Milestone 1 + observability profile and validates health for Grafana, Prometheus, Loki, Tempo, and OTel Collector.
- The script triggers application traffic (`trigger-successful-order.sh`) with a unique correlation ID.
- The script verifies Prometheus and Tempo endpoints are reachable.
- The script checks Docker container logs for the correlation ID as a fallback evidence path.

## What is not automatically verified
- End-to-end Loki ingestion for application logs is **not** automatically asserted.
- Automatic Tempo trace lookup by trace ID is **not** asserted.
- Therefore observability readiness is **Partially implemented** (component health + triggerability, not full query proof).

## How to inspect Grafana
- URL: `http://localhost:3000`
- Default credentials: `admin/admin`
- Use **Explore** to query Prometheus/Loki/Tempo datasources.

## How to inspect Prometheus
- URL: `http://localhost:9090`
- Health: `http://localhost:9090/-/healthy`
- Example target check: **Status -> Targets** (gateway/orders/payments should be UP).

## How to inspect Loki
- Readiness: `http://localhost:3100/ready`
- Example query in Grafana Explore (Loki datasource):
  - `{service=~"api-gateway|orders-service|payments-service"} |= "<correlation-id>"`

## How to inspect Tempo
- Readiness: `http://localhost:3200/ready`
- In Grafana Explore, select Tempo datasource and search by trace ID from logs.

## Known limitations
- Loki ingestion can vary by Docker logging environment; verification script does not fail on missing Loki query evidence.
- Trace search requires manual extraction of trace IDs from logs or responses.

## Future hardening path
1. Add deterministic Loki query assertion in `verify-observability-stack.sh` by correlation ID.
2. Add deterministic trace extraction + Tempo API lookup assertion.
3. Promote observability status from *Partially implemented* to *Implemented* after both assertions are stable in CI/runtime.
