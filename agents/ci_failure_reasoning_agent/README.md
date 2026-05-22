# CI Failure Reasoning Agent

Read-only scaffold for generating a structured diagnostic report from a bounded CI evidence pack.

## Scope

This package is intentionally conservative:

- no LLM call;
- no secrets;
- no code mutation;
- no PR creation;
- no deployment;
- no image publishing.

## Input

Expected evidence directory:

```text
triage/
  raw/
    run.json
    jobs.json
  logs/
    workflow-run.log
  output/
    ci-failure-diagnostics-report.md
    agent-fix-plan.md
```

The package also reads repository-level `AGENTS.md` from the provided repository root.

## Output

```text
agent-diagnostic-report.md
```

## Local run

```bash
PYTHONPATH=agents/ci_failure_reasoning_agent/src \
python -m ci_failure_reasoning_agent.main \
  --evidence-dir triage \
  --repository-root . \
  --output reasoning/output/agent-diagnostic-report.md
```

## Tests

```bash
cd agents/ci_failure_reasoning_agent
python -m unittest discover -s tests
```
