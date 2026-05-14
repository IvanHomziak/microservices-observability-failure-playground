#!/usr/bin/env bash
set -euo pipefail

CORRELATION_ID="audit-$(date +%s)"

echo "[verify-audit-flow] starting stack"
docker compose up -d --build orders-service api-gateway payments-service audit-service postgres redpanda >/dev/null

echo "[verify-audit-flow] waiting for audit-service"
until curl -fsS http://localhost:8085/actuator/health >/dev/null; do sleep 2; done

echo "[verify-audit-flow] triggering successful order"
RESPONSE=$(curl -sS -X POST http://localhost:8080/api/orders \
  -H 'Content-Type: application/json' \
  -H "X-Correlation-Id: ${CORRELATION_ID}" \
  -d '{"customerId":"audit-check","amount":42.00,"currency":"USD"}')

echo "$RESPONSE"

echo "[verify-audit-flow] checking audit logs"
docker compose logs audit-service --since=2m | rg "operation=audit_event_received" | rg "correlation_id=${CORRELATION_ID}" >/dev/null

echo "[verify-audit-flow] PASS correlation id found in audit logs"
