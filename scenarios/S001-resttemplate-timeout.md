# S001 — RestTemplate timeout between orders-service and payments-service

## Scenario ID
S001

## Description
Simulates a synchronous downstream timeout on the `orders-service -> payments-service` payment authorization path. In this first iteration, the timeout is deterministic and injected in `orders-service` via a failure toggle, causing order placement to fail with a payment-timeout error.

## Services involved
- `api-gateway`
- `orders-service`
- `payments-service` (logical dependency; call is short-circuited when simulation is on)

## How to enable the scenario
1. In `orders-service/src/main/resources/application.yml`, set:
   - `orders.failures.payment-timeout: true`
2. Restart `orders-service`.

## How to trigger it
1. Submit an order through gateway:
   ```bash
   curl -i -X POST http://localhost:8080/orders \
     -H 'Content-Type: application/json' \
     -H 'X-Correlation-Id: s001-test-001' \
     -d '{"sku":"SKU-123","quantity":1,"amount":19.99,"currency":"USD"}'
   ```
2. Observe a 5xx failure response with payment-timeout semantics.

## Expected logs
- `orders-service` shows error handling path with one of:
  - `PAYMENT_TIMEOUT`
  - `Simulated payment timeout`
- Logs contain populated tracing and correlation fields from pattern:
  - `traceId`
  - `spanId`
  - `correlationId`
- `payments-service` may show no matching authorization request for this trace because failure is injected before outbound call.

## Expected traces
- Root span in `api-gateway` and downstream span for `orders-service` request.
- Error status on `orders-service` span associated with payment authorization step.
- No successful child client span to `payments-service` in the simulated mode.

## Expected metrics
- Increased HTTP 5xx count on `orders-service` order endpoint.
- Increased request latency for failed order attempts (typically modest in simulation mode).
- No matching success increment on payment authorization outcomes.

## Expected root cause
`orders-service` failure simulation toggle `orders.failures.payment-timeout=true` intentionally forces `PaymentClient` to throw `PaymentGatewayException` with code `PAYMENT_TIMEOUT`.

## What the AI diagnostics agent should conclude
- Impacted flow: `POST /orders` via gateway.
- Failing component: `orders-service` payment dependency layer (`PaymentClient`).
- Evidence: error code `PAYMENT_TIMEOUT`, failed spans in `orders-service`, correlation via trace/correlation IDs.
- Root cause classification: **intentional fault injection / timeout simulation**, not an organic infrastructure outage.

## Known limitations
- Current implementation simulates timeout immediately rather than waiting for actual network/socket timeout.
- `payments-service` is not necessarily contacted in this mode; absence of payment logs is expected.
- To model real timeout behavior (connect/read), dedicated HTTP client timeout configuration and a delayed payments endpoint should be added in a future iteration.
