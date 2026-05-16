#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

RESULTS_FILE="$(mktemp)"
REQUIRED_FAILURE=0

cleanup() {
  rm -f "$RESULTS_FILE"
}
trap cleanup EXIT

run_check() {
  local name="$1"
  local cmd="$2"
  local required="${3:-required}"
  local result="PASS"
  local notes="ok"

  echo "[CHECK] $name"
  if bash -lc "$cmd"; then
    :
  else
    local rc=$?
    if [[ "$required" = "optional" ]]; then
      result="WARNING"
      notes="optional check failed (exit=${rc})"
    else
      result="FAIL"
      notes="exit=${rc}"
      REQUIRED_FAILURE=1
    fi
  fi

  printf '%s|%s|%s\n' "$name" "$result" "$notes" >> "$RESULTS_FILE"
}

add_verifier_if_executable() {
  local label="$1"
  local script_path="$2"
  if [[ -x "$script_path" ]]; then
    run_check "$label" "$script_path"
  else
    echo "[SKIP] $label (missing or not executable: $script_path)"
    printf '%s|%s|%s\n' "$label" "WARNING" "missing or not executable: $script_path" >> "$RESULTS_FILE"
  fi
}

run_check "bash -n scripts/*.sh" "bash -n scripts/*.sh"
run_check "docker compose config" "docker compose config"
run_check "docker compose + s001 override" "docker compose -f docker-compose.yml -f docker-compose.s001.yml config"
run_check "docker compose + s002 override" "docker compose -f docker-compose.yml -f docker-compose.s002.yml config"

for compose_override in docker-compose.s003.yml docker-compose.s004.yml docker-compose.s005.yml docker-compose.s006.yml docker-compose.s007.yml; do
  if [[ -f "$compose_override" ]]; then
    if [[ "$compose_override" == "docker-compose.s004.yml" || "$compose_override" == "docker-compose.s005.yml" ]]; then
      run_check "docker compose + ${compose_override} (kafka profile)" "docker compose -f docker-compose.yml -f ${compose_override} --profile kafka config"
    else
      run_check "docker compose + ${compose_override}" "docker compose -f docker-compose.yml -f ${compose_override} config"
    fi
  fi
done

run_check "docker compose + kafka override/profile" "docker compose -f docker-compose.yml -f docker-compose.kafka.yml --profile kafka config"
run_check "docker compose + notification override/profile" "docker compose -f docker-compose.yml -f docker-compose.notification.yml --profile async config"
run_check "docker compose + audit override/profile" "docker compose -f docker-compose.yml -f docker-compose.audit.yml --profile async config"
run_check "docker compose observability profile" "docker compose --profile observability config"
run_check "docker compose full profile" "docker compose --profile full config"

run_check "verify milestone 1" "./scripts/verify-milestone-1.sh"
run_check "verify s001" "./scripts/verify-s001-resttemplate-timeout.sh"
run_check "verify s002" "./scripts/verify-s002-payments-http-500.sh"
add_verifier_if_executable "verify s003" "./scripts/verify-s003-db-slow-query.sh"
add_verifier_if_executable "verify s004" "./scripts/verify-s004-kafka-poison-message.sh"
add_verifier_if_executable "verify s005" "./scripts/verify-s005-kafka-consumer-lag.sh"
add_verifier_if_executable "verify s006" "./scripts/verify-s006-pubsub-publish-failure.sh"
add_verifier_if_executable "verify s007" "./scripts/verify-s007-broken-trace-propagation.sh"
add_verifier_if_executable "verify s008" "./scripts/verify-s008-missing-correlation-id.sh"
run_check "verify kafka flow" "./scripts/verify-kafka-flow.sh"
run_check "verify notification flow" "./scripts/verify-notification-flow.sh"
run_check "verify audit flow" "./scripts/verify-audit-flow.sh"
run_check "verify observability stack" "./scripts/verify-observability-stack.sh"

echo
echo "Check | Result | Notes"
echo "---|---|---"
while IFS='|' read -r check result notes; do
  echo "$check | $result | $notes"
done < "$RESULTS_FILE"

if [[ "$REQUIRED_FAILURE" -ne 0 ]]; then
  echo "[FAIL] Readiness verification failed."
  exit 1
fi

echo "[PASS] Readiness verification completed."
