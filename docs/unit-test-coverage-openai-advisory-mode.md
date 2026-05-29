# Unit Test Coverage OpenAI Advisory Mode

## Purpose

This document explains safe `OPENAI_API_KEY` usage for the Unit Test Coverage Agent workflows.

The key rule is that OpenAI is an **advisory explanation layer only**. It may improve human-facing summaries after deterministic evidence has already been generated, but it must not decide whether a pull request is green or red.

## Two-layer coverage-agent model

The test coverage agent has two layers.

### A. Deterministic enforcement layer

The deterministic layer is the source of truth for coverage evidence and pass/fail behavior. It uses repository-local evidence and policy logic, including:

- Git diff;
- affected service detection;
- Maven `verify`;
- Maven failed-service evidence from `coverage-agent/raw/maven-failed-services.txt`;
- Surefire XML;
- JaCoCo XML;
- coverage policy;
- `enforce_policy`;
- green/red decisions.

This layer decides `coverage_status`, `merge_recommendation`, `policy_violations`, and policy enforcement results. It also passes `--test-execution-failures-file coverage-agent/raw/maven-failed-services.txt` into report generation so collected Maven failures appear in `test_execution_failures` and the Markdown `Test execution failures` section. Maven failure evidence is advisory or blocking depending on the selected deterministic policy. It is the only layer that may be used for branch protection or required PR checks.

### B. Optional OpenAI advisory layer

The optional OpenAI advisory layer reads validated deterministic JSON artifacts after the deterministic layer has produced them. It may improve:

- human explanation quality;
- reviewer recommendations;
- PR comment wording;
- management-friendly summaries.

It does **not** decide green/red. It must not override deterministic evidence, mutate code, create PRs, deploy, or change branch protection.

## Workflows and OpenAI usage matrix

| Workflow | File | OpenAI allowed? | Why |
|---|---|---:|---|
| Unit Test Coverage PR Agent | `.github/workflows/unit-test-coverage-pr-agent.yml` | No | automatic PR quality gate, no secrets, deterministic |
| Unit Test Coverage Agent | `.github/workflows/unit-test-coverage-agent.yml` | Yes, optional | manual advisory analysis |
| Unit Test Coverage PR Comment | `.github/workflows/unit-test-coverage-pr-comment.yml` | Yes, optional | manual comment enhancement from validated artifacts |
| Unit Test Coverage Policy Check | `.github/workflows/unit-test-coverage-policy-check.yml` | No or not recommended | manual deterministic enforcement/debug |

## Explicit safety rule

**OPENAI_API_KEY must not be added to Unit Test Coverage PR Agent.**

Reason:

- it runs on `pull_request`;
- it should be deterministic;
- it should not depend on secrets;
- it should be safe for branch protection;
- an LLM must not decide pass/fail.

The automatic PR quality gate must remain deterministic-only and safe for required checks.

## How to add `OPENAI_API_KEY`

Add the key only as a GitHub Actions repository secret:

1. Open the GitHub repository.
2. Go to `Settings -> Secrets and variables -> Actions -> New repository secret`.
3. Use this name:

   ```text
   OPENAI_API_KEY
   ```

4. Use this value:

   ```text
   <your OpenAI API key>
   ```

Do not commit the key.
Do not put it in YAML directly.
Do not print it in logs.
Do not upload it in artifacts.

## How to run manual Unit Test Coverage Agent with OpenAI

Use this path when you want an advisory coverage report with optional LLM-refined wording:

```text
Actions -> Unit Test Coverage Agent -> Run workflow
```

Recommended inputs for OpenAI advisory mode:

| Input | Value |
|---|---|
| `base_ref` | `origin/main` |
| `head_ref` | `HEAD` or a branch/ref |
| `run_tests` | `true` or `false` |
| `provider` | `langchain-openai` |
| `model` | `gpt-4.1-mini` |

Expected result:

- deterministic report generated;
- optional LLM-refined explanation when `OPENAI_API_KEY` is configured;
- coverage artifacts uploaded.

### Deterministic mode

Use deterministic mode when you do not want an OpenAI call:

```text
provider: deterministic
```

Deterministic mode does not require `OPENAI_API_KEY`.

## How to run PR Comment workflow with OpenAI

Use this path when you want a PR comment created or updated from validated coverage artifacts, with optional OpenAI-enhanced wording:

```text
Actions -> Unit Test Coverage PR Comment -> Run workflow
```

Recommended inputs for OpenAI-enhanced PR comments:

| Input | Value |
|---|---|
| `pr_number` | `<PR number>` |
| `run_tests` | `true` or `false` |
| `use_llm_summary` | `true` |
| `model` | `gpt-4.1-mini` |

Expected result:

- deterministic artifacts generated;
- optional LLM summary rendered;
- PR comment created or updated;
- existing comment marker prevents duplicates.

Use this input to render the deterministic-only comment without OpenAI:

```text
use_llm_summary: false
```

The comment marker is:

```text
<!-- unit-test-coverage-agent-comment -->
```

## What OpenAI may improve

OpenAI may improve advisory, human-facing language only, including:

- reviewer summary;
- management-friendly explanation;
- developer next steps;
- suggested tests wording;
- risk prioritization;
- explanation of policy violations.

## What OpenAI must not control

OpenAI must not control or override deterministic facts and repository controls, including:

- `coverage_status`;
- `merge_recommendation`;
- `policy_violations`;
- `policy_warnings`;
- `test_execution_failures`;
- changed files;
- coverage percentages;
- branch protection;
- required checks;
- code mutation;
- PR creation;
- deployment.

## How to demo OpenAI advisory mode

Use this sequence for the POC demo:

1. Open a negative validation PR.
2. Show that `Unit Test Coverage PR Agent` fails deterministically.
3. Explain that branch protection blocks merge.
4. Run `Unit Test Coverage PR Comment` with `use_llm_summary=false`.
5. Show the deterministic comment.
6. Run `Unit Test Coverage PR Comment` with `use_llm_summary=true`.
7. Show the improved human explanation.
8. Emphasize that the red/green result did not change.

Key message:

```text
AI improves explanation, not enforcement.
```

## Troubleshooting

### `provider=langchain-openai` fails with missing `OPENAI_API_KEY`

Confirm the repository secret exists at `Settings -> Secrets and variables -> Actions`. The secret name must be exactly `OPENAI_API_KEY`.

If the secret is intentionally absent, rerun with:

```text
provider: deterministic
```

### Secret is configured but the workflow cannot read it

Confirm you are running a workflow that is allowed to use OpenAI:

- `Unit Test Coverage Agent` may use `OPENAI_API_KEY` in manual advisory mode.
- `Unit Test Coverage PR Comment` may use `OPENAI_API_KEY` when `use_llm_summary=true`.
- `Unit Test Coverage PR Agent` must not use `OPENAI_API_KEY`.

Also confirm the workflow was started from the repository Actions tab and that repository Actions secrets are available to the selected branch/ref.

### OpenAI call fails

Treat this as an advisory-layer failure, not a deterministic coverage result. Rerun with deterministic mode or `use_llm_summary=false` to continue without OpenAI.

### Invalid LLM response

The model response must validate before it is rendered. Invalid advisory output must not change deterministic fields. Use deterministic mode or rerun the manual workflow after checking the model input.

### Deterministic fallback

For the manual coverage agent, select:

```text
provider: deterministic
```

For the PR comment workflow, select:

```text
use_llm_summary: false
```

### No PR comment appears

Confirm that `Unit Test Coverage PR Comment` was run with the correct `pr_number` and that the comment-update job completed. The workflow is manual and separate from the automatic PR quality gate.

### Duplicate comments

The PR comment workflow should update the existing bot comment when the marker is present:

```text
<!-- unit-test-coverage-agent-comment -->
```

If duplicates appear, verify that existing comments still contain that marker and were authored by `github-actions[bot]`.

### Wrong workflow was made required

Required branch protection should use `Unit Test Coverage PR Agent`, not advisory or manual workflows.

Correct required check:

- `Unit Test Coverage PR Agent`

Actual GitHub check context may appear as:

- `Add Unit Test Coverage PR Agent`
- `Generate deterministic unit test coverage evidence for PR`

Do not require:

- `Unit Test Coverage Agent`;
- `Unit Test Coverage PR Comment`;
- `Unit Test Coverage Policy Check`.

## Branch protection note

Required branch protection should use `Unit Test Coverage PR Agent`, not `Unit Test Coverage Agent`.

Correct required check:

- `Unit Test Coverage PR Agent`

Actual GitHub check context may appear as:

- `Add Unit Test Coverage PR Agent`
- `Generate deterministic unit test coverage evidence for PR`

Do not require:

- `Unit Test Coverage Agent`;
- `Unit Test Coverage PR Comment`;
- `Unit Test Coverage Policy Check`.

## Related documentation

- [Unit Test Coverage PR Agent](unit-test-coverage-pr-agent.md)
- [POC Validation Runbook](poc-validation-runbook.md)
- [Coverage PR Comment Integration](coverage-pr-comment-integration.md)
- [Unit Test Coverage Agent README](../agents/unit_test_coverage_agent/README.md)
