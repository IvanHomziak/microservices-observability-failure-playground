# S002 — Payments service returns deterministic HTTP 500

## Status
Implemented

## Purpose
Exercise deterministic downstream 5xx handling for the synchronous request chain so diagnostics tooling can prove `payments-service` is the root cause.

## Services involved
- `api-gateway`
- `orders-service`
- `payments-service`

## Config toggles
`payments-service` uses:
- `failure-simulation.payments.forced-status-code=500`

## How to trigger
```bash
./scripts/trigger-s002-payments-http-500.sh
```

## Expected HTTP response
Gateway returns controlled downstream error:
- HTTP `502 Bad Gateway`
- JSON includes: `code`, `message`, `correlationId`, `timestamp`
- `code` value is `PAYMENT_5XX`

## Expected logs
- `payments-service` logs
  - `operation=payment_failure_mode_triggered`
  - `mode=forced-status-500`
  - `order_id`
  - `correlation_id` (if provided)
  - `trace_id` (if available)
- `orders-service` maps downstream 500 to `PAYMENT_5XX`

## Expected root cause
`payments-service` was configured with forced HTTP 500 and fails authorization deterministically.

## Expected AI diagnostics agent conclusion
The client symptom (`502` with `PAYMENT_5XX`) is caused by a deterministic downstream internal error in `payments-service` (`forced-status-500`), not by transport timeout/connection failures.

## Known limitations
- Requires stack runtime to set `failure-simulation.payments.forced-status-code=500` for `payments-service`.
- `trace_id` field depends on tracing context propagation at runtime.
