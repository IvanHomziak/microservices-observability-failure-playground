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

## Implementation status summary

### Implemented
- `S001` (`trigger-s001-resttemplate-timeout.sh`)
- `S002` (`trigger-s002-payments-http-500.sh`, `verify-s002-payments-http-500.sh`)
- `S003` (`trigger-s003-db-slow-query.sh`, `verify-s003-db-slow-query.sh`)
- `S004` (`trigger-s004-kafka-poison-message.sh`, `verify-s004-kafka-poison-message.sh`)
- `S005` (`trigger-s005-kafka-consumer-lag.sh`, `verify-s005-kafka-consumer-lag.sh`)
- `S006` (`trigger-s006-pubsub-publish-failure.sh`, `verify-s006-pubsub-publish-failure.sh`)
- `S007` (`trigger-s007-broken-trace-propagation.sh`, `verify-s007-broken-trace-propagation.sh`)
- `S008` (`trigger-s008-missing-correlation-id.sh`, `verify-s008-missing-correlation-id.sh`)

### Partially implemented
- None currently documented.

### Placeholder
- None currently documented.

## Consistency notes
- All scenario docs now use one standardized structure (16 sections).
- Endpoint for synchronous request scenarios is `POST /api/orders` at `http://localhost:8080/api/orders`.
- Scenario docs reference exact script names and exact config property names used in code/config.
