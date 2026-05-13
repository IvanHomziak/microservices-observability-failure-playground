# Failure Scenarios

This folder contains deterministic incident playbooks for the microservices observability failure playground.

## Scenario files

- `S001-resttemplate-timeout.md`
- `S002-payments-http-500.md`
- `S003-db-slow-query.md`
- `S004-kafka-poison-message.md`
- `S005-kafka-consumer-lag.md`
- `S006-pubsub-publish-failure.md`
- `S007-broken-trace-propagation.md`
- `S008-missing-correlation-id.md`

## Required section contract (per scenario)

Each scenario file includes:

- Scenario ID
- Description
- Services involved
- How to enable the scenario
- How to trigger it
- Expected logs
- Expected traces
- Expected metrics
- Expected root cause
- What the AI diagnostics agent should conclude
- Known limitations

## Implementation status

- **Fully implemented in this iteration:** `S001-resttemplate-timeout`
- **Documentation + placeholders:** `S002` through `S008`
