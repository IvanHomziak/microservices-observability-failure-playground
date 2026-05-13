# Architecture Notes (Milestone 1 reality)

This playground currently prioritizes a **small, deterministic, runnable** failure-analysis surface over a full distributed platform.

## What is actually in Milestone 1

### Stable synchronous path
1. Client -> `api-gateway`
2. `api-gateway` -> `orders-service`
3. `orders-service` -> `payments-service`
4. `orders-service` persists order state in PostgreSQL

### Failure scenario in scope
- **S001** (`RestTemplate` timeout from `orders-service` to `payments-service`) is the only fully stabilized, verified failure scenario in this milestone.

## Deferred/disabled-by-default areas

### Kafka
- Kafka-style event publishing code paths exist, but Kafka runtime flow is **deferred for Milestone 1**.
- In default Milestone 1 config, Kafka publishing is disabled (`orders.events.kafka.enabled: false`).
- Do not treat Kafka scenarios as runnable acceptance criteria for this milestone.

### Pub/Sub-like notifications
- Notification behavior is currently local/simulated; real external Pub/Sub integration is deferred.
- Pub/Sub failure scenarios are placeholders until a real runtime integration is implemented and tested.

### Observability stack
- Observability configuration files exist (`observability/*`), but a full production-like stack is **not required** for Milestone 1 verification.
- Milestone 1 acceptance is based on API behavior, health checks, and reproducible scenario outcomes (SUCCESS + S001), not on Grafana/Loki/Tempo dashboards being operational.

## Why this scope is intentional
- Keeps diagnosis deterministic for AI-agent evaluation.
- Reduces infrastructure noise while validating contract-level behavior:
  - success response contract,
  - timeout error contract (`PAYMENT_TIMEOUT`, HTTP 504),
  - correlation ID propagation.

## AI diagnostics compatibility in Milestone 1
A diagnostics agent should be able to:
1. detect a failed `POST /api/orders` symptom,
2. pivot by `correlationId` across gateway/orders/payments logs,
3. infer downstream timeout as root cause,
4. produce an evidence-backed conclusion consistent with S001 expectations.

## Recommended next milestone
After maintaining S001 stability, add one additional deterministic synchronous failure (recommended: S002 payments HTTP 500) plus script-based verification, then expand asynchronous infrastructure incrementally.
