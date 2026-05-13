# Implementation Plan

## Phase 1 — Repository Scaffold
1. Create top-level folders and independent Spring Boot services.
2. Ensure Java 21 and Spring Boot 3.x in each Maven project.
3. Add baseline service configs with unique ports and actuator/tracing settings.

## Phase 2 — Observability Foundation
1. Add Docker Compose stack for Prometheus, Grafana, Tempo, Loki, Kafka, and ZooKeeper.
2. Add minimal Prometheus and Tempo config to collect telemetry.
3. Wire service OTLP defaults and metrics endpoints.

## Phase 3 — Failure Scenarios
1. Add deterministic scenario playbooks with trigger steps.
2. Define expected telemetry signatures and root cause for each scenario.
3. Add script placeholders for triggering incidents reproducibly.

## Phase 4 — AI Diagnostics Agent Workflow
1. Document trace-first investigation path.
2. Define expected AI outputs per scenario (suspected service, evidence, root cause, remediation).
3. Prepare repo for follow-up service-level scenario implementation.
