# CI Failure Reasoning Agent

Read-only scaffold for generating a structured diagnostic report from a bounded CI evidence pack.

## Scope

This package is intentionally conservative:

- optional LLM call only when explicitly selected;
- no secrets in default deterministic mode;
- no code mutation;
- no PR creation;
- no deployment;
- no image publishing.

## Provider model

The package has a provider abstraction.

Supported providers:

```text
deterministic
openai
```

Default provider:

```text
deterministic
```

`deterministic` performs no external call and returns the locally rendered reasoning report.

`openai` is optional. It requires:

```text
OPENAI_API_KEY
```

Optional model override:

```text
OPENAI_MODEL
```

Default model:

```text
gpt-4.1-mini
```

Disabled aliases:

```text
llm
external
```

Those aliases intentionally fail closed. Use `openai` explicitly after environment review.

## Structured output contract

The package emits a validated structured JSON report:

```text
agent-diagnostic-report.json
```

Current schema version:

```text
1.0
```

The contract validates required fields, allowed confidence values, non-empty evidence/recommendation lists, and an explicit safety boundary without adding a third-party schema dependency.

The OpenAI provider output is not trusted unless it validates against this contract. Markdown is rendered from the validated JSON contract, not from raw model text.

## Prompt artifact

The CLI can generate a bounded reasoning prompt artifact:

```text
reasoning-prompt.md
```

This artifact is for audit/review of the prompt sent to the optional provider.

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

## Local deterministic run

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

## Local OpenAI run

```bash
export OPENAI_API_KEY="<redacted>"
export OPENAI_MODEL="gpt-4.1-mini"

PYTHONPATH=agents/ci_failure_reasoning_agent/src \
python -m ci_failure_reasoning_agent.main \
  --evidence-dir triage \
  --repository-root . \
  --provider openai \
  --output reasoning/output/agent-diagnostic-report.md \
  --json-output reasoning/output/agent-diagnostic-report.json \
  --prompt-output reasoning/output/reasoning-prompt.md
```

## Tests

```bash
cd agents/ci_failure_reasoning_agent
python -m unittest discover -s tests
```