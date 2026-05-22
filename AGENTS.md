# AGENTS.md

## Repository purpose

This repository is a deterministic microservices failure playground for AI diagnostics workflows.

It is not a generic demo application. Its purpose is to generate controlled, reproducible failure scenarios across Spring Boot microservices so an AI diagnostics agent can evaluate evidence and produce root-cause hypotheses from logs, traces, metrics, and events.

## Core architecture

The default Milestone 1 runtime starts the minimal deterministic stack:

- `postgres`
- `api-gateway`
- `orders-service`
- `payments-service`

Optional runtime profiles extend the playground:

- `kafka` — Redpanda and asynchronous inventory event flow
- `async` — notification and audit services
- `observability` — Grafana, Prometheus, Loki, Tempo, and OpenTelemetry Collector
- `full` — all optional profiles together

## Scenario model

Failure scenarios are deterministic evidence-generation contracts. They are not accidental bugs and must not be removed or simplified casually.

Each implemented scenario must keep the following files and contracts aligned:

- scenario document under `scenarios/`
- trigger script under `scripts/trigger-*.sh`
- verifier script under `scripts/verify-*.sh`
- Docker Compose override, when required
- expected HTTP behavior
- expected logs, traces, metrics, or event evidence
- expected AI diagnostics conclusion
- known limitations

Current scenario families include:

- `S001` — RestTemplate/payment timeout
- `S002` — payments HTTP 500
- `S003` — database slow query
- `S004` — Kafka poison message
- `S005` — Kafka consumer lag
- `S006` — notification/PubSub-style publish failure
- `S007` — broken trace propagation
- `S008` — missing correlation ID

## Agent operating rules

When modifying this repository, agents must follow these rules:

1. Do not treat this as a generic Spring Boot sample.
2. Do not remove deterministic failure toggles unless explicitly requested.
3. Do not simplify failure scenarios by removing evidence needed by diagnostics workflows.
4. Do not change expected HTTP status codes without updating scenario docs and verifier scripts.
5. Do not modify trigger/verifier behavior without updating the corresponding scenario document.
6. Do not make long-running readiness or observability workflows required PR checks unless they are proven deterministic and stable.
7. Do not use `pull_request_target` for untrusted PR validation workflows.
8. Do not use repository, organization, or environment secrets in PR validation workflows.
9. Do not deploy from PR workflows.
10. Do not push Docker images from PR workflows.
11. Do not add auto-merge behavior.
12. Prefer small, reviewable PRs with clear validation evidence.

## CI/CD workflow model

The dedicated workflow split is intentional:

1. `pr-fast-feedback.yml` — fast repository, script, Compose, and workflow safety checks.
2. `java-build-test.yml` — Maven tests per Java service.
3. `compose-contracts.yml` — Docker Compose contract validation.
4. `runtime-smoke.yml` — default runtime smoke verification.
5. `readiness-gate.yml` — manual full deterministic readiness verification.
6. `agentic-cicd-planner.yml` — manual repository context and CI/CD planning artifact.

The first four workflows are appropriate candidates for automatic PR validation.

`readiness-gate.yml` and `agentic-cicd-planner.yml` must remain manual-only unless there is an explicit decision to promote them.

## Validation order

For CI/CD or scenario changes, validate in this order:

1. Shell syntax: `bash -n scripts/*.sh`
2. Base Compose contract: `docker compose config`
3. Scenario Compose overrides
4. Java tests for affected services
5. Runtime smoke: `./scripts/verify-milestone-1.sh`
6. Scenario-specific verifier
7. Full readiness gate: `./scripts/verify-readiness.sh`

## Important files agents should read first

Before making architectural, CI/CD, or scenario changes, read:

- `README.md`
- `docs/ai-diagnostics-contract.md`
- `docs/evidence-pack-schema.md`
- `docs/readiness-checklist.md`
- `docs/observability-model.md`
- `scenarios/README.md`
- affected `scenarios/S*.md` documents
- affected `scripts/trigger-*.sh` and `scripts/verify-*.sh` files
- `docker-compose.yml` and affected `docker-compose*.yml` overrides
- `.github/workflows/*.yml`

## Evidence and diagnostics expectations

Diagnostics conclusions must be evidence-based.

Agents should avoid overclaiming. If telemetry is incomplete, the output must include missing data or uncertainty rather than inventing a root cause.

Expected diagnostic reasoning should:

- correlate by `correlationId` first
- use `traceId` to confirm distributed path continuity when available
- distinguish symptoms from root causes
- reference concrete logs, spans, metrics, or events
- classify confidence as low, medium, or high
- recommend concrete and testable remediation steps

## Production-safety boundary

This repository is a local deterministic playground. CI/CD workflows may build, test, validate Compose contracts, and run local Docker-based verification.

They must not perform production deployment, cloud infrastructure mutation, package publication, or image publishing unless a separate protected release workflow is intentionally designed and reviewed.
