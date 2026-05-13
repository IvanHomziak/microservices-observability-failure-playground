# Failure Scenarios

This folder tracks deterministic incident playbooks for the microservices observability playground.

## Scenario template requirements

Each scenario document must include:

1. **Objective** - what failure behavior is being simulated.
2. **Deterministic toggle** - exact mechanism to enable/disable failure.
3. **Trigger steps** - commands or requests to execute.
4. **Expected app symptom** - status codes, latency, async delay, etc.
5. **Expected telemetry evidence**
   - logs (required fields and representative events),
   - metrics (which counters/timers/gauges should move),
   - traces (where error spans should appear).
6. **Expected root cause** - canonical explanation.
7. **Validation checks** - concrete evidence confirming diagnosis.
8. **Recovery / rollback** - exact steps to return to healthy state.

## Scenario catalog

- `001-payment-timeout.md` - synchronous downstream timeout propagation and retries.
- `002-inventory-consistency.md` - mismatch between reservation and order state.
- `003-notification-backlog.md` - delayed async notifications under queue pressure.
- `004-kafka-consumer-lag.md` - consumer lag growth and stale event processing.
- `005-pubsub-publish-failure.md` - publish/ack failure for Pub/Sub-like fan-out path.
- `006-resttemplate-connectivity.md` - DNS/refused connection causing hard dependency failure.

## Evidence quality bar

A scenario is considered "ready" only if an external AI diagnostics agent can produce a report containing:

- impacted request scope,
- correlated `trace_id` values,
- implicated service and dependency,
- telemetry-backed root-cause narrative,
- confidence statement with explicit evidence references.

