# Architecture Notes

This playground favors **simple business behavior** and **high observability density**. It is intentionally not a full product system.

## Design principles

1. **Simple domain, complex failure analysis**
   - Order placement is the central flow.
   - Business rules stay intentionally minimal so diagnosis effort focuses on telemetry and causality.

2. **Deterministic and replayable failures**
   - Every failure scenario must have explicit toggles (feature flags, headers, injected latency/error rates, or scripted state).
   - A scenario should be reproducible on demand and reversible.

3. **Cross-signal observability parity**
   - Each meaningful request path should produce:
     - structured logs,
     - metrics,
     - traces.
   - Failures should be visible in all three signals with consistent IDs.

4. **AI-agent friendly evidence model**
   - Scenarios must expose enough evidence for an external diagnostics agent to infer root cause from telemetry, not hidden implementation details.

## Baseline request and event topology

### Synchronous (HTTP)

1. Client -> `api-gateway`
2. `api-gateway` -> `orders-service`
3. `orders-service` -> `payments-service`
4. `orders-service` -> `inventory-service`

### Asynchronous (Kafka / Pub-Sub-like)

5. `orders-service` publishes domain events (e.g., `order.created`, `order.failed`).
6. `notification-service` and `audit-service` consume events.
7. Optional fan-out or forwarding can emulate Pub/Sub-like behavior (topic-based routing and independent consumers).

## Context propagation contract

Where transport allows, services should propagate a common tracing and correlation envelope:

- W3C `traceparent` / `tracestate` for distributed traces.
- Baggage or headers for domain context where appropriate.
- Message headers for Kafka and Pub/Sub-like events.

### Required IDs in logs

Each service should emit structured logs including:

- `service_name`
- `trace_id`
- `span_id`
- `correlation_id`
- `request_id`
- domain IDs (for example `order_id`, `payment_id`, `inventory_reservation_id`, `notification_id`)

## Telemetry requirements

### Metrics

- Spring Boot Actuator endpoints enabled (`/actuator/health`, `/actuator/prometheus`, etc.).
- Micrometer used for:
  - HTTP latency and error rates,
  - downstream dependency timings,
  - message publish/consume rates,
  - retry counts, timeout counts, and backlog/lag gauges.

### Traces

- OpenTelemetry instrumentation for incoming HTTP, outgoing HTTP, and message producer/consumer spans.
- Error classification should appear on spans (`status=ERROR`) with relevant attributes.

### Logs

- JSON structured logging with stable field names.
- Log entries should always support pivoting from metrics/traces back to causal events.

## Failure toggle model

Every scenario should define:

- **Toggle type**: config flag, request header, runtime endpoint, or script.
- **Activation scope**: one request, percentage, service-wide, or consumer-group scoped.
- **Expected impact**: user symptom and blast radius.
- **Expected telemetry signature**: logs + metrics + traces.
- **Rollback**: exact command/config to return to healthy baseline.

## AI diagnostics workflow compatibility

The platform should enable this external agent loop:

1. detect anomalous SLO/SLI condition,
2. identify affected request IDs and trace IDs,
3. reconstruct cross-service call/event path,
4. compare healthy vs failing telemetry patterns,
5. produce evidence-based root-cause hypothesis,
6. validate hypothesis against deterministic scenario expectation.

