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
| S003 — DB slow query | Implemented | `docker-compose.s003.yml` | default | `./scripts/trigger-s003-db-slow-query.sh` | `./scripts/verify-s003-db-slow-query.sh` | HTTP 2xx with induced DB latency + slow-query log evidence | Requires override for deterministic latency threshold |
| S004 — Kafka poison message | Implemented | `docker-compose.s004.yml` | `kafka` | `./scripts/trigger-s004-kafka-poison-message.sh` | `./scripts/verify-s004-kafka-poison-message.sh` | HTTP 2xx trigger + poison-consumer failure and DLQ evidence | DLQ proof can be runtime/log-format dependent |
| S005 — Kafka consumer lag | Implemented | `docker-compose.s005.yml` | `kafka` | `./scripts/trigger-s005-kafka-consumer-lag.sh` | `./scripts/verify-s005-kafka-consumer-lag.sh` | Burst publish success + deterministic consumer processing delay evidence | Lag snapshots can read zero depending on sampling instant |
| S006 — Pub/Sub publish failure | Implemented | `docker-compose.s006.yml` | default | `./scripts/trigger-s006-pubsub-publish-failure.sh` | `./scripts/verify-s006-pubsub-publish-failure.sh` | HTTP 503 + `NOTIFICATION_PUBLISH_FAILED` with publish-failure logs | Requires S006 override to force failure deterministically |
| S007 — Broken trace propagation | Implemented | `docker-compose.s007.yml` | default | `./scripts/trigger-s007-broken-trace-propagation.sh` | `./scripts/verify-s007-broken-trace-propagation.sh` | HTTP 2xx business success with downstream trace propagation break evidence | Deterministic proof is log-based, not Tempo-UI dependent |
| S008 — Missing correlation ID | Implemented | none | default | `./scripts/trigger-s008-missing-correlation-id.sh` | `./scripts/verify-s008-missing-correlation-id.sh` | HTTP 2xx with auto-generated correlation ID propagated across services | Relies on log field consistency for matching evidence |
| Kafka success flow | Implemented | `docker-compose.kafka.yml` | `kafka` | `./scripts/trigger-kafka-success-flow.sh` | `./scripts/verify-kafka-flow.sh` | Event publish + consume logs for same correlation ID | Requires Kafka profile + override for deterministic verification |
| Notification flow | Implemented | `docker-compose.notification.yml` | `async` | `./scripts/trigger-notification-success-flow.sh` | `./scripts/verify-notification-flow.sh` | Notification publish + receive + sent logs | Requires async profile + override for deterministic verification |
| Audit flow | Implemented | `docker-compose.audit.yml` | `async` | Inline trigger in verifier (`POST /api/orders`) | `./scripts/verify-audit-flow.sh` | Audit event received for correlation ID | Requires async profile + override for deterministic verification |
| Observability stack | Partially implemented | none | `observability` | Inline trigger in verifier (`POST /api/orders`) | `./scripts/verify-observability-stack.sh` | Component health, request triggerability, Docker log correlation, Loki ingestion proof | Tempo trace lookup can downgrade to warning when deterministic trace ID extraction is unavailable |

Only scenarios with code path + deterministic override (if needed) + trigger + verifier + documentation are marked Implemented.
