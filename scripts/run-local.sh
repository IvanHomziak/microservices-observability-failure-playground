#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[run-local] Starting shared infrastructure with docker compose..."
docker compose up -d

echo "[run-local] Infrastructure started."
echo "[run-local] Start services in separate terminals:"
echo "  cd api-gateway && mvn spring-boot:run"
echo "  cd orders-service && mvn spring-boot:run"
echo "  cd payments-service && mvn spring-boot:run"
echo "  cd inventory-service && mvn spring-boot:run"
echo "  cd notification-service && mvn spring-boot:run"
echo "  cd audit-service && mvn spring-boot:run"

echo "[run-local] Optional health check: curl -sS http://localhost:8080/actuator/health"
