# S008 — Missing correlation ID

## 1. Scenario ID
S008

## 2. Status
Implemented

## 3. Purpose
Validate that `api-gateway` generates and propagates a correlation ID when client omits `X-Correlation-Id`.

## 4. Services involved
- `api-gateway`
- `orders-service`
- `payments-service`

## 5. Preconditions
- Local stack is running.
- Request is sent without `X-Correlation-Id` header.

## 6. Configuration toggles
No special failure toggle required.

## 7. How to run
```bash
./scripts/trigger-s008-missing-correlation-id.sh
```
Optional verification:
```bash
./scripts/verify-s008-missing-correlation-id.sh
```

## 8. Request/event payload
HTTP request to exact endpoint:
- `POST /api/orders` (`http://localhost:8080/api/orders`)

Must omit header:
- `X-Correlation-Id`

## 9. Expected HTTP response if applicable
- Success response (typically `200 OK`) or scenario-specific business result.
- Response contains generated correlation identifier via header and/or body `correlationId`.

## 10. Expected logs
- `api-gateway`: `operation=correlation_id_generated correlation_id=<generated-id>`
- `orders-service`: same `correlation_id`
- `payments-service`: same `correlation_id`

## 11. Expected metrics
- No incident-level metric degradation expected for successful propagation.

## 12. Expected traces
- Trace continuity should remain connected if tracing is enabled.

## 13. Expected root cause
If validation fails, cause is missing correlation propagation on one or more service hops.

## 14. What the AI diagnostics agent should conclude
If IDs are consistent across services, this is not an incident; gateway correctly generated and propagated correlation context.

## 15. Known limitations
- Response format can vary by failure mode of the same request; correlation behavior should remain verifiable.
- Trace evidence depends on tracing setup.

## 16. Troubleshooting
- Ensure request truly omits `X-Correlation-Id`.
- Compare gateway/orders/payments logs using generated ID.
