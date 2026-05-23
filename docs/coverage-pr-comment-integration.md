# Coverage PR Comment Integration

## Purpose

This document describes Story 6 for the Unit Test Coverage Agent: manually posting a coverage review comment to a pull request.

The integration is intentionally separated from the read-only coverage workflow because posting a PR comment requires write permission.

## Workflow

New workflow:

```text
.github/workflows/unit-test-coverage-pr-comment.yml
```

This workflow is manual-only:

```yaml
on:
  workflow_dispatch:
```

Manual inputs:

```text
pr_number
run_tests
provider
model
```

## Permissions

This workflow uses scoped write permissions only for commenting:

```yaml
permissions:
  contents: read
  actions: read
  pull-requests: write
  issues: write
```

The main `Unit Test Coverage Agent` workflow remains read-only.

## Flow

```text
manual workflow_dispatch
        |
        v
resolve PR base/head refs
        |
        v
checkout PR head commit
        |
        v
generate coverage artifacts
        |
        v
render comment from validated JSON artifacts
        |
        v
post PR comment with gh pr comment
```

## Generated artifacts

The workflow uploads:

```text
coverage-agent/output/unit-test-coverage-report.md
coverage-agent/output/unit-test-coverage-report.json
coverage-agent/output/unit-test-coverage-patch-proposal.md
coverage-agent/output/unit-test-coverage-patch-proposal.json
coverage-agent/output/coverage-reasoning-prompt.md
coverage-agent/output/pr-comment.md
coverage-agent/raw/pr.json
coverage-agent/raw/changed-files.txt
coverage-agent/raw/surefire-files.txt
coverage-agent/raw/jacoco-files.txt
```

## Comment rendering

The comment is rendered by:

```text
agents/unit_test_coverage_agent/src/unit_test_coverage_agent/pr_comment.py
```

It reads:

```text
unit-test-coverage-report.json
unit-test-coverage-patch-proposal.json
```

The coverage report JSON is validated using the local output schema before comment generation.

The workflow does not post raw model text.

## Safety model

The workflow must not:

- run automatically on `pull_request`;
- run on `pull_request_target`;
- mutate code;
- create commits;
- create PRs;
- deploy;
- enforce thresholds;
- delete or weaken tests;
- post raw unvalidated model output.

## Usage

Open GitHub Actions:

```text
Actions -> Unit Test Coverage PR Comment -> Run workflow
```

Inputs:

```text
pr_number: <PR number>
run_tests: true | false
provider: deterministic | langchain-openai
model: gpt-4.1-mini
```

Recommended first run:

```text
run_tests: false
provider: deterministic
```

Use `run_tests: true` when you want the workflow to generate Surefire and JaCoCo evidence before commenting.

Use `provider: langchain-openai` only after `OPENAI_API_KEY` is configured and you explicitly want LLM-based reasoning over the deterministic evidence contract.

## Current limitations

This implementation appends a new comment each time it runs.

A later improvement may update an existing comment using the marker:

```text
<!-- unit-test-coverage-agent-comment -->
```

That improvement should be implemented carefully to avoid editing unrelated user comments.
