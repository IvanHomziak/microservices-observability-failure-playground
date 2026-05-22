# CI Failure Diagnostics

## Purpose

This document explains the deterministic CI failure diagnostics workflow.

The goal is to improve the agentic CI/CD feedback loop:

```text
CI failed -> collect evidence -> classify failure signatures -> generate report -> human or agent fixes with evidence
```

This workflow does not call an LLM.
It does not modify code.
It does not open pull requests.
It does not use repository secrets.

It produces a markdown diagnostics report and raw evidence artifacts for review.

## Files

| File | Purpose |
|---|---|
| `.github/workflows/ci-failure-diagnostics.yml` | Manual workflow that collects logs, job metadata, artifacts, and generates the report |
| `scripts/analyze-ci-failure.py` | Deterministic rule-based log and job-metadata analyzer |
| `docs/ci-failure-diagnostics.md` | User guide for this diagnostics flow |

## How to run

1. Open the failed workflow run in GitHub Actions.
2. Copy the workflow run ID from the URL.

Example URL:

```text
https://github.com/<owner>/<repo>/actions/runs/1234567890
```

The run ID is:

```text
1234567890
```

3. Go to:

```text
Actions -> CI Failure Diagnostics -> Run workflow
```

4. Paste the run ID into the `run_id` input.
5. Start the workflow.
6. Download the artifact named:

```text
ci-failure-diagnostics-<run_id>
```

7. Open:

```text
ci-failure-diagnostics-report.md
```

## What the workflow collects

The workflow collects:

- workflow run metadata into `diagnostics/raw/run.json`;
- job and step metadata into `diagnostics/raw/jobs.json`;
- workflow logs into `diagnostics/logs/workflow-run.log` when available;
- downloaded workflow artifacts into `diagnostics/downloaded-artifacts/` when available.

The final artifact includes the generated markdown report plus raw evidence files.

## What the report contains

The report includes:

- repository name;
- workflow run ID;
- scanned evidence files;
- failed jobs and failed steps from `jobs.json`;
- detected failure categories;
- concrete log evidence;
- deterministic recommendations;
- suggested triage order;
- next validation commands.

## Failed jobs and steps section

The v2 diagnostics report includes a table like:

| Job | Conclusion | Status | Failed steps | Job URL |
|---|---|---|---|---|
| `Maven test (orders-service)` | `failure` | `completed` | `#4 Run Maven tests with retry (failure)` | open |

This section is based on GitHub Actions job metadata, not log pattern matching.

Use it to quickly identify which workflow job and step failed before reading raw logs.

## Current failure categories

The analyzer currently detects these categories:

| Category | Meaning |
|---|---|
| `service-startup-or-port-health-issue` | health endpoint connection reset, empty reply, connection refused, port/startup issue |
| `health-timeout` | service health endpoint did not become ready in time |
| `docker-compose-contract-failure` | Compose config or override contract failure |
| `maven-build-or-test-failure` | Java compilation or test failure |
| `maven-dependency-resolution` | Maven repository/network/dependency resolution issue |
| `shell-script-syntax-or-permission` | shell syntax, executable bit, interpreter, or missing file issue |
| `workflow-safety-policy-failure` | forbidden trigger, secret usage, deployment command, or safety-rule failure |
| `runtime-verifier-evidence-failure` | verifier expected evidence but did not find it |
| `workflow-timeout-or-hang` | workflow timeout, cancellation, or long-running hang |

## How agents should use this report

Agents should treat this report as an evidence index, not as final truth.

The correct workflow is:

1. Read `ci-failure-diagnostics-report.md`.
2. Start with the `Failed jobs and steps` table.
3. Inspect the raw logs referenced by the report.
4. Inspect the affected repository files.
5. Identify the smallest safe fix.
6. Make the change in a PR.
7. Let dedicated workflows validate the fix.

Agents must not claim root cause based only on a category match if the raw evidence is insufficient.

## Limitations

This is v2 of the diagnostics flow.

Known limitations:

- It is rule-based and may miss new failure signatures.
- It can classify symptoms but does not prove root cause by itself.
- It only analyzes logs, job metadata, and downloaded artifacts available to the workflow token.
- It does not parse Surefire XML reports yet.
- It does not use LLM reasoning.
- It does not perform code changes.
- It does not create PRs.
- It does not access external systems.

## Safety model

The workflow uses:

```yaml
permissions:
  actions: read
  contents: read
```

It does not require secrets.

It is manual-only:

```yaml
on:
  workflow_dispatch:
```

This keeps the diagnostics flow safe for the current POC.

## Future evolution

Possible next steps:

1. Add more deterministic rules as failure patterns appear.
2. Add support for parsing Surefire XML reports.
3. Add richer workflow-run summary from `diagnostics/raw/run.json`.
4. Add optional LLM summarization over the generated evidence pack.
5. Add an agent-generated fix proposal.
6. Add agent-created PRs only after explicit permissions and prompt-injection review.

The recommended evolution is:

```text
v1: deterministic report, no LLM
v2: richer deterministic parser with failed job metadata
v3: Surefire XML parsing and richer run summary
v4: optional LLM summary, manual-only
v5: agent proposes fix
v6: agent opens PR with strict permissions and human review
```
