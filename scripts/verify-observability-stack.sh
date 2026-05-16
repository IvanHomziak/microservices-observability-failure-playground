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

query_loki_for_correlation() {
  local correlation_id="$1"
  local encoded_query
  encoded_query="%7Bservice%3D~%22api-gateway%7Corders-service%7Cpayments-service%22%7D%20%7C%3D%20%22${correlation_id}%22"

  for _ in {1..20}; do
    local response
    response="$(curl -fsS "http://localhost:3100/loki/api/v1/query_range?query=${encoded_query}&limit=20" || true)"
    if printf '%s' "$response" | grep -q "${correlation_id}"; then
      echo "  OK: Loki query returned log(s) for ${correlation_id}"
      return 0
    fi
    sleep 3
  done

  echo "  FAIL: Loki query did not return log(s) for ${correlation_id}" >&2
  return 1
}

echo "[1/8] Starting Milestone 1 + observability profile"
docker compose --profile observability up -d --build

echo "[2/8] Waiting for core and observability endpoints"
check_url "api-gateway" "http://localhost:8080/actuator/health"
check_url "orders-service" "http://localhost:8081/actuator/health"
check_url "payments-service" "http://localhost:8082/actuator/health"
check_url "Grafana" "http://localhost:3000/api/health"
check_url "Prometheus" "http://localhost:9090/-/healthy"
check_url "Loki" "http://localhost:3100/ready"
check_url "Tempo" "http://localhost:3200/ready"
check_url "OTel Collector" "http://localhost:13133/"

echo "[3/8] Triggering successful request with unique correlation ID"
CORRELATION_ID="observability-$(date +%s)"
curl -fsS -X POST http://localhost:8080/api/orders \
  -H 'Content-Type: application/json' \
  -H "X-Correlation-Id: ${CORRELATION_ID}" \
  -d '{"customerId":"obs-check","amount":17.50,"currency":"USD"}' >/tmp/verify-observability-response.json

echo "[4/8] Verifying log evidence in Docker logs"
LOG_OUTPUT="$(docker compose logs --since=3m api-gateway orders-service payments-service || true)"
if printf '%s' "$LOG_OUTPUT" | grep -q "${CORRELATION_ID}"; then
  echo "  OK: correlation ID found in Docker logs (${CORRELATION_ID})"
else
  echo "  FAIL: correlation ID not found in recent Docker logs (${CORRELATION_ID})" >&2
  exit 1
fi

echo "[5/8] Verifying Loki ingestion by correlation ID"
query_loki_for_correlation "$CORRELATION_ID"

echo "[6/8] Verifying Prometheus status pages"
check_url "Prometheus targets" "http://localhost:9090/api/v1/targets"

echo "[7/8] Tempo trace assertion"
TRACE_ID="$(printf '%s' "$LOG_OUTPUT" | sed -n 's/.*trace_id=\([0-9a-f]\{16,32\}\).*/\1/p' | grep -v '^$' | tail -n1 || true)"
if [[ -n "$TRACE_ID" ]]; then
  TEMPO_RESPONSE="$(curl -fsS "http://localhost:3200/api/traces/${TRACE_ID}" || true)"
  if printf '%s' "$TEMPO_RESPONSE" | grep -qi "$TRACE_ID"; then
    echo "  OK: Tempo contains trace ${TRACE_ID}"
  else
    echo "  WARNING: Tempo lookup did not return extracted trace ${TRACE_ID}; Loki correlation proof remains the required observability evidence."
  fi
else
  echo "  WARNING: Tempo is reachable, but deterministic trace assertion is not implemented because trace ID extraction is not stable."
fi

echo "[8/8] Done"
echo "  Verified (required): endpoint health, request success, Docker log correlation, Loki query ingestion, Prometheus targets reachability."
echo "  Tempo trace lookup is best-effort and may warn without failing readiness."
