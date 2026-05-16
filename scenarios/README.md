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

## Runtime verification matrix

| Scenario | Status | Compose override | Profile | Trigger script | Verification script | Expected outcome | Known limitations |
|---|---|---|---|---|---|---|---|
| S001 | Implemented | `docker-compose.s001.yml` | default | `./scripts/trigger-s001-resttemplate-timeout.sh` | `./scripts/verify-s001-resttemplate-timeout.sh` | HTTP 504 + `PAYMENT_TIMEOUT` | Must use override for determinism |
| S002 | Implemented | `docker-compose.s002.yml` | default | `./scripts/trigger-s002-payments-http-500.sh` | `./scripts/verify-s002-payments-http-500.sh` | HTTP 502 + `PAYMENT_5XX` | Must use override for determinism |
| Kafka success flow | Implemented | `docker-compose.kafka.yml` | `kafka` | `./scripts/trigger-kafka-success-flow.sh` | `./scripts/verify-kafka-flow.sh` | Event publish + consume logs for same correlation ID | Requires Kafka profile + override for deterministic verification |
| Notification flow | Implemented | `docker-compose.notification.yml` | `async` | `./scripts/trigger-notification-success-flow.sh` | `./scripts/verify-notification-flow.sh` | Notification publish + receive + sent logs | Requires async profile + override for deterministic verification |
| Audit flow | Implemented | `docker-compose.audit.yml` | `async` | Inline trigger in verifier (`POST /api/orders`) | `./scripts/verify-audit-flow.sh` | Audit event received for correlation ID | Requires async profile + override for deterministic verification |
| Observability stack validation | Partially implemented | none | `observability` | Inline trigger in verifier (`POST /api/orders`) | `./scripts/verify-observability-stack.sh` | Component health + triggerability + Docker log correlation | Deterministic Loki ingestion and Tempo trace lookup assertions are not automated |
| S003 — DB slow query | Partially implemented | env/config toggle | default | `./scripts/trigger-s003-db-slow-query.sh` | Not implemented yet | Success response with induced latency | No deterministic verifier currently included |
| S004 — Kafka poison message | Partially implemented | `docker-compose.kafka.yml` | `kafka` | `./scripts/trigger-s004-kafka-poison-message.sh` | Not implemented yet | Poison message processing failure + DLQ behavior | No deterministic verifier currently included |
| S005 — Kafka consumer lag | Partially implemented | `docker-compose.kafka.yml` | `kafka` | `./scripts/trigger-s005-kafka-consumer-lag.sh` | Not implemented yet | Consumer lag increase under load | No deterministic verifier currently included |
| S006 — Pub/Sub publish failure | Partially implemented | `docker-compose.notification.yml` | `async` | `./scripts/trigger-s006-pubsub-publish-failure.sh` | Not implemented yet | HTTP 503 + `NOTIFICATION_PUBLISH_FAILED` | No deterministic verifier currently included |
| S007 — Broken trace propagation | Partially implemented | env/config toggle | default | `./scripts/trigger-s007-broken-trace-propagation.sh` | Not implemented yet | Business call may succeed while traces disconnect | No deterministic verifier currently included |
| S008 — Missing correlation ID | Partially implemented | none | default | `./scripts/trigger-s008-missing-correlation-id.sh` | Not implemented yet | Correlation ID auto-generated and propagated | No deterministic verifier currently included |

Scenarios without verifier scripts must not be considered fully implemented.
