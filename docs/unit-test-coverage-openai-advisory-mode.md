# Unit Test Coverage OpenAI Advisory Mode

## Purpose

The Unit Test Coverage Agent supports an optional `langchain-openai` provider for advisory explanation quality. OpenAI can help summarize deterministic coverage evidence and improve recommendations, but it must not become part of pull request pass/fail enforcement.

## What OpenAI may improve

`langchain-openai` may refine advisory fields that are already grounded in deterministic evidence:

- missing test scenario explanations;
- recommended test descriptions;
- blocking reason wording;
- confidence wording within the schema enum.

The provider sends the validated deterministic coverage evidence contract to the model and asks for JSON only. Markdown reports are rendered from validated JSON, not raw model text.

## What OpenAI must not control

OpenAI/LangChain must not decide or override:

- `coverage_status`;
- `merge_recommendation`;
- `policy_violations`;
- `policy_warnings`;
- branch protection behavior;
- pull request quality gate behavior;
- code mutation, commits, PR creation, deployment, or automatic remediation.

Pass/fail remains based only on deterministic policy violations in the validated JSON contract.

## Security constraints

The optional provider must not send or render:

- `OPENAI_API_KEY` values;
- token values or secrets;
- all environment variables;
- raw request headers;
- unrestricted logs;
- full repository source code unless that content is already explicitly part of the validated deterministic evidence contract.

If `--provider langchain-openai` is selected without `OPENAI_API_KEY`, the agent fails with:

```text
OPENAI_API_KEY is required for provider=langchain-openai
```

The error must not print the key value or dump environment variables.

## Provider metadata

The CLI prints non-secret provider metadata:

- provider name;
- model name when used;
- whether an external call was used.

This metadata must not include API keys, token values, secrets, or raw request headers.

## Run deterministic mode locally

```bash
cd agents/unit_test_coverage_agent
PYTHONPATH=src python -m unit_test_coverage_agent.main \
  --repository-root ../.. \
  --base-ref origin/main \
  --head-ref HEAD \
  --policy ../../coverage-policy.yml \
  --provider deterministic \
  --output ../../coverage-agent/output/unit-test-coverage-report.md \
  --json-output ../../coverage-agent/output/unit-test-coverage-report.json \
  --prompt-output ../../coverage-agent/output/coverage-reasoning-prompt.md \
  --patch-proposal-output ../../coverage-agent/output/unit-test-coverage-patch-proposal.md \
  --patch-proposal-json-output ../../coverage-agent/output/unit-test-coverage-patch-proposal.json
```

Deterministic mode is the default and does not require `OPENAI_API_KEY`.

## Run OpenAI advisory mode locally

```bash
cd agents/unit_test_coverage_agent
export OPENAI_API_KEY="<redacted>"
export OPENAI_MODEL="gpt-4.1-mini"
PYTHONPATH=src python -m unit_test_coverage_agent.main \
  --repository-root ../.. \
  --base-ref origin/main \
  --head-ref HEAD \
  --policy ../../coverage-policy.yml \
  --provider langchain-openai \
  --output ../../coverage-agent/output/unit-test-coverage-report.md \
  --json-output ../../coverage-agent/output/unit-test-coverage-report.json \
  --prompt-output ../../coverage-agent/output/coverage-reasoning-prompt.md \
  --patch-proposal-output ../../coverage-agent/output/unit-test-coverage-patch-proposal.md \
  --patch-proposal-json-output ../../coverage-agent/output/unit-test-coverage-patch-proposal.json
```

If `OPENAI_MODEL` is absent, the provider uses the project default model, `gpt-4.1-mini`. The provider does not make a startup call to validate model availability.

## Manual GitHub Actions workflow

The manual `Unit Test Coverage Agent` workflow may use OpenAI advisory mode because it is started only with `workflow_dispatch`. It must remain separate from the automatic `Unit Test Coverage PR Agent` quality gate.

Manual setup and execution:

1. Add the repository secret in GitHub: `Settings -> Secrets and variables -> Actions -> New repository secret`, with name `OPENAI_API_KEY`.
2. Open `Actions -> Unit Test Coverage Agent -> Run workflow`.
3. For OpenAI advisory mode, set:
   - `provider`: `langchain-openai`
   - `model`: `gpt-4.1-mini`
   - `base_ref`: `origin/main`
   - `head_ref`: `HEAD`
   - `run_tests`: `true` to generate fresh Maven/Surefire/JaCoCo evidence, or `false` to analyze existing evidence if present.

Deterministic mode is still the default and does not require `OPENAI_API_KEY`. The workflow should fail before report generation with a clear message when `provider=langchain-openai` is selected and the repository secret is missing.

## Pull request quality gate separation

The automatic pull request quality gate remains deterministic-only. This advisory mode does not require adding `OPENAI_API_KEY` to the PR workflow, does not use `pull_request_target`, does not add write permissions, and does not change branch protection behavior.
