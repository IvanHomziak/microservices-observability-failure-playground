# S001 — RestTemplate timeout between orders-service and payments-service

## Scenario ID
S001

## Implemented status
Implemented and verified in Milestone 1.

## Endpoint and request to use
Submit through gateway endpoint:
- `POST /api/orders`
- URL: `http://localhost:8080/api/orders`

Request payload (must include `customerId`):
```json
{
  "customerId": "customer-123",
  "amount": 19.99,
  "currency": "USD"
}
```

Example command:
```bash
curl -i -X POST http://localhost:8080/api/orders \
  -H 'Content-Type: application/json' \
  -H 'X-Correlation-Id: s001-test-001' \
  -d '{"customerId":"customer-123","amount":19.99,"currency":"USD"}'
```

## Exact config values for this scenario
`orders-service/src/main/resources/application.yml`
- `orders.rest-clients.payments.connect-timeout-ms: 500`
- `orders.rest-clients.payments.read-timeout-ms: 1000`
- `orders.failures.payment-timeout: false`

`payments-service/src/main/resources/application.yml`
- `failure-simulation.payments.delay-ms: 5000`

These values force a real downstream timeout (not a simulated exception toggle in `orders-service`).

## Expected API result
- HTTP status: **`504 Gateway Timeout`**
- Error code: **`PAYMENT_TIMEOUT`**
- Expected message: `Timeout while calling payment service`
- Response contains `correlationId`

Representative response body:
```json
{
  "code": "PAYMENT_TIMEOUT",
  "message": "Timeout while calling payment service",
  "correlationId": "s001-...",
  "timestamp": "2026-...Z"
}
```

## Expected root cause
`payments-service` intentionally sleeps for `5000ms`, while `orders-service` HTTP read timeout is `1000ms`, so the downstream call times out and `orders-service` maps it to `PAYMENT_TIMEOUT` and HTTP 504.

## Expected AI diagnostics conclusion
- User symptom: `POST /api/orders` fails with HTTP 504.
- Failing service boundary: `orders-service` calling `payments-service`.
- Primary cause: downstream latency exceeded configured client read timeout.
- Confidence: high, if logs and response share the same `correlationId`.

## Logs to inspect by `correlationId`
Use:
```bash
./scripts/show-logs-by-correlation-id.sh <correlationId>
```

Or direct compose logs:
```bash
docker compose logs api-gateway orders-service payments-service | grep '<correlationId>'
```

Look for:
- gateway request with same `correlationId`
- `orders-service` timeout handling and `PAYMENT_TIMEOUT`
- `payments-service` delayed authorization handling around the same request window
