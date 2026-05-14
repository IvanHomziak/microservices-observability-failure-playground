# S001 — RestTemplate timeout between orders-service and payments-service

## 1. Scenario ID
S001

## 2. Status
Implemented

## 3. Purpose
Validate timeout handling and error mapping when `orders-service` calls `payments-service` and the downstream response exceeds configured HTTP client timeouts.

## 4. Services involved
- `api-gateway`
- `orders-service`
- `payments-service`

## 5. Preconditions
- Default stack is running for success-path verification.
- For deterministic S001 verification, run with `docker-compose.s001.yml` override so `payments-service` delay is greater than `orders-service` read timeout.

## 6. Configuration toggles
Use these exact properties:
- `orders.rest-clients.payments.connect-timeout-ms=500`
- `orders.rest-clients.payments.read-timeout-ms=1000`
- `orders.failures.payment-timeout=false`
- `failure-simulation.payments.delay-ms=5000`

## 7. How to run
Deterministic verification:
```bash
./scripts/verify-s001-resttemplate-timeout.sh
```

Trigger-only (no deterministic setup by itself):
```bash
./scripts/trigger-s001-resttemplate-timeout.sh
```

## 8. Request/event payload
HTTP request to exact endpoint:
- `POST /api/orders` (`http://localhost:8080/api/orders`)

Payload:
```json
{
  "customerId": "customer-123",
  "amount": 19.99,
  "currency": "USD"
}
```

## 9. Expected HTTP response if applicable
- Status: `504 Gateway Timeout`
- Body includes:
  - `code=PAYMENT_TIMEOUT`
  - `message=Timeout while calling payment service`
  - `correlationId`
  - `timestamp`

## 10. Expected logs
Look for the same `correlationId` across services:
- gateway request log
- `orders-service` payment timeout mapping log
- `payments-service` delayed authorization handling log

Helpful command:
```bash
./scripts/show-logs-by-correlation-id.sh <correlationId>
```

## 11. Expected metrics
- No dedicated scenario-specific metric is guaranteed by this scenario documentation.
- General HTTP latency/error metrics may increase if your runtime collects them.

## 12. Expected traces
- If tracing is enabled in the runtime, the downstream call span from `orders-service` to `payments-service` should show timeout/error.

## 13. Expected root cause
`payments-service` intentionally delays response (`failure-simulation.payments.delay-ms`) beyond `orders-service` read timeout.

## 14. What the AI diagnostics agent should conclude
`POST /api/orders` failed with `PAYMENT_TIMEOUT` because downstream payment authorization exceeded configured client timeout; this is a deterministic latency failure, not a schema or routing issue.

## 15. Known limitations
- `trigger-s001-resttemplate-timeout.sh` only sends the request and does not enforce runtime delay configuration.
- Deterministic behavior depends on using `docker-compose.s001.yml`.
- Trace evidence depends on whether tracing infrastructure is enabled.

## 16. Troubleshooting
- Confirm effective config values in running containers.
- Re-run with a unique `X-Correlation-Id` to isolate logs.
- Ensure `failure-simulation.payments.forced-status-code` is not set to a conflicting mode.
