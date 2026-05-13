# S007 — Broken trace propagation

## Scenario ID
S007

## Description
Simulates missing/incorrect trace context propagation across service boundaries, resulting in fragmented traces.

## Services involved
- `api-gateway`
- `orders-service`
- downstream services (`payments-service`, `inventory-service`, etc.)

## How to enable the scenario
Placeholder:
- Add a toggle that strips or overwrites tracing headers on outbound call path.

## How to trigger it
- Execute normal order flow while propagation break toggle is enabled.

## Expected logs
- Requests still process, but log correlation by trace ID becomes inconsistent across services.

## Expected traces
- Multiple disconnected traces for what should be one transaction.

## Expected metrics
- Standard success/error metrics may remain normal; observability quality degrades.

## Expected root cause
Trace context headers not forwarded or replaced incorrectly.

## What the AI diagnostics agent should conclude
Primary issue is telemetry instrumentation/propagation, not business logic failure.

## Known limitations
- Deterministic propagation-break switch not fully wired in first iteration.
