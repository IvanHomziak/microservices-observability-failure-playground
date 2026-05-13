# S005 — Kafka consumer lag growth

## Scenario ID
S005

## Description
Simulates throughput imbalance where event production outpaces consumer processing, causing sustained lag.

## Services involved
- Kafka broker
- Producing service(s)
- Consuming service(s): `inventory-service`, `audit-service`, etc.

## How to enable the scenario
Placeholder:
- Introduce controlled consumer slowdown (sleep/backpressure toggle) or burst producer load script.

## How to trigger it
- Generate event burst while slowdown is active.

## Expected logs
- Consumer processing delay indicators.
- Periodic lag monitoring output (if enabled).

## Expected traces
- Longer end-to-end async latency from produce to consume spans.

## Expected metrics
- Increasing Kafka consumer lag gauge.
- Reduced consumer throughput versus producer throughput.

## Expected root cause
Consumer capacity/latency bottleneck relative to ingest rate.

## What the AI diagnostics agent should conclude
Incident is backlog/lag driven, not message-level corruption.

## Known limitations
- Deterministic lag generator may require additional scripts and topic instrumentation.
