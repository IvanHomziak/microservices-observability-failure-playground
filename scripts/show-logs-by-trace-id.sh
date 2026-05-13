#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <trace-id>"
  exit 1
fi

TRACE_ID="$1"

echo "[logs] docker compose logs filtered by trace ID: ${TRACE_ID}"
docker compose logs --no-color api-gateway orders-service payments-service inventory-service notification-service audit-service \
  | rg --line-number --fixed-strings "${TRACE_ID}" || true

echo "[logs] Grafana Explore: http://localhost:3000/explore"
echo "[logs] Loki query: {service_name=~\"api-gateway|orders-service|payments-service|inventory-service|notification-service|audit-service\"} |= \"${TRACE_ID}\""
echo "[traces] Tempo: search exact trace ID ${TRACE_ID}"
