# S002 — Payments service returns HTTP 500

## Scenario ID
S002

## Description
Documents a deterministic payment-provider 5xx failure mode where order placement fails due to `payments-service` internal error.

## Services involved
- `api-gateway`
- `orders-service`
- `payments-service`

## How to enable the scenario
Placeholder (first iteration):
- Option A: add a payments failure toggle in `payments-service` to force `POST /payments/authorize` => HTTP 500.
- Option B: use existing simulation hooks if present and mapped to 5xx behavior.

## How to trigger it
- Submit `POST /orders` with a normal payload through `api-gateway`.

## Expected logs
- `payments-service` internal error log for authorization path.
- `orders-service` maps downstream 5xx to `PAYMENT_5XX`.

## Expected traces
- Client span `orders-service -> payments-service` with error status.
- Server span in `payments-service` marked error (500).

## Expected metrics
- `payments-service` HTTP 500 counter increases.
- `orders-service` failed order counter / 5xx response count increases.

## Expected root cause
`payments-service` forced internal error causes authorization failure propagated back to `orders-service`.

## What the AI diagnostics agent should conclude
Downstream dependency failure in `payments-service` (HTTP 500) is the proximate cause of failed order creation.

## Known limitations
- Full deterministic toggle and runbook wiring may still be incomplete.
