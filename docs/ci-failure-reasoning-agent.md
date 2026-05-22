# CI Failure Reasoning Agent

## Purpose

This document describes the first read-only CI Failure Reasoning Agent scaffold.

The agent converts a bounded CI evidence pack into a structured diagnostic report.

It is intentionally conservative:

- no LLM calls;
- no secrets;
- no code mutation;
- no PR creation;
- no deployment;
- no image publishing;
- no write permissions.

The goal is to establish a safe agent contract before adding any model integration.

## Current architecture

```text
Failed GitHub Actions run
        |
        v
Collect run/job/log/artifact evidence
        |
        v
CI Failure Diagnostics report
        |
        v
Agent Fix Plan
        |
        v
Read-only CI Failure Reasoning Agent
        |
        v
agent-diagnostic-report.md
```

## Files

| File | Purpose |
|---|---|
| `agents/ci_failure_reasoning_agent/` | Python package scaffold |
| `agents/ci_failure_reasoning_agent/src/ci_failure_reasoning_agent/evidence_loader.py` | Loads bounded evidence pack |
| `agents/ci_failure_reasoning_agent/src/ci_failure_reasoning_agent/reasoner.py` | Deterministic reasoning layer |
| `agents/ci_failure_reasoning_agent/src/ci_failure_reasoning_agent/renderer.py` | Markdown report renderer |
| `agents/ci_failure_reasoning_agent/src/ci_failure_reasoning_agent/main.py` | CLI entrypoint |
| `.github/workflows/ci-failure-reasoning-agent.yml` | Manual workflow wrapper |

## Evidence pack

The agent reads only bounded evidence:

```text
triage/raw/run.json
triage/raw/jobs.json
triage/output/ci-failure-diagnostics-report.md
triage/output/agent-fix-plan.md
triage/logs/workflow-run.log
AGENTS.md
```

The agent does not scan the entire repository by default.

This reduces hallucination risk, cost, prompt-injection surface, and reasoning ambiguity.

## Output

The generated report is:

```text
agent-diagnostic-report.md
```

It includes:

- executive summary;
- evidence inspected;
- failed workflow;
- failed jobs and steps;
- symptoms;
- root-cause hypotheses;
- confidence;
- missing evidence;
- recommended fix;
- files likely affected;
- files not to change casually;
- validation plan;
- risk assessment;
- safety boundary.

## Local usage

After producing a triage evidence directory, run:

```bash
PYTHONPATH=agents/ci_failure_reasoning_agent/src \
python -m ci_failure_reasoning_agent.main \
  --evidence-dir triage \
  --repository-root . \
  --output reasoning/output/agent-diagnostic-report.md
```

## GitHub Actions usage

1. Open a failed GitHub Actions run.
2. Copy the run ID from the URL.
3. Open:

```text
Actions -> CI Failure Reasoning Agent -> Run workflow
```

4. Paste the run ID.
5. Download artifact:

```text
ci-failure-reasoning-agent-<run_id>
```

6. Review:

```text
agent-diagnostic-report.md
```

## Safety model

The workflow is manual-only:

```yaml
on:
  workflow_dispatch:
```

Permissions are read-only:

```yaml
permissions:
  actions: read
  contents: read
```

The workflow must not be converted to automatic PR execution without explicit review.

## Anti-hallucination rules

The agent must:

- report missing evidence explicitly;
- avoid claiming root cause when only symptoms are known;
- avoid scanning unrelated repository files unless explicitly requested;
- derive confidence from deterministic evidence quality;
- keep human approval in the loop.

The agent must not:

- invent services, ports, scripts, endpoints, topics, or workflow names;
- weaken CI checks to make a run green;
- remove verifier assertions without updating scenario contracts;
- create patches automatically;
- open PRs automatically;
- use secrets from PR workflows;
- run on `pull_request_target`.

## Current limitations

This scaffold is not yet an LLM-powered agent.

Known limitations:

- deterministic reasoning only;
- rule-based category extraction;
- no code patch generation;
- no source-code search beyond bounded evidence;
- no Surefire XML parsing inside the reasoning package;
- no comments posted back to PRs;
- no autonomous remediation.

## Recommended next evolution

Do not jump directly to auto-fix.

Recommended order:

```text
v1: read-only deterministic reasoning report
v2: optional LLM provider interface over bounded evidence
v3: structured JSON output schema validation
v4: patch proposal artifact, no commit
v5: human-approved PR creation with strict permissions
```

The next safe step after this scaffold is to add an optional provider abstraction that can later support LLM summarization without changing workflow permissions or enabling code mutation.
