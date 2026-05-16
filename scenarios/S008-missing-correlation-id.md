# S008 — Missing correlation ID

## 1. Scenario ID
S008

## 2. Status
Implemented

## 3. Purpose
Validate deterministic behavior when `POST /api/orders` is sent without `X-Correlation-Id`: `api-gateway` must generate a correlation ID and propagate it through the core synchronous flow.

## 4. Services involved
- `api-gateway`
- `orders-service`
- `payments-service`

## 5. Preconditions
- Docker is available.
- Default Milestone 1 stack can be started via `docker compose up -d --build --force-recreate`.
- Client request intentionally omits `X-Correlation-Id`.

## 6. Configuration toggles
- No special failure toggle required.
- No compose override required.

## 7. How to run
Trigger only:
```bash
./scripts/trigger-s008-missing-correlation-id.sh
```

Deterministic end-to-end verification:
```bash
./scripts/verify-s008-missing-correlation-id.sh
```

## 8. Request/event payload
HTTP request to exact endpoint:
- `POST /api/orders` (`http://localhost:8080/api/orders`)

Must omit header:
- `X-Correlation-Id`

## 9. Expected HTTP response if applicable
- Expected HTTP status: `2xx`.
- Response should expose generated correlation ID in either:
  - header `X-Correlation-Id`, or
  - response body field `correlationId`.

## 10. Expected logs
Verifier asserts the same extracted correlation ID exists in:
- `api-gateway` logs
- `orders-service` logs
- `payments-service` logs

Useful live log command:
```bash
docker compose logs -f api-gateway orders-service payments-service
```

## 11. Expected metrics
- No failure mode or degradation is expected for this scenario.

## 12. Expected traces
- Trace/correlation continuity should remain intact across gateway → orders → payments path.

## 13. Expected root cause
N/A for passing scenario. If verification fails, likely causes are:
- gateway not generating missing correlation IDs, or
- propagation break on one of the service hops.

## 14. What the AI diagnostics agent should conclude
Gateway generated missing correlation ID and propagated it across core synchronous flow.

## 15. Known limitations
- If a service log format changes, string matching for correlation evidence may need updates.

## 16. Troubleshooting
- Confirm the request does not include `X-Correlation-Id`.
- Re-run verifier and inspect service logs with:
  - `docker compose logs -f api-gateway orders-service payments-service`
