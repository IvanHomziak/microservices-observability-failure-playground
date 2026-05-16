#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/6] Starting Milestone 1 + observability profile"
docker compose --profile observability up -d --build

echo "[2/6] Waiting for endpoints"
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

check_url "api-gateway" "http://localhost:8080/actuator/health"
check_url "orders-service" "http://localhost:8081/actuator/health"
check_url "payments-service" "http://localhost:8082/actuator/health"
check_url "Grafana" "http://localhost:3000/api/health"
check_url "Prometheus" "http://localhost:9090/-/healthy"
check_url "Loki" "http://localhost:3100/ready"
check_url "Tempo" "http://localhost:3200/ready"
check_url "OTel Collector" "http://localhost:13133/"

echo "[3/6] Triggering SUCCESS"
./scripts/trigger-successful-order.sh

echo "[4/6] Triggering S001"
./scripts/trigger-s001-resttemplate-timeout.sh

echo "[5/6] Verification scope and limitations"
echo "  Verified: service/observability components started and health endpoints responded."
echo "  Note: this script does NOT assert Loki contains application logs."
echo "  Promtail is started, but container log shipping may require Docker socket or container log volume mounts."
echo "  Fallback for deterministic troubleshooting: docker compose logs api-gateway orders-service payments-service"

echo "[6/6] Done"
