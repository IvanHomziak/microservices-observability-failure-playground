# Failure Scenarios

## Scenario index
- [S001 — RestTemplate timeout](./S001-resttemplate-timeout.md)
- [S002 — Payments HTTP 500](./S002-payments-http-500.md)
- [S003 — DB slow query](./S003-db-slow-query.md)
- [S004 — Kafka poison message](./S004-kafka-poison-message.md)
- [S005 — Kafka consumer lag](./S005-kafka-consumer-lag.md)
- [S006 — Pub/Sub publish failure](./S006-pubsub-publish-failure.md)
- [S007 — Broken trace propagation](./S007-broken-trace-propagation.md)
- [S008 — Missing correlation ID](./S008-missing-correlation-id.md)

## Runtime verification status

| Scenario | Status | Required profile/override | Deterministic verifier | Notes |
|---|---|---|---|---|
| S001 RestTemplate timeout | Implemented | `docker-compose.s001.yml` | `./scripts/verify-s001-resttemplate-timeout.sh` | Verifier starts full Milestone 1 + S001 override and restores default `payments-service` runtime on exit. |
| S002 Payments HTTP 500 | Implemented | `docker-compose.s002.yml` | `./scripts/verify-s002-payments-http-500.sh` | Verifier starts full Milestone 1 + S002 override and restores default `payments-service` runtime on exit. |
| Kafka success flow | Implemented | `docker-compose.kafka.yml` + `kafka` profile | `./scripts/verify-kafka-flow.sh` | Use verifier; profile alone is not sufficient unless kafka override/env flags are also applied. |
| Notification flow | Implemented | `docker-compose.notification.yml` + `async` profile | `./scripts/verify-notification-flow.sh` | Use verifier; profile alone is not sufficient unless notification override/env flags are also applied. |
| Audit flow | Implemented | `docker-compose.audit.yml` + `async` profile | `./scripts/verify-audit-flow.sh` | Use verifier; profile alone is not sufficient unless audit override/env flags are also applied. |
| Observability stack validation | Partially implemented | `observability` profile | `./scripts/verify-observability-stack.sh` | Verifies stack health + request triggers; does not guarantee Loki app logs unless Docker log mounts/socket are configured for Promtail. |

## Consistency notes
- Use verifier scripts for deterministic runtime validation instead of manual profile-only startup commands.
- Endpoint for synchronous request scenarios is `POST /api/orders` at `http://localhost:8080/api/orders`.
