# Unit Test Coverage PR Agent

## Purpose

This workflow automatically validates unit test coverage evidence for pull requests.

It exists because manual `workflow_dispatch` execution can be unreliable in GitHub UI/API. Pull request validation should not depend on manual dispatch.

## Workflow

```text
.github/workflows/unit-test-coverage-pr-agent.yml
```

## Trigger

```yaml
on:
  pull_request:
    paths:
      - "**/src/main/java/**"
      - "**/src/test/java/**"
      - "**/pom.xml"
      - "coverage-policy.yml"
      - "coverage-policy-pr.yml"
      - "agents/unit_test_coverage_agent/**"
      - ".github/workflows/unit-test-coverage-pr-agent.yml"
```

## Security model

This workflow is intentionally limited:

```text
pull_request only
deterministic only
no OpenAI
no LangChain
no secrets
no PR comments
no write permissions
no code mutation
no commits
no PR creation
no deployment
```

Permissions:

```yaml
permissions:
  contents: read
  actions: read
```

## Java runtime

The workflow configures Java 21 explicitly:

```yaml
uses: actions/setup-java@v4
with:
  distribution: temurin
  java-version: "21"
  cache: maven
```

This is required because the services compile with Java release 21. Without this setup, Maven can fail before tests run, producing no Surefire or JaCoCo evidence.

## Strict PR policy

The PR workflow uses:

```text
coverage-policy-pr.yml
```

This policy is stricter than the default advisory policy.

It fails on:

```text
unknown changed-class coverage
missing Surefire XML evidence
missing JaCoCo XML evidence
production Java changes without Java test changes
line coverage below threshold
method coverage below threshold
branch coverage below threshold (when branch counters exist)
```

## Flow

```text
pull request update
        |
        v
checkout PR code
        |
        v
setup Java 21
        |
        v
validate coverage agent Python package
        |
        v
detect affected services from PR diff
        |
        v
run Maven verify for affected services only
        |
        v
generate deterministic coverage report with coverage-policy-pr.yml
        |
        v
enforce coverage policy
        |
        v
upload coverage artifacts even on failure
```

## Enforcement behavior

The workflow runs:

```bash
python -m unit_test_coverage_agent.enforce_policy \
  --coverage-json coverage-agent/output/unit-test-coverage-report.json
```

Rules:

```text
policy_violations empty -> job succeeds
policy_violations non-empty -> job fails
policy_warnings only -> job succeeds
```

## Generated artifacts

Artifacts are uploaded with `if: always()` so they are available even when enforcement fails:

```text
unit-test-coverage-report.md
unit-test-coverage-report.json
unit-test-coverage-patch-proposal.md
unit-test-coverage-patch-proposal.json
coverage-reasoning-prompt.md
changed-files.txt
surefire-files.txt
jacoco-files.txt
```

## How to validate with PR #89

After this workflow is merged into `main`, update the validation branch:

```text
feature/coverage-validation-demo
```

by pushing any small commit that touches a trigger path, for example:

```text
orders-service/src/test/java/com/playground/ordersservice/app/OrderRiskClassifierTest.java
```

That should automatically trigger:

```text
Unit Test Coverage PR Agent
```

on PR #89.

Expected changed class mapping:

```text
orders-service/src/main/java/com/playground/ordersservice/app/OrderRiskClassifier.java
-> com.playground.ordersservice.app.OrderRiskClassifier
```

## Difference from manual workflow

Manual workflow:

```text
.github/workflows/unit-test-coverage-agent.yml
```

supports:

```text
workflow_dispatch
deterministic provider
optional langchain-openai provider
advisory reporting
```

PR workflow:

```text
.github/workflows/unit-test-coverage-pr-agent.yml
```

supports only:

```text
pull_request
deterministic provider
strict PR policy enforcement
```

This separation prevents accidental mixing of PR code, secrets, and LLM provider configuration.

## Affected-service detection and Maven failure evidence

The PR workflow now writes deterministic raw evidence files:

- `coverage-agent/raw/changed-files.txt`
- `coverage-agent/raw/affected-services.txt`
- `coverage-agent/raw/maven-failed-services.txt`

Affected services are detected from the git diff using the Unit Test Coverage Agent code. Behavior:

- Service-local changes in `production-java`, `test-java`, `build-config`, or `service-other` categories run Maven only for those services.
- Global coverage/agent/workflow/policy changes (`coverage-policy.yml`, `coverage-policy-pr.yml`, `.github/workflows/*`, `agents/unit_test_coverage_agent/*`) run Maven for all known services.
- Docs-only changes produce an empty `affected-services.txt`, so Maven verification is skipped.

`maven-failed-services.txt` is consumed by the report generator via `--test-execution-failures-file` and surfaced as structured `test_execution_failures` in JSON/Markdown output.

Strict PR policy (`coverage-policy-pr.yml`) now includes:

- `fail_on_maven_verification_failure: true`

When enabled, Maven verification failures become policy violations (not warnings), allowing enforcement to fail the PR check when test execution evidence is incomplete.

The workflow remains deterministic-only and read-only (no secrets, no OpenAI/LangChain, no write permissions, no PR comments, no code mutation).

## Surefire failure/error classification

The deterministic coverage agent now treats Surefire unit-test failures/errors as first-class evidence, not only as proof that reports exist.

Structured JSON contract fields include:

- `test_total_count`
- `test_failure_count`
- `test_error_count`
- `test_skipped_count`
- `failed_test_suites`

`failed_test_suites` is populated from Surefire suites where `failures > 0` or `errors > 0`.

## Strict policy behavior for failing tests

`coverage-policy-pr.yml` now includes:

- `fail_on_test_failures: true`

When enabled, any Surefire failure/error count produces a policy violation and policy enforcement fails the PR check.

When disabled (advisory mode), the same condition is reported as a policy warning.

Coverage evidence is not considered trustworthy for merge decisions when tests fail, even if raw coverage percentages are high.

## Report visibility

Generated JSON and Markdown artifacts now expose aggregate test execution counts and the list of failing Surefire suites.

Markdown includes a `Failed test suites` section with per-suite file/counts.

## Safety model remains unchanged

The PR workflow remains deterministic-only/read-only:

- no OpenAI/LangChain provider use
- no secrets
- no write permissions
- no PR comments
- no code mutation

## Branch coverage policy

The strict PR policy now enforces:

```yaml
minimum_branch_coverage_for_changed_classes: 60
```

Why this matters:

- Line coverage can be high while key conditional paths remain untested.
- Branch coverage adds explicit visibility into conditional-path testing quality.

Behavior details:

- The threshold is a numeric percentage in the 0..100 range.
- It applies only to changed production Java classes.
- It is enforced only when JaCoCo reports branch counters for the changed class.
- Classes with no branch counters (`missed=0`, `covered=0`) do not fail solely due to branch coverage.
- Under strict PR policy, a branch-coverage threshold miss is a policy violation and fails the coverage check.


## Related test heuristic

The agent now performs deterministic, naming-based related test matching for each changed production Java class.

It checks changed test files against expected candidates:
- `<ClassName>Test.java`
- `<ClassName>Tests.java`
- `<ClassName>IT.java`
- `<ClassName>IntegrationTest.java`

Strict policy key:

```yaml
require_related_test_change_when_production_code_changes: true
```

This heuristic improves PR hygiene but does not prove semantic test quality. JaCoCo coverage evidence remains the stronger execution signal.

## Changed source to JaCoCo mapping behavior

The changed-class mapper remains deterministic and read-only.

Strategy order:

1. `exact_class_name`
2. `nested_top_level_class`
3. `package_sourcefilename`
4. `sourcefilename_service_scoped`
5. `sourcefilename_unscoped` (only when unique)
6. `unmatched`

Exact class match is always preferred. If filename-based matches are ambiguous across classes/services, the result stays `unmatched` and coverage status remains `unknown` for safety.

The Markdown report now includes `Mapping` and `Confidence` columns plus a `Coverage mapping details` section with candidate classes for debugging.
