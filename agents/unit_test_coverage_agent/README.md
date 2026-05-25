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

`deterministic` performs no external call.

`langchain-openai` requires:

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
- is explicit opt-in;
- requires `OPENAI_API_KEY`;
- must return JSON only;
- has its response validated against the local output schema;
- cannot mutate code;
- cannot create PRs;
- cannot deploy;
- cannot access write permissions from the workflow.

Markdown is rendered from validated JSON, not from raw model text.

## Tests

```bash
cd agents/unit_test_coverage_agent
python -m unittest discover -s tests
```