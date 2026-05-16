# Observability model

## What is currently verified
- `./scripts/verify-observability-stack.sh` starts Milestone 1 + observability profile and validates health for Grafana, Prometheus, Loki, Tempo, and OTel Collector.
- The script triggers application traffic with a unique correlation ID prefixed as `observability-`.
- The script verifies request success and checks Docker container logs for the correlation ID.
- The script performs a deterministic Loki query API assertion and fails if no matching log line is returned for the correlation ID.
- The script verifies Prometheus health and Targets API reachability.
- The script attempts deterministic Tempo trace lookup when a stable trace ID can be extracted from logs.

## Observability readiness status
- **Loki ingestion proof: Implemented** (query assertion by correlation ID).
- **Tempo trace assertion: Partially implemented** (best-effort: if trace ID extraction fails or Tempo lookup does not return the extracted trace, verifier emits warning and continues).
- Overall readiness remains **partially implemented** until deterministic Tempo assertion is always stable.

## Query examples
- Loki readiness: `curl -fsS http://localhost:3100/ready`
- Loki query by correlation ID:
  - `curl -fsS "http://localhost:3100/loki/api/v1/query_range?query={service=~\"api-gateway|orders-service|payments-service\"}%20|=%20\"<correlation-id>\"&limit=20"`
- Prometheus targets API:
  - `curl -fsS http://localhost:9090/api/v1/targets`
- Tempo trace lookup (when trace ID is known):
  - `curl -fsS "http://localhost:3200/api/traces/<trace-id>"`

## Tempo limitation behavior
If trace ID extraction from runtime logs is not stable/reliable in a given environment, verifier output is:

`WARNING: Tempo is reachable, but deterministic trace assertion is not implemented because trace ID extraction is not stable.`

In these warning paths, script still proves required Loki ingestion and component reachability, but does not claim full Tempo evidence.

## Known limitations
- Promtail relies on Docker host mounts (`/var/run/docker.sock` and `/var/lib/docker/containers`) in read-only mode; this can vary across host runtimes (Docker Desktop VM mappings, rootless Docker, CI container isolation).
- Tempo assertion depends on log availability of trace IDs; if missing/unstable, fallback warning is emitted.

## Troubleshooting
1. Confirm observability stack is running:
   - `docker compose --profile observability ps`
2. Check Promtail sees Docker containers:
   - `docker compose logs promtail | tail -n 100`
3. Validate Loki endpoint and query manually:
   - `curl -fsS http://localhost:3100/ready`
   - run query example above with a known correlation ID.
4. If Tempo lookup fails, inspect service logs for `trace_id=` fields:
   - `docker compose logs --since=5m api-gateway orders-service payments-service | grep trace_id=`
5. If Docker host paths are unavailable, run with an environment that exposes `/var/run/docker.sock` and `/var/lib/docker/containers` to Compose mounts.
