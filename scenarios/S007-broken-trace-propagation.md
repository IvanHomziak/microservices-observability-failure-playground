# S007 — Broken trace propagation

## Scenario ID
S007

## Description
Simulates a deterministic observability gap where distributed trace context is intentionally removed between `orders-service` and `payments-service` while the business flow can still succeed.

## Services involved
- `api-gateway`
- `orders-service`
- `payments-service`

## How to enable the scenario
Set this toggle in `orders-service`:

- `orders.failures.tracing-break-propagation-to-payments=true`

When enabled, `orders-service` removes the following outbound headers before calling `payments-service`:

- `traceparent`
- `tracestate`
- `b3`
- `X-B3-TraceId`
- `X-B3-SpanId`
- `X-B3-ParentSpanId`
- `X-B3-Sampled`
- `X-B3-Flags`

## How to trigger it
- Run `./scripts/trigger-s007-broken-trace-propagation.sh`.

## How to verify it
- Run `./scripts/verify-s007-broken-trace-propagation.sh`.

Verification expectations:
- response still contains `correlationId`
- `orders-service` logs include:
  - `operation=trace_propagation_intentionally_broken`
  - `target_service=payments-service`
  - `correlation_id`
  - `trace_id`
- `payments-service` logs inbound `traceparent`; if header is absent it logs `traceparent=missing`

## Expected traces
- Trace continuity is broken on the `orders-service -> payments-service` hop.
- Separate/disconnected traces may appear in Tempo for one business transaction.

## Expected AI conclusion
- issue type: observability gap
- same correlationId across services
- trace continuity broken between orders-service and payments-service
- not necessarily a business failure

## Acceptance criteria
- normal flow preserves trace context
- S007 breaks trace context deterministically
- correlationId still propagates
