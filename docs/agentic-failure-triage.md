# Agentic Failure Triage

## Purpose

This document explains the manual Agentic Failure Triage workflow.

The workflow converts deterministic CI diagnostics evidence into an agent-ready remediation plan.

The goal is to support the next stage of the agentic CI/CD loop:

```text
CI failed -> collect evidence -> generate diagnostics report -> generate agent fix plan -> human reviews -> targeted implementation
```

This workflow does not call an LLM.
It does not modify code.
It does not open pull requests.
It does not use repository secrets.
It does not deploy or publish anything.

## Files

| File | Purpose |
|---|---|
| `.github/workflows/agentic-failure-triage.yml` | Manual workflow that collects CI evidence and generates the fix plan |
| `scripts/generate-agent-fix-plan.py` | Deterministic fix-plan generator |
| `scripts/analyze-ci-failure.py` | Existing deterministic CI diagnostics analyzer reused by this workflow |
| `docs/agentic-failure-triage.md` | User guide for this triage flow |

## How to run

1. Open a failed GitHub Actions workflow run.
2. Copy the run ID from the URL.

Example:

```text
https://github.com/<owner>/<repo>/actions/runs/1234567890
```

The run ID is:

```text
1234567890
```

3. Go to:

```text
Actions -> Agentic Failure Triage -> Run workflow
```

4. Paste the run ID.
5. Start the workflow.
6. Download the artifact:

```text
agentic-failure-triage-<run_id>
```

7. Open:

```text
agent-fix-plan.md
```

## What the workflow collects

The workflow collects:

- workflow run metadata: `triage/raw/run.json`;
- job and step metadata: `triage/raw/jobs.json`;
- workflow logs: `triage/logs/workflow-run.log` when available;
- downloaded workflow artifacts: `triage/downloaded-artifacts/` when available.

It then generates:

- `triage/output/ci-failure-diagnostics-report.md`;
- `triage/output/agent-fix-plan.md`.

## What the agent fix plan contains

The generated `agent-fix-plan.md` includes:

- failed workflow summary;
- failed jobs and steps;
- observed deterministic failure categories;
- primary triage category;
- probable root cause;
- confidence level;
- files likely involved;
- files or behavior that must not be changed casually;
- recommended fix approach;
- validation commands;
- risk assessment;
- human approval requirement;
- evidence references.

## How agents should use this plan

Agents must treat the generated plan as advisory evidence, not as permission to mutate the repository.

Correct usage:

1. Read `agent-fix-plan.md`.
2. Inspect `ci-failure-diagnostics-report.md`.
3. Inspect raw logs and metadata.
4. Inspect affected repository files.
5. Propose the smallest safe fix.
6. Implement only after human approval or an explicit user request.
7. Let required workflows validate the fix.

Agents must not:

- invent missing evidence;
- claim root cause without supporting logs, metadata, or repository evidence;
- weaken CI checks to make a run green;
- delete verifier assertions without updating scenario contracts;
- remove failure scenarios casually;
- add secrets or write permissions to this workflow;
- convert this workflow into an auto-fix workflow without explicit review.

## Safety model

The workflow is manual-only:

```yaml
on:
  workflow_dispatch:
```

It uses read-only permissions:

```yaml
permissions:
  actions: read
  contents: read
```

It does not use:

- `pull_request_target`;
- secrets;
- deployment commands;
- Docker image publishing;
- write permissions;
- PR creation;
- auto-merge.

## Relationship to CI Failure Diagnostics

`CI Failure Diagnostics` produces a deterministic diagnostics report.

`Agentic Failure Triage` reuses that diagnostics logic and adds an additional remediation-planning layer.

The separation is intentional:

```text
CI Failure Diagnostics -> What failed?
Agentic Failure Triage -> What should be investigated or fixed next?
```

## Limitations

This is a deterministic v1 triage planner.

Known limitations:

- It is rule-based.
- It does not prove root cause by itself.
- It does not parse source code deeply.
- It does not parse Surefire XML reports yet.
- It does not call an LLM.
- It does not generate patches.
- It does not create pull requests.
- It does not post comments back to PRs.

## Future evolution

Recommended evolution:

```text
v1: deterministic triage plan, no LLM
v2: parse Surefire XML and include Java test failure details
v3: add optional LLM summary over deterministic evidence
v4: generate patch proposal without committing
v5: create PR with strict permissions and human review
```

Do not skip directly to v5.
