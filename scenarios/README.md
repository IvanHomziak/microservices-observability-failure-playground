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
| S003 | Implemented | none (env/config toggle) | default | `./scripts/trigger-s003-db-slow-query.sh` | `./scripts/verify-s003-db-slow-query.sh` | Success with induced latency | Metrics/traces depend on observability runtime |
| S004 | Implemented | `docker-compose.kafka.yml` | `kafka` | `./scripts/trigger-s004-kafka-poison-message.sh` | `./scripts/verify-s004-kafka-poison-message.sh` | Poison message retries + DLQ | Trace assertions are runtime dependent |
| S005 | Implemented | `docker-compose.kafka.yml` | `kafka` | `./scripts/trigger-s005-kafka-consumer-lag.sh` | `./scripts/verify-s005-kafka-consumer-lag.sh` | Lag grows under delay mode | Lag visibility depends on event volume |
| S006 | Implemented | `docker-compose.notification.yml` | `async` | `./scripts/trigger-s006-pubsub-publish-failure.sh` | `./scripts/verify-s006-pubsub-publish-failure.sh` | HTTP 503 + publish failure | Must enable notification flow toggles |
| S007 | Implemented | none (env/config toggle) | default | `./scripts/trigger-s007-broken-trace-propagation.sh` | `./scripts/verify-s007-broken-trace-propagation.sh` | Business flow succeeds; trace linkage broken | Trace proof depends on observability runtime |
| S008 | Implemented | none | default | `./scripts/trigger-s008-missing-correlation-id.sh` | `./scripts/verify-s008-missing-correlation-id.sh` | Correlation ID generated/propagated | Trace proof depends on observability runtime |

Observability verification status remains **Partially implemented** until deterministic Loki ingestion and Tempo lookup assertions are automated.
