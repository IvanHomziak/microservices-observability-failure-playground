# EvidencePack Schema

This document defines the canonical **EvidencePack** contract that scenario runners (or data collection pipelines) should produce for a diagnostics agent.

## Purpose
An EvidencePack is the minimum reproducible bundle of observability facts for a single incident window. It is intentionally scenario-focused and correlation-centric.

## JSON schema (contract shape)

```json
{
  "scenarioId": "...",
  "correlationId": "...",
  "traceId": "...",
  "timeWindow": {
    "from": "...",
    "to": "..."
  },
  "involvedServices": [],
  "logs": [],
  "spans": [],
  "metrics": [],
  "events": [],
  "knownExpectedRootCause": "for evaluation only"
}
```

## Field semantics
- `scenarioId` (string): must match scenario docs naming, for example `S001`.
- `correlationId` (string): primary key for cross-service log pivots.
- `traceId` (string): distributed trace lookup key; may be empty when propagation is intentionally broken.
- `timeWindow.from` / `timeWindow.to` (ISO-8601 UTC): evidence inclusion boundaries.
- `involvedServices` (string[]): service names present in the incident.
- `logs` (object[]): structured log entries relevant to this incident.
- `spans` (object[]): flattened trace span summaries used by agent reasoning.
- `metrics` (object[]): time-series samples or window aggregates.
- `events` (object[]): domain/integration events (Kafka, Pub/Sub-like, DLQ, retries).
- `knownExpectedRootCause` (string): **evaluation-only label** for grading; agents must not assume this exists in production.

## Recommended inner object shapes

### `logs[]`
```json
{
  "id": "log-1",
  "timestamp": "2026-05-14T10:21:33.220Z",
  "service": "orders-service",
  "level": "ERROR",
  "message": "payment call timed out",
  "fields": {
    "correlationId": "s001-demo-01",
    "traceId": "7a13...",
    "exception": "ResourceAccessException"
  }
}
```

### `spans[]`
```json
{
  "id": "span-1",
  "traceId": "7a13...",
  "spanId": "0af1...",
  "parentSpanId": "",
  "service": "orders-service",
  "operation": "POST /orders",
  "status": "ERROR",
  "durationMs": 3050,
  "attributes": {
    "http.status_code": 504
  }
}
```

### `metrics[]`
```json
{
  "id": "metric-1",
  "name": "http_server_requests_seconds_p95",
  "service": "orders-service",
  "timestamp": "2026-05-14T10:21:35Z",
  "value": 3.08,
  "unit": "seconds",
  "labels": {
    "uri": "/api/orders",
    "status": "504"
  }
}
```

### `events[]`
```json
{
  "id": "event-1",
  "timestamp": "2026-05-14T10:21:34.000Z",
  "type": "kafka.dlq.publish",
  "sourceService": "inventory-service",
  "payloadSummary": "order-created message moved to order-created-dlq",
  "fields": {
    "topic": "order-created-dlq",
    "correlationId": "s004-demo-01"
  }
}
```

## Security and data handling
- Never include secrets, credentials, private keys, tokens, or PII.
- Redact payload fields not required for diagnosis.
- Keep raw values truthful; do not synthesize impossible telemetry.
