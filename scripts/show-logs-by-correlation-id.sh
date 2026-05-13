#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <correlation-id>"
  exit 1
fi

CORRELATION_ID="$1"

echo "[logs] docker compose logs filtered by correlation ID: ${CORRELATION_ID}"
docker compose logs --no-color api-gateway orders-service payments-service inventory-service notification-service audit-service \
  | rg --line-number --fixed-strings "${CORRELATION_ID}" || true

echo "[logs] Grafana Explore: http://localhost:3000/explore"
echo "[logs] Loki query: {service_name=~\"api-gateway|orders-service|payments-service|inventory-service|notification-service|audit-service\"} |= \"${CORRELATION_ID}\""
