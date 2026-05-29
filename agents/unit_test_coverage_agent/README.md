# Unit Test Coverage Agent

For OpenAI advisory mode and workflow usage, see [`docs/unit-test-coverage-openai-advisory-mode.md`](../../docs/unit-test-coverage-openai-advisory-mode.md) from the repository root.

Evidence-first agent for reviewing whether changed Java production code has adequate unit-test coverage.

## Scope

Current version:

- collects changed files from Git diff;
- classifies changed files;
- parses existing Surefire XML reports;
- parses existing JaCoCo XML reports;
- maps changed Java code to JaCoCo class/method coverage;
- evaluates coverage against configurable repository policy;
- generates validated JSON and markdown reports;
- optionally refines the deterministic report using LangChain + OpenAI;
- generates advisory patch proposal artifacts for missing/partial test coverage;
- does not mutate code;
- does not create PRs;
- does not enforce branch protection by itself.

## Providers

Supported providers:

```text
deterministic
langchain-openai
```

Default provider:

```text
deterministic
```

`deterministic` is the default provider. It performs no external call, does not read `OPENAI_API_KEY`, and renders stable output from local deterministic evidence only.

`langchain-openai` is optional advisory mode. It is explicit opt-in with `--provider langchain-openai` and requires:

```text
OPENAI_API_KEY
```

The key is required only for `langchain-openai`; deterministic mode must work without it. The key value and environment variables must not be rendered into reports, prompts, or error messages.

Optional model override:

```text
OPENAI_MODEL
```

Default model when `OPENAI_MODEL` is absent:

```text
gpt-4.1-mini
```

The model name is selected locally. The provider does not validate model availability by making a startup OpenAI call.

## Inputs

```text
base_ref
head_ref
provider
policy
```

Deterministic example:

```bash
PYTHONPATH=agents/unit_test_coverage_agent/src \
python -m unit_test_coverage_agent.main \
  --repository-root . \
  --base-ref origin/main \
  --head-ref HEAD \
  --policy coverage-policy.yml \
  --provider deterministic \
  --output coverage-agent/output/unit-test-coverage-report.md \
  --json-output coverage-agent/output/unit-test-coverage-report.json \
  --prompt-output coverage-agent/output/coverage-reasoning-prompt.md \
  --patch-proposal-output coverage-agent/output/unit-test-coverage-patch-proposal.md \
  --patch-proposal-json-output coverage-agent/output/unit-test-coverage-patch-proposal.json
```

LangChain example:

```bash
export OPENAI_API_KEY="<redacted>"
export OPENAI_MODEL="gpt-4.1-mini"

PYTHONPATH=agents/unit_test_coverage_agent/src \
python -m unit_test_coverage_agent.main \
  --repository-root . \
  --base-ref origin/main \
  --head-ref HEAD \
  --policy coverage-policy.yml \
  --provider langchain-openai \
  --output coverage-agent/output/unit-test-coverage-report.md \
  --json-output coverage-agent/output/unit-test-coverage-report.json \
  --prompt-output coverage-agent/output/coverage-reasoning-prompt.md \
  --patch-proposal-output coverage-agent/output/unit-test-coverage-patch-proposal.md \
  --patch-proposal-json-output coverage-agent/output/unit-test-coverage-patch-proposal.json
```

## Manual workflow with OpenAI advisory provider

The `Unit Test Coverage Agent` GitHub Actions workflow is manual/advisory only and starts only from `workflow_dispatch`. It must not be used as the required automatic pull request quality gate.

To run the manual workflow with OpenAI advisory explanations:

1. Add a repository secret:
   - Go to `Settings -> Secrets and variables -> Actions -> New repository secret`.
   - Name the secret `OPENAI_API_KEY`.
2. Run the workflow:
   - Go to `Actions -> Unit Test Coverage Agent -> Run workflow`.
3. Use these inputs when OpenAI advisory mode is desired:
   - `provider`: `langchain-openai`
   - `model`: `gpt-4.1-mini`
   - `base_ref`: `origin/main`
   - `head_ref`: `HEAD`
   - `run_tests`: `true` to run Maven verification first, or `false` to analyze existing evidence if present.

Manual coverage workflows install Java 21 before Maven verification. If Maven fails after Java setup, it should represent a real build or test issue rather than missing JDK setup.

Deterministic mode remains the default, does not require `OPENAI_API_KEY`, and performs no external model call. `langchain-openai` requires `OPENAI_API_KEY`, uses `OPENAI_MODEL` from the workflow `model` input, and is advisory only. Pass/fail remains deterministic when enforcement is used; OpenAI may refine explanations and recommendations but must not control required PR gate decisions.

## Coverage policy

Default policy file:

```text
coverage-policy.yml
```

Supported fields:

```text
minimum_line_coverage_for_changed_classes
minimum_method_coverage_for_changed_classes
require_test_changes_when_production_code_changes
fail_on_unknown_coverage
fail_on_missing_surefire_evidence
fail_on_missing_jacoco_evidence
```

The policy is advisory by default. It influences the generated report, PR comment, and merge recommendation, but it does not configure GitHub branch protection automatically.

## Evidence sources

The agent reads:

```text
git diff --name-only <base_ref>...<head_ref>
*/target/surefire-reports/TEST-*.xml
*/target/site/jacoco/jacoco.xml
coverage-policy.yml
```

## Output

```text
unit-test-coverage-report.md
unit-test-coverage-report.json
coverage-reasoning-prompt.md
unit-test-coverage-patch-proposal.md
unit-test-coverage-patch-proposal.json
```

## Patch proposal artifact

The patch proposal artifact recommends:

- production class that needs tests;
- suggested test file path;
- suggested test class name;
- suggested test method names;
- rationale;
- validation commands.

It is advisory only. It does not apply patches, generate commits, or create PRs.

## Coverage status values

```text
sufficient
partial
insufficient
unknown
not_applicable
policy_violation
```

## Safety boundary

The report is advisory only. It does not authorize code mutation, test deletion, PR creation, deployment, secrets access, workflow permission escalation, or automatic remediation.

## LangChain safety model

The LangChain provider:

- receives only the deterministic coverage evidence contract;
- does not receive unrestricted logs, environment variables, request headers, tokens, secrets, or full repository source code unless that content is already part of the validated deterministic evidence contract;
- is explicit opt-in;
- requires `OPENAI_API_KEY`;
- uses `OPENAI_MODEL` when set and otherwise uses `gpt-4.1-mini`;
- must return JSON only;
- has its response validated against the local output schema;
- cannot decide pass/fail;
- cannot change deterministic authority fields such as `coverage_status`, `merge_recommendation`, `policy_violations`, or `policy_warnings`;
- may only refine advisory explanation fields that remain supported by deterministic evidence;
- cannot mutate code;
- cannot create PRs;
- cannot deploy;
- cannot access write permissions from the workflow.

Pass/fail remains based only on deterministic policy violations in the validated JSON contract. Markdown is rendered from validated JSON, not from raw model text. Provider metadata is printed by the CLI as provider name, model name, and whether an external call was used; it must not include API keys, token values, secrets, or raw request headers.

The automatic pull request quality gate remains deterministic-only and separate from optional OpenAI advisory mode.

## Tests

```bash
cd agents/unit_test_coverage_agent
python -m compileall src tests
python -m unittest discover -s tests
```

## Optional OpenAI-enhanced PR comments

The manual `Unit Test Coverage PR Comment` workflow can add an optional OpenAI-generated advisory summary to the PR comment when `use_llm_summary=true`. The default remains deterministic-only: no `OPENAI_API_KEY` is required and no external model call is made when the input is `false`.

When enabled, the OpenAI call happens only in the trusted `update-pr-comment` job after deterministic artifacts have been generated and downloaded. The model receives validated coverage JSON, validated patch proposal JSON, and optionally trimmed deterministic Markdown. The response must validate as bounded JSON before rendering; invalid responses fall back to the deterministic comment with a short unavailable note.

The enhanced summary may improve explanation quality, reviewer guidance, developer next steps, and risk wording. It cannot change deterministic policy facts such as `coverage_status`, `merge_recommendation`, `policy_violations`, `policy_warnings`, changed files, coverage percentages, affected services, test failure counts, or Maven failure status. The existing `<!-- unit-test-coverage-agent-comment -->` marker is preserved so the workflow updates the existing bot comment instead of creating duplicates.

See `../../docs/unit-test-coverage-openai-advisory-mode.md` for setup, workflow inputs, and troubleshooting.
