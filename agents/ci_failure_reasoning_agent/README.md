# CI Failure Reasoning Agent

Read-only scaffold for generating a structured diagnostic report from a bounded CI evidence pack.

## Scope

This package is intentionally conservative:

- no active LLM call;
- no secrets;
- no code mutation;
- no PR creation;
- no deployment;
- no image publishing.

## Provider model

The package now has a provider abstraction.

Current enabled provider:

```text
deterministic
```

The deterministic provider performs no external call and returns the locally rendered reasoning report.

External provider names such as `openai`, `llm`, or `external` intentionally fail closed. A real external provider must be added in a separate PR with explicit security review, structured output validation, environment protection, and no PR write permissions.

## Structured output contract

The package emits a validated structured JSON report:

```text
agent-diagnostic-report.json
```

Current schema version:

```text
1.0
```

The contract validates required fields, allowed confidence values, and non-empty evidence/recommendation lists without adding a third-party schema dependency.

This JSON contract is the future boundary for LLM output validation. A real LLM provider should not be trusted unless its output passes the same contract validation.

## Prompt artifact

The CLI can generate a bounded reasoning prompt artifact:

```text
reasoning-prompt.md
```

This artifact is for audit/review of the future LLM prompt contract. It is not sent to any model in the current implementation.

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
agent-diagnostic-report.json
reasoning-prompt.md
```

## Local run

```bash
PYTHONPATH=agents/ci_failure_reasoning_agent/src \
python -m ci_failure_reasoning_agent.main \
  --evidence-dir triage \
  --repository-root . \
  --provider deterministic \
  --output reasoning/output/agent-diagnostic-report.md \
  --json-output reasoning/output/agent-diagnostic-report.json \
  --prompt-output reasoning/output/reasoning-prompt.md
```

## Tests

```bash
cd agents/ci_failure_reasoning_agent
python -m unittest discover -s tests
```