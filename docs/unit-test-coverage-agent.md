# Unit Test Coverage Agent

## Purpose

The Unit Test Coverage Agent evaluates whether changed Java production code has enough test and coverage evidence.

The first version is deterministic-only. It intentionally does not use LangChain or an LLM yet.

The goal is to build the evidence foundation first:

```text
changed files -> Surefire evidence -> JaCoCo evidence -> validated coverage report
```

LangChain reasoning will be added in a later story after the evidence contract is stable.

## Current scope

This version:

- reads changed files from Git diff;
- classifies changed files;
- parses Surefire XML reports if present;
- parses JaCoCo XML reports if present;
- generates `unit-test-coverage-report.md`;
- generates `unit-test-coverage-report.json`;
- runs from a manual GitHub Actions workflow;
- does not call an LLM;
- does not mutate code;
- does not create PRs.

## GitHub Actions workflow

Workflow:

```text
.github/workflows/unit-test-coverage-agent.yml
```

Manual inputs:

```text
base_ref: origin/main
head_ref: HEAD
run_tests: false | true
```

Permissions:

```yaml
contents: read
actions: read
```

## How to run

Open GitHub Actions:

```text
Actions -> Unit Test Coverage Agent -> Run workflow
```

Recommended first run:

```text
base_ref: origin/main
head_ref: HEAD
run_tests: false
```

Use `run_tests: true` only when you want the workflow to attempt Maven test execution before collecting Surefire reports.

## Artifacts

The workflow uploads:

```text
unit-test-coverage-report.md
unit-test-coverage-report.json
changed-files.txt
surefire-files.txt
jacoco-files.txt
TEST-*.xml when present
jacoco.xml when present
```

## Output contract

Main fields:

```text
schema_version
coverage_status
changed_production_files
changed_test_files
changed_services
surefire_reports_found
jacoco_reports_found
covered_classes
uncovered_classes
unknown_coverage_files
missing_test_scenarios
recommended_tests
confidence
blocking_reasons
merge_recommendation
safety_boundary
```

## Status values

Coverage status:

```text
sufficient
insufficient
unknown
not_applicable
```

Merge recommendation:

```text
approve
block
manual_review
```

Confidence:

```text
low
medium
high
```

## Important limitation

If JaCoCo XML is missing, the agent must report coverage as `unknown`. It must not infer coverage from code text alone.

## LangChain roadmap

LangChain will be added later as a reasoning layer over validated evidence.

The intended future flow is:

```text
deterministic evidence -> validated JSON -> LangChain reasoning -> validated JSON -> markdown report
```

LangChain must not replace deterministic evidence collection.
