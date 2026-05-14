# S003 — DB slow query / database latency

## Status
Implemented

## Scenario ID
S003

## Primary service
- `orders-service`

## Description
`orders-service` simulates deterministic database-operation latency during order creation by injecting a controlled delay immediately before persistence operations.

## Config toggles
In `orders-service`:
- `orders.failures.database.slow-query-enabled` (default: `false`)
- `orders.failures.database.slow-query-delay-ms` (default: `0`)

## How to trigger
```bash
./scripts/trigger-s003-db-slow-query.sh
```

## How to verify
```bash
./scripts/verify-s003-db-slow-query.sh
```

## Expected HTTP response contract
- HTTP `200`
- Standard order response body (`orderId`, `status`, `correlationId`, `traceId`)

## Expected evidence
### Logs (`orders-service`)
- `operation=db_query_started`
- `operation=db_query_slow_simulated`
- `operation=db_query_completed`
- fields include `order_id`, `correlation_id`, `duration_ms`

### Metrics
- `orders.database.operation.duration`

### Trace
- span around simulated DB operation:
  - `orders.db.simulated.query`

## Expected root cause
Deterministic database operation latency in `orders-service` caused by enabled slow-query simulation settings.

## Expected AI conclusion
- **primary service:** `orders-service`
- **root cause:** database operation latency
- **evidence:** slow-query simulation logs, elevated request latency, DB simulation span/metric

## Acceptance criteria mapping
- S003 increases latency deterministically: controlled `slow-query-delay-ms` sleep.
- Logs show DB delay evidence: explicit `db_query_*` operation logs with duration.
- Normal flow unaffected when disabled: no delay if toggle is `false`.
