# S008 — Missing correlation ID

## Scenario ID
S008

## Description
Client sends `POST /api/orders` without `X-Correlation-Id`.
The `api-gateway` must generate a correlation ID, return it in the response header, and propagate it downstream.

## Services involved
- `api-gateway`
- `orders-service`
- `payments-service`
- Kafka and notification flow (when enabled)

## How to enable the scenario
No failure toggle is required.
Use a request that omits the `X-Correlation-Id` header.

## How to trigger it
```bash
./scripts/trigger-s008-missing-correlation-id.sh
```

## How to verify it
```bash
./scripts/verify-s008-missing-correlation-id.sh
```

Verification checks:
- request is sent **without** `X-Correlation-Id`
- response includes generated `X-Correlation-Id` header (or `correlationId` in body)
- same correlation ID can be searched in gateway/orders/payments logs

## Expected logs
- `api-gateway`: `operation=correlation_id_generated correlation_id=<generated-id>`
- `orders-service`: request and business logs include the same `correlation_id`
- `payments-service`: authorization logs include the same `correlation_id`
- when Kafka/notification is enabled, emitted events carry the same correlation ID in payload/headers

## Expected traces
Tracing should remain connected. This scenario specifically validates correlation-ID generation and propagation.

## Expected metrics
No incident-level degradation expected when propagation is correct.

## Expected root cause (if failing)
Missing propagation between service hops or event publication path.

## What the AI diagnostics agent should conclude
- If propagated correctly: **no incident**, gateway generated a correlation ID and observability context remained intact.
- If missing downstream: **observability propagation gap**, correlation metadata was not forwarded through all hops.
