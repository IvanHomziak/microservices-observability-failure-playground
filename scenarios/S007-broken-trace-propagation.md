# S007 — Broken trace propagation

## 1. Scenario ID
S007

## 2. Status
Implemented

## 3. Purpose
Create a deterministic observability gap by intentionally dropping outbound trace headers from `orders-service` to `payments-service`.

## 4. Services involved
- `api-gateway`
- `orders-service`
- `payments-service`

## 5. Preconditions
- Local stack is running.
- Trace break toggle is enabled in `orders-service`.

## 6. Configuration toggles
- `orders.failures.tracing-break-propagation-to-payments=true`

## 7. How to run
```bash
./scripts/trigger-s007-broken-trace-propagation.sh
```
Optional verification:
```bash
./scripts/verify-s007-broken-trace-propagation.sh
```

## 8. Request/event payload
HTTP request to exact endpoint:
- `POST /api/orders` (`http://localhost:8080/api/orders`)

## 9. Expected HTTP response if applicable
Business request can still succeed (typically `200 OK`) with `correlationId` present.

## 10. Expected logs
- `orders-service`: `operation=trace_propagation_intentionally_broken target_service=payments-service`
- `payments-service`: inbound trace header missing/changed (for example `traceparent=missing` in validation logs)

## 11. Expected metrics
- No guaranteed scenario-specific metric.

## 12. Expected traces
- Trace continuity is broken at `orders-service -> payments-service` hop (disconnected traces).

## 13. Expected root cause
Intentional trace header removal controlled by `orders.failures.tracing-break-propagation-to-payments`.

## 14. What the AI diagnostics agent should conclude
This is an observability propagation issue: business flow may succeed, but distributed trace linkage is intentionally broken.

## 15. Known limitations
- Requires tracing backend/runtime instrumentation to visualize disconnected spans.
- Correlation ID may still provide cross-service linkage even when trace continuity is broken.

## 16. Troubleshooting
- Verify `orders.failures.tracing-break-propagation-to-payments=true` in effective config.
- Confirm logs are searched with the same `correlationId`.
