# S003 — Database slow query

## Scenario ID
S003

## Description
Simulates degraded latency caused by slow SQL query execution in an order or inventory persistence path.

## Services involved
- `orders-service` and/or `inventory-service`
- PostgreSQL backing store

## How to enable the scenario
Placeholder:
- Introduce a toggle that adds artificial DB delay (e.g., `pg_sleep`) or an intentionally non-indexed query path.

## How to trigger it
- Issue repeated read/write API calls that hit the affected query.

## Expected logs
- Slow query logs or explicit latency warning statements.
- Request processing duration noticeably above baseline.

## Expected traces
- Long DB client span(s) under affected service request traces.

## Expected metrics
- Increased DB query latency histogram percentiles (p95/p99).
- Increased API latency and potential timeout/error rates.

## Expected root cause
Inefficient/blocked database operation causing cascading request latency.

## What the AI diagnostics agent should conclude
Primary bottleneck is in database interaction (query duration), not upstream network failure.

## Known limitations
- No fully wired deterministic slow-query injector in this iteration.
