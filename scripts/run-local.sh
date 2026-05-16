#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[run-local] Starting Milestone 1 Docker stack..."
docker compose up -d --build

echo
printf '%-18s %s\n' "api-gateway" "http://localhost:8080"
printf '%-18s %s\n' "orders-service" "http://localhost:8081"
printf '%-18s %s\n' "payments-service" "http://localhost:8082"
printf '%-18s %s\n' "postgres" "localhost:5432"

echo
echo "[run-local] Verify stack: ./scripts/verify-milestone-1.sh"
echo "[run-local] Tail logs:   docker compose logs -f api-gateway orders-service payments-service"
