# S001 — RestTemplate timeout between orders-service and payments-service

## Scenario ID
S001

## Description
Implements a real synchronous downstream timeout on the `orders-service -> payments-service` payment authorization path. `orders-service` calls `payments-service` via `RestTemplate`, while `payments-service` intentionally delays its response long enough to exceed the configured client read timeout.

## Services involved
- `api-gateway`
- `orders-service`
- `payments-service`

## How to enable the scenario
1. Ensure `orders-service/src/main/resources/application.yml` contains:
   - `orders.rest-clients.payments.connect-timeout-ms: 500`
   - `orders.rest-clients.payments.read-timeout-ms: 1000`
2. Ensure `payments-service/src/main/resources/application.yml` contains:
   - `failure-simulation.payments.delay-ms: 5000`
3. Keep `orders.failures.payment-timeout: false` so the real HTTP call is executed.
4. Restart both services.

## How to trigger it
1. Submit an order through gateway:
   ```bash
   curl -i -X POST http://localhost:8080/api/orders \
     -H 'Content-Type: application/json' \
     -H 'X-Correlation-Id: s001-test-001' \
     -d '{"customerId":"customer-123","amount":19.99,"currency":"USD"}'
   ```
2. Observe a `504 Gateway Timeout` response with `PAYMENT_TIMEOUT`, a useful message, and `correlationId` in the response body.

## Expected logs
- `orders-service` shows timeout handling with:
  - `PAYMENT_TIMEOUT`
  - `Timeout while calling payment service`
  - `event=payments_authorization_timeout`
- Logs contain populated tracing and correlation fields from pattern:
  - `traceId`
  - `spanId`
  - `correlationId`
- `payments-service` shows delayed authorization handling (`mode=fixed-delay delayMs=5000`).

## Expected traces
- Root span in `api-gateway` and downstream span for `orders-service` request.
- A slow/failed client span from `orders-service` to `payments-service` due to read timeout.
- `orders-service` request span marked as error from `PAYMENT_TIMEOUT`.

## Expected metrics
- Increased HTTP 5xx count on `orders-service` order endpoint.
- Increased request latency around the configured timeout window on failed requests.
- Payments-side request latency increases due to configured sleep.

## Expected root cause
`payments-service` response latency (`delay-ms=5000`) exceeds `orders-service` RestTemplate read timeout (`read-timeout-ms=1000`), producing `ResourceAccessException` and a `PaymentGatewayException` with code `PAYMENT_TIMEOUT`.

## What the AI diagnostics agent should conclude
- Primary failing service: `orders-service`
- Downstream dependency: `payments-service`
- Root cause: payments latency exceeded RestTemplate read timeout
- Confidence: high
- Evidence: timeout log (`event=payments_authorization_timeout`), slow/failed client span, HTTP client timeout exception, latency/error metric spikes.

## Known limitations
- Timeout depends on local runtime and scheduler precision; observed failure timing may vary slightly around the configured read timeout.


## TODO (first pass gaps)

- [ ] Attach a sample `docker compose logs` snippet that includes the same `correlationId` across `api-gateway`, `orders-service`, and `payments-service`.
- [ ] Attach a sample trace screenshot (Tempo) showing the failing `orders-service -> payments-service` client span timing out.
- [ ] Add a deterministic automated scenario check (script or test) that asserts the expected 504 response contract and timeout error code.
