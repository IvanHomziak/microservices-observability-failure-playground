# S003 — DB slow query / database latency

## Status
Implemented

## Required override
- `docker-compose.s003.yml`

## Trigger
- `./scripts/trigger-s003-db-slow-query.sh`

## Verifier
- `./scripts/verify-s003-db-slow-query.sh`

## Deterministic setup
The verifier starts the stack with:

```bash
docker compose -f docker-compose.yml -f docker-compose.s003.yml up -d --build --force-recreate
```

Override values used for this scenario:
- `ORDERS_FAILURES_DATABASE_SLOW_QUERY_ENABLED=true`
- `ORDERS_FAILURES_DATABASE_SLOW_QUERY_DELAY_MS=3000`
- Kafka/notification/audit feature flags remain disabled for deterministic scope.

## Expected HTTP result
- `POST http://localhost:8080/api/orders` returns a `2xx` status.
- Response JSON contains `correlationId`.

## Expected latency evidence
- Trigger script prints elapsed request time in milliseconds.
- Verifier asserts elapsed time is at least `2500 ms`.

## Expected log evidence
- `orders-service` logs include the request correlation ID.
- `orders-service` logs include slow-query evidence (`operation=db_query_slow_simulated`).

## AI diagnostics expected conclusion
"Root cause is induced slow database path in orders-service, not payment-service failure."


## Known limitations
- Deterministic assertion is based on elapsed time threshold and logs, not DB engine internals.
- Slow-query threshold can be sensitive to host load; verifier uses a conservative lower-bound check.
