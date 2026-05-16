# S007 — Broken trace propagation

## 1. Scenario ID
S007

## 2. Status
Implemented

## 3. Purpose
Validate a deterministic observability failure where order creation succeeds, but distributed trace propagation is intentionally broken on the `orders-service -> payments-service` hop.

## 4. Services involved
- `api-gateway`
- `orders-service`
- `payments-service`

## 5. Preconditions
- Scenario stack started with:
  - `docker compose -f docker-compose.yml -f docker-compose.s007.yml up -d --build --force-recreate`
- `orders-service` has propagation-break toggle enabled.

## 6. Configuration toggles
- `ORDERS_FAILURES_TRACING_BREAK_PROPAGATION_TO_PAYMENTS=true`
- Equivalent app property: `orders.failures.tracing-break-propagation-to-payments=true`

## 7. How to run
```bash
./scripts/trigger-s007-broken-trace-propagation.sh
```
Deterministic verification:
```bash
./scripts/verify-s007-broken-trace-propagation.sh
```

## 8. Request/event payload
HTTP request to:
- `POST /api/orders` (`http://localhost:8080/api/orders`)

Payload:
```json
{"customerId":"customer-123","amount":19.99,"currency":"USD"}
```

## 9. Definition of broken propagation in this codebase
Broken propagation means **orders-service intentionally removes outbound `traceparent` before calling payments-service**, creating a trace continuity gap even when business processing succeeds.

Strong evidence hierarchy used by verifier:
1. `orders-service` log marker: `operation=trace_propagation_intentionally_broken target_service=payments-service`.
2. `payments-service` inbound log marker: `operation=payment_authorize_received ... traceparent=missing`.
3. Optional fallback evidence: payment log path lacks the same correlation ID, indicating header/context propagation was broken.

## 10. Expected HTTP response
- Business request should succeed (`2xx`, typically `201`).
- Response body should include `correlationId`.

## 11. Expected observability/log result
- `orders-service` contains the request correlation ID.
- `orders-service` records explicit intentional break marker.
- `payments-service` must show at least one of:
  - missing `traceparent` (`traceparent=missing`), or
  - absence/mismatch of propagated correlation evidence.

Expected AI diagnostics conclusion:
> Business flow succeeds, but observability evidence shows broken downstream trace/correlation propagation.

## 12. Expected metrics
- No scenario-specific metric guarantees.

## 13. Expected traces
- Trace continuity across `orders-service -> payments-service` is intentionally broken.
- Do not treat this scenario as requiring Tempo UI proof.

## 14. Expected root cause
Intentional behavior toggled by:
- `orders.failures.tracing-break-propagation-to-payments=true`

## 15. Known limitations
- Without dedicated trace backend assertions, deterministic verification relies on service logs.
- Correlation ID may still be present on some requests even when `traceparent` is dropped; this does not invalidate the scenario.
- Log format/order can vary slightly by runtime timing; verifier avoids brittle timestamp/ordering checks.

## 16. Troubleshooting
- Confirm override file sets `ORDERS_FAILURES_TRACING_BREAK_PROPAGATION_TO_PAYMENTS=true`.
- Re-run verifier and inspect live logs:
  - `docker compose logs -f api-gateway orders-service payments-service`
- Ensure unique `s007-` correlation IDs are used per trigger run.
