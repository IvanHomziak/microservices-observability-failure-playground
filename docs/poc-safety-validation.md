# POC Safety Validation

## Purpose

This document describes the final lightweight safety validation gate for the Agentic GitHub Actions POC.

The goal is to catch unsafe workflow drift before the POC is considered complete.

## Workflow

Workflow:

```text
.github/workflows/poc-safety-validation.yml
```

Triggers:

```yaml
workflow_dispatch:
pull_request:
  paths:
    - ".github/workflows/**"
    - "agents/**"
    - "docs/**"
    - "scripts/validate_poc_safety.py"
    - "coverage-policy.yml"
```

## Permissions

```yaml
permissions:
  contents: read
  actions: read
```

The workflow has no write permissions and uses no secrets.

## Validation script

Script:

```text
scripts/validate_poc_safety.py
```

The script validates:

- expected workflows exist;
- expected POC documents exist;
- expected Unit Test Coverage Agent modules exist;
- `coverage-policy.yml` exists;
- no expected workflow uses `pull_request_target`;
- read-only workflows do not request PR or issue write permissions;
- PR comment workflow isolates evidence generation from comment write permissions;
- PR comment workflow does not use `OPENAI_API_KEY`;
- PR comment workflow does not expose LangChain/OpenAI provider inputs;
- policy enforcement workflow is deterministic-only;
- policy enforcement workflow does not request write permissions;
- Unit Test Coverage Agent workflow supports deterministic and optional LangChain/OpenAI modes but remains read-only.

## Python validation

The workflow also runs:

```bash
cd agents/unit_test_coverage_agent
python -m compileall src tests
python -m unittest discover -s tests
```

## Safety boundary

This validation gate does not:

- mutate code;
- create commits;
- create pull requests;
- post comments;
- deploy;
- access secrets;
- use write permissions;
- call an LLM.

## Recommended usage

Keep this workflow enabled for PRs that modify:

- workflows;
- agent code;
- documentation;
- safety validation logic;
- coverage policy.

This gives the POC a lightweight regression safety net.

## POC completion meaning

After this validation gate is merged, the POC can be considered complete for internal technical demo purposes.

Production rollout still requires:

- security review;
- audit logging;
- observability;
- cost tracking;
- branch protection strategy;
- operational ownership;
- false-positive monitoring.
