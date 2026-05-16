# S002 — Payments service returns deterministic HTTP 500

## 1. Scenario ID
S002

## 2. Status
Implemented

## 3. Purpose
Exercise deterministic downstream 5xx handling so clients observe a stable upstream error contract.

## 4. Services involved
- `api-gateway`
- `orders-service`
- `payments-service`

## 5. Preconditions
- Local stack is running.
- `payments-service` is configured to force 500.

## 6. Configuration toggles
- `failure-simulation.payments.forced-status-code=500`

## 7. How to run
Deterministic verification:
```bash
./scripts/verify-s002-payments-http-500.sh
```

Trigger-only (no deterministic setup by itself):
```bash
./scripts/trigger-s002-payments-http-500.sh
```

## 8. Request/event payload
HTTP request to exact endpoint:
- `POST /api/orders` (`http://localhost:8080/api/orders`)

## 9. Expected HTTP response if applicable
- Status: `502 Bad Gateway`
- Body includes:
  - `code=PAYMENT_5XX`
  - `message`
  - `correlationId`
  - `timestamp`

## 10. Expected logs
- `payments-service` emits forced failure log (for example `operation=payment_failure_mode_triggered` with forced 500 mode details).
- `orders-service` maps downstream 500 to `PAYMENT_5XX`.

## 11. Expected metrics
- No scenario-specific custom metric is guaranteed here.
- General 5xx/error counters may rise if runtime metrics are enabled.

## 12. Expected traces
- If tracing is enabled, downstream payment span should end in error on forced 500.

## 13. Expected root cause
Configuration-driven forced 500 response in `payments-service`.

## 14. What the AI diagnostics agent should conclude
The symptom (`502` + `PAYMENT_5XX`) is caused by deterministic downstream 500 in `payments-service`, not timeout or connectivity failure.

## 15. Known limitations
- Requires `failure-simulation.payments.forced-status-code=500` in runtime config.
- Trace visibility depends on tracing stack availability.

## 16. Troubleshooting
- Verify active property value inside `payments-service`.
- Confirm no competing toggle (for example artificial delay) is masking expected behavior.
