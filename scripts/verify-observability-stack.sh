#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

check_url() {
  local name="$1" url="$2"
  for _ in {1..40}; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "  OK: $name -> $url"
      return 0
    fi
    sleep 3
  done
  echo "  FAIL: $name -> $url" >&2
  return 1
}

echo "[1/6] Starting Milestone 1 + observability profile"
docker compose --profile observability up -d --build --force-recreate

echo "[2/6] Waiting for core and observability endpoints"
check_url "api-gateway" "http://localhost:8080/actuator/health"
check_url "orders-service" "http://localhost:8081/actuator/health"
check_url "payments-service" "http://localhost:8082/actuator/health"
check_url "Grafana" "http://localhost:3000/api/health"
check_url "Prometheus" "http://localhost:9090/-/healthy"
check_url "Loki" "http://localhost:3100/ready"
check_url "Tempo" "http://localhost:3200/ready"
check_url "OTel Collector" "http://localhost:13133/"

echo "[3/6] Triggering successful request with unique correlation ID"
CORRELATION_ID="obs-$(date +%s)"
curl -fsS -X POST http://localhost:8080/api/orders \
  -H 'Content-Type: application/json' \
  -H "X-Correlation-Id: ${CORRELATION_ID}" \
  -d '{"customerId":"obs-check","amount":17.50,"currency":"USD"}' >/tmp/verify-observability-response.json

echo "[4/6] Verifying fallback log evidence in Docker logs"
if docker compose logs --since=2m api-gateway orders-service payments-service | grep -q "${CORRELATION_ID}"; then
  echo "  OK: correlation ID found in Docker logs (${CORRELATION_ID})"
else
  echo "  FAIL: correlation ID not found in recent Docker logs (${CORRELATION_ID})" >&2
  exit 1
fi

echo "[5/6] Verification scope"
echo "  Verified: observability components are reachable; traffic is generated; Docker log correlation works."
echo "  Not automatically verified: Loki query ingestion proof and Tempo trace lookup assertion."
echo "  Status: Partially implemented observability verification."

echo "[6/6] Done"
