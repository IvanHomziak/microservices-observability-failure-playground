# S008 — Missing correlation ID

## Scenario ID
S008

## Description
Simulates requests/events where `correlationId` is absent, preventing reliable log stitching.

## Services involved
- `api-gateway`
- `orders-service`
- all downstream services participating in logging

## How to enable the scenario
Placeholder:
- Send requests without `X-Correlation-Id` header and/or disable correlation ID generation middleware.

## How to trigger it
- Call `POST /orders` without correlation header.

## Expected logs
- `correlationId` field empty/default in log pattern.
- Trace IDs may still exist if tracing is intact.

## Expected traces
- Distributed traces may remain connected, but log-to-trace correlation is weaker.

## Expected metrics
- Business metrics mostly unchanged; observability quality KPI should degrade.

## Expected root cause
Correlation identifier injection/propagation missing at ingress or between hops.

## What the AI diagnostics agent should conclude
Incident concerns observability metadata hygiene rather than core runtime failure.

## Known limitations
- Some frameworks may auto-generate correlation-like values, reducing reproducibility without explicit toggles.
