# 001 - Payment Timeout Cascade

## Intent
Validate that the AI agent can identify a downstream timeout in `payments-service` as the root cause of `orders-service` failures.

## Trigger
1. Introduce 10s+ artificial latency in payment charge endpoint (future service toggle).
2. Send order requests via `api-gateway` at steady load.

## Expected User Symptom
- Intermittent HTTP 5xx from order placement.
- Higher end-to-end request latency.

## Expected Telemetry
- Elevated `http.server.requests` p95/p99 for `orders-service`.
- Error spans in orders workflow with child span timeout on payments call.
- Logs containing timeout exceptions and shared trace IDs.

## Root Cause
Synchronous dependency timeout from `orders-service` to `payments-service` exceeds client timeout budget.
