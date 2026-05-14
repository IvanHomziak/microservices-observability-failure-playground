# S003 — DB slow query / database latency

## 1. Scenario ID
S003

## 2. Status
Implemented

## 3. Purpose
Simulate deterministic persistence latency in `orders-service` and validate observability signals for slow database operations.

## 4. Services involved
- `orders-service`

## 5. Preconditions
- Local stack is running.
- Slow-query simulation toggle is enabled with non-zero delay.

## 6. Configuration toggles
- `orders.failures.database.slow-query-enabled=true`
- `orders.failures.database.slow-query-delay-ms` (for example `1500`)

## 7. How to run
```bash
./scripts/trigger-s003-db-slow-query.sh
```
Optional verification:
```bash
./scripts/verify-s003-db-slow-query.sh
```

## 8. Request/event payload
HTTP request to exact endpoint:
- `POST /api/orders` (`http://localhost:8080/api/orders`)

## 9. Expected HTTP response if applicable
- Status: `200 OK`
- Standard order response (for example `orderId`, `status`, `correlationId`, `traceId`), with increased latency.

## 10. Expected logs
`orders-service` logs include:
- `operation=db_query_started`
- `operation=db_query_slow_simulated`
- `operation=db_query_completed`

## 11. Expected metrics
- `orders.database.operation.duration`

## 12. Expected traces
- `orders.db.simulated.query` span for simulated DB work.

## 13. Expected root cause
Intentional DB-operation delay introduced by `orders.failures.database.slow-query-*` properties.

## 14. What the AI diagnostics agent should conclude
Increased request latency is caused by deterministic DB slow-query simulation in `orders-service`, not by downstream payment failures.

## 15. Known limitations
- This is simulated latency, not a real database engine bottleneck.
- Requires observability stack to collect metrics/traces.

## 16. Troubleshooting
- Verify `orders.failures.database.slow-query-enabled` is `true` at runtime.
- Ensure delay is non-zero and large enough to observe.
