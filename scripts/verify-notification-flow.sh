#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

cleanup_orders_runtime() {
  local cleanup_rc=0
  echo "[INFO] Restoring default orders-service runtime"
  if docker compose up -d --build --force-recreate orders-service; then
    return 0
  fi
  cleanup_rc=$?
  echo "[WARN] Failed to restore default orders-service runtime (exit=${cleanup_rc})." >&2
}

trap cleanup_orders_runtime EXIT

wait_for_health() {
  local name="$1" url="$2"
  for _ in {1..60}; do
    local body
    body="$(curl -sS "$url" || true)"
    if printf '%s' "$body" | grep -Eq '"status"\s*:\s*"UP"'; then
      echo "[OK] ${name} is healthy"
      return 0
    fi
    sleep 3
  done

  echo "[FAIL] ${name} did not become healthy at ${url}" >&2
  docker compose logs --tail=120 api-gateway orders-service payments-service notification-service >&2 || true
  exit 1
}

echo "[verify-notification-flow] starting deterministic notification runtime"
docker compose -f docker-compose.yml -f docker-compose.notification.yml --profile async up -d --build --force-recreate

wait_for_health "api-gateway" "http://localhost:8080/actuator/health"
wait_for_health "orders-service" "http://localhost:8081/actuator/health"
wait_for_health "payments-service" "http://localhost:8082/actuator/health"
wait_for_health "notification-service" "http://localhost:8084/actuator/health"

./scripts/trigger-notification-success-flow.sh >/tmp/notification-flow-trigger.txt
correlation_id=$(grep -Eo 'correlation_id=[^[:space:]]+' /tmp/notification-flow-trigger.txt | head -n1 | sed 's/correlation_id=//')

if [[ -z "${correlation_id}" ]]; then
  echo "[FAIL] could not extract correlation_id from trigger output" >&2
  cat /tmp/notification-flow-trigger.txt >&2
  exit 1
fi

sleep 3

docker compose logs orders-service --since=2m | grep -E 'operation=notification_publish_succeeded' | grep -E "${correlation_id}" >/dev/null
docker compose logs notification-service --since=2m | grep -E 'operation=notification_event_received' | grep -E "${correlation_id}" >/dev/null
docker compose logs notification-service --since=2m | grep -E 'operation=notification_sent' | grep -E "${correlation_id}" >/dev/null

echo "[PASS] Notification flow verified for correlation_id=${correlation_id}"
echo "[INFO] Logs command: docker compose logs -f orders-service notification-service"
