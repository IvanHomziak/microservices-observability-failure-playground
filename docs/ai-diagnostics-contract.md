# AI Diagnostics Contract

This contract defines how a future AI diagnostics agent should consume evidence in this repository and how it should emit conclusions.

## Inputs and outputs
- **Input:** one `EvidencePack` JSON document (see `docs/evidence-pack-schema.md`).
- **Output:** one `DiagnosticReport` JSON document.

## DiagnosticReport schema

```json
{
  "scenarioId": "...",
  "incidentSummary": "...",
  "affectedServices": [],
  "rootCauseHypotheses": [
    {
      "cause": "...",
      "confidence": "LOW|MEDIUM|HIGH",
      "evidenceIds": [],
      "reasoningSummary": "..."
    }
  ],
  "performanceFindings": [],
  "missingData": [],
  "recommendedActions": [],
  "escalationRequired": false
}
```

## Agent reasoning workflow (required)
1. Validate `scenarioId`, `timeWindow`, and at least one of `correlationId` or `traceId`.
2. Build a timeline from `logs`, `spans`, `metrics`, and `events` ordered by timestamp.
3. Correlate by `correlationId` first (logs/events), then confirm with `traceId` (spans).
4. Identify symptom at API/service boundary (timeout, 5xx, lag, publish failure, broken observability context).
5. Produce 1-N hypotheses with explicit confidence and exact `evidenceIds` references.
6. Add `missingData` when confidence depends on absent telemetry.
7. Recommend actions that are concrete and testable (toggle check, retry policy, backpressure, propagation fix).

## How to consume logs, metrics, and traces
- **Logs:** establish error class, config mode, and service-local failure point.
- **Spans:** validate cross-service path, latency hotspots, and propagation continuity.
- **Metrics:** determine blast radius and severity (error rate, p95 latency, consumer lag).
- **Events:** confirm asynchronous transitions (publish ack/nack, retries, DLQ routing).

Agents should avoid overclaiming: if data only supports a probable cause, confidence must be `MEDIUM` or `LOW` and unresolved questions must be listed under `missingData`.

## Evaluation-only field handling
`knownExpectedRootCause` in EvidencePack is **for evaluation only**. It may be used by benchmark harnesses after inference, but agent reasoning should be based on telemetry evidence IDs, not this label.

## Scenario alignment notes
The sample reports in `docs/sample-agent-reports/` map to scenarios `S001` through `S008` documented in `scenarios/` and demonstrate realistic confidence, evidence usage, and actionability without claiming certainty beyond available signals.
