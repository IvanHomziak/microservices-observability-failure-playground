# S006 — Pub/Sub publish failure

## Scenario ID
S006

## Description
Simulates publish acknowledgement failure on notification fan-out path.

## Services involved
- `orders-service`
- `notification-service`
- In-memory/adapter PubSub implementation

## How to enable the scenario
- Use `notification-service` failure mode controls (see service README/config) to force publish/ack failure.
- If needed, add/enable `orders.failures.publish-notification-failure` path for deterministic failure injection.

## How to trigger it
- Place order or call notification simulation endpoint that publishes notification event.

## Expected logs
- Publish attempt followed by failure/negative ack logs.

## Expected traces
- Error span in notification publish adapter.

## Expected metrics
- Publish failure counter increases.
- Notification success rate drops.

## Expected root cause
Messaging adapter failed to publish or receive ack from pub/sub channel.

## What the AI diagnostics agent should conclude
Notification fan-out path is degraded due to publish failure, while core order path may still succeed depending on coupling.

## Known limitations
- Behavior may differ between in-memory simulation and real broker semantics.
