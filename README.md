# microservices-observability-failure-playground

Deterministic microservices failure playground for AI diagnostics workflows.

## Default runtime contract (Milestone 1)
Default startup is intentionally minimal and deterministic:

```bash
docker compose up -d --build
```

Started services:
- `postgres`
- `api-gateway` (`:8080`)
- `orders-service` (`:8081`)
- `payments-service` (`:8082`)

Optional integrations (Kafka, notification, audit, observability) are **opt-in** via compose overrides/profiles and verifier scripts.

## run-local.sh behavior
Use:

```bash
./scripts/run-local.sh
```

It starts the Docker Milestone 1 stack only (no Maven manual startup instructions).

## Final readiness command
Use this command for the readiness matrix:

```bash
./scripts/verify-readiness.sh
```

It runs static checks, compose contract checks, and runtime verifier scripts, then prints a PASS/FAIL/WARNING summary table.

## Implemented deterministic verifiers (current readiness gate, target >=95% scoped readiness)
```bash
./scripts/verify-milestone-1.sh
./scripts/verify-s001-resttemplate-timeout.sh
./scripts/verify-s002-payments-http-500.sh
./scripts/verify-s003-db-slow-query.sh
./scripts/verify-s004-kafka-poison-message.sh
./scripts/verify-s005-kafka-consumer-lag.sh
./scripts/verify-s006-pubsub-publish-failure.sh
./scripts/verify-s007-broken-trace-propagation.sh
./scripts/verify-s008-missing-correlation-id.sh
./scripts/verify-kafka-flow.sh
./scripts/verify-notification-flow.sh
./scripts/verify-audit-flow.sh
./scripts/verify-observability-stack.sh
```

`verify-observability-stack.sh` is included with **partial** observability verification only.

S003–S008 are now included in the readiness gate only when their verifier scripts are present and executable.

## Optional profiles and purpose
- `kafka`: Redpanda + inventory async event flow runtime.
- `async`: notification/audit services runtime.
- `observability`: Grafana, Prometheus, Loki, Tempo, OTel Collector runtime.
- `full`: all optional profiles together.

> Warning: manual profile startup is runtime-only smoke startup. Deterministic scenario verification should use the `verify-*` scripts.

## CI checks
CI validates:
- Maven tests per service
- shell syntax for `scripts/*.sh`
- compose contracts:
  - base `docker compose config`
  - `s001`, `s002`, `kafka`, `notification`, `audit` override combinations
  - `observability` and `full` profile configs

## Observability status
Current status: **Partially implemented** (Loki proof required; Tempo assertion may warn if deterministic trace extraction is unavailable).
- Verified: observability components reachable; request triggerability; Docker log correlation evidence.
- Not automatically asserted in all runs: deterministic Tempo trace lookup assertion (can warn when trace extraction is unstable).

## Documentation links
- Readiness checklist: [docs/readiness-checklist.md](docs/readiness-checklist.md)
- Scenario index and status: [scenarios/README.md](scenarios/README.md)
- AI diagnostics contract: [docs/ai-diagnostics-contract.md](docs/ai-diagnostics-contract.md)
- Evidence pack schema: [docs/evidence-pack-schema.md](docs/evidence-pack-schema.md)
- Observability model details: [docs/observability-model.md](docs/observability-model.md)
