# Observability stack

This folder contains a runnable local observability stack:
- OpenTelemetry Collector (`observability/otel-collector/otel-collector.yml`)
- Prometheus (`observability/prometheus/prometheus.yml`)
- Grafana datasource/dashboard provisioning
- Loki (`observability/loki/loki-config.yml`)
- Promtail (`observability/promtail/promtail-config.yml`)
- Tempo (`observability/tempo/tempo.yml`)

## Start
```bash
docker compose up -d --build
```

## Access
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## Correlation workflow
1. Trigger scenario, get `correlationId` from API response.
2. Search Loki logs by correlation ID.
3. Copy `trace_id` from logs and search Tempo in Grafana Explore.
4. Validate metric impact on dashboard (request rate, error rate, latency, health).
