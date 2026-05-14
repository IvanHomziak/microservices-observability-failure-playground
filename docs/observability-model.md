# Observability model

## Signal flow
1. Spring Boot services emit metrics at `/actuator/prometheus` and are scraped by Prometheus.
2. Services emit traces via OTLP HTTP to `otel-collector:4318`; collector exports traces to Tempo.
3. Container logs are tailed by Promtail from Docker socket and sent to Loki.
4. Grafana visualizes Prometheus metrics, Loki logs, and Tempo traces.

## Correlation strategy
- `X-Correlation-Id` is propagated from gateway to downstream services.
- Logs include `correlation_id`, `trace_id`, and `span_id` fields.
- Use correlation ID for request-level pivot, trace ID for distributed call graph.

## Prometheus scraping
Prometheus scrapes:
- `api-gateway:8080/actuator/prometheus`
- `orders-service:8081/actuator/prometheus`
- `payments-service:8082/actuator/prometheus`

## Query examples
### Loki by correlation ID
```logql
{service=~"api-gateway|orders-service|payments-service"} |= "<correlation-id>"
```

### Tempo by trace ID
In Grafana Explore:
- Datasource: Tempo
- Paste trace ID from logs (`trace_id=...`) into TraceQL / trace ID search.

## AI diagnostics agent usage
An AI diagnostics agent can:
1. Trigger SUCCESS/S001.
2. Extract `correlationId` from response.
3. Pull matching Loki logs across services.
4. Extract `trace_id` and open Tempo trace for latency/failure span.
5. Correlate Prometheus spikes (error rate, latency) with request evidence.
