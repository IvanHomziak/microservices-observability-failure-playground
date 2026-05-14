#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/6] Starting stack"
docker compose up -d --build

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
  echo "  FAIL: $name -> $url"
  return 1
}

check_url "Grafana" "http://localhost:3000/api/health"
check_url "Prometheus" "http://localhost:9090/-/healthy"
check_url "Loki" "http://localhost:3100/ready"
check_url "Tempo" "http://localhost:3200/ready"
check_url "OTel Collector" "http://localhost:13133/"

echo "[3/6] Triggering SUCCESS"
./scripts/trigger-successful-order.sh || true

echo "[4/6] Triggering S001"
./scripts/trigger-s001-resttemplate-timeout.sh || true

echo "[5/6] Query hints"
echo "  Logs by correlationId: ./scripts/show-logs-by-correlation-id.sh <correlation-id>"
echo "  Traces by traceId in Grafana Tempo: Explore -> Tempo datasource -> query by trace ID"

echo "[6/6] Done"
