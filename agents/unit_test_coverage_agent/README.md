# Unit Test Coverage Agent

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
