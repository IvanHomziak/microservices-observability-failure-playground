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

## OpenAI-enhanced PR comments

The manual `Unit Test Coverage PR Comment` workflow can optionally use OpenAI to add a bounded advisory summary to the bot comment that it posts on a pull request. This is separate from the deterministic `Unit Test Coverage PR Agent` quality gate.

### Configure the secret

Add the repository secret before enabling OpenAI summaries:

1. Open `Settings -> Secrets and variables -> Actions -> New repository secret`.
2. Set the secret name to `OPENAI_API_KEY`.
3. Paste the OpenAI API key value and save it.

Do not print the secret in workflow logs. The workflow only exposes the secret to the trusted comment-rendering job when `use_llm_summary=true`.

### Run the manual PR comment workflow

1. Open `Actions -> Unit Test Coverage PR Comment -> Run workflow`.
2. Use these inputs:
   - `pr_number`: `<PR>`
   - `run_tests`: `true` to generate fresh Maven/Surefire/JaCoCo evidence, or `false` to use available evidence.
   - `use_llm_summary`: `true`
   - `model`: `gpt-4.1-mini`

With `use_llm_summary=false`, behavior remains deterministic-only, no `OPENAI_API_KEY` is required, and no OpenAI call is made.

### What OpenAI can improve

The OpenAI-enhanced PR comment may improve only reviewer-facing advisory wording:

- executive summary quality;
- reviewer guidance;
- developer next-step wording;
- risk prioritization language;
- limitations based on the provided evidence.

The model receives validated coverage JSON, validated patch proposal JSON, and a trimmed deterministic Markdown report. It is instructed to reason only from those artifacts and to return bounded JSON.

### What OpenAI cannot change

OpenAI must not change or override deterministic facts, including:

- `coverage_status`;
- `merge_recommendation`;
- `policy_violations`;
- `policy_warnings`;
- changed files;
- coverage percentages;
- affected services;
- test failure counts;
- Maven failure status.

The validated local renderer still renders those fields from deterministic JSON artifacts. Raw model text is never posted directly.

### Security model

The workflow keeps the two-job security split:

1. `generate-coverage-evidence` has read-only permissions, checks out trusted agent code, creates a PR worktree, and generates deterministic artifacts without secrets or write credentials.
2. `update-pr-comment` has comment write permissions, checks out trusted agent code from the default branch, downloads deterministic artifacts, optionally calls OpenAI, validates the structured response, renders the final comment locally, and updates the existing bot comment marker.

Secrets are not available to code from the PR head. The workflow does not use `pull_request_target`, does not deploy, does not publish images, does not mutate code, and does not let the LLM decide pass/fail.

### Troubleshooting

- If `use_llm_summary=true` and the repository secret is missing, the workflow fails clearly with `OPENAI_API_KEY repository secret is required when use_llm_summary=true`.
- If the OpenAI response is invalid or cannot be validated, the renderer falls back to the deterministic comment and includes `LLM summary unavailable due to invalid response.`
- If an existing bot comment is present, the workflow finds `<!-- unit-test-coverage-agent-comment -->` and updates that comment instead of creating duplicates.
- If deterministic artifacts are invalid, comment rendering fails before any model output can be rendered.
