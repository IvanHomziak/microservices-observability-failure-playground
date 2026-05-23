# Coverage PR Comment Integration

## Purpose

This document describes Story 6 for the Unit Test Coverage Agent: manually posting or updating a coverage review comment on a pull request.

The integration is intentionally separated from the read-only coverage workflow because posting or updating a PR comment requires write permission.

## Workflow

Workflow:

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
```

## Permissions

Top-level permissions are read-only:

```yaml
permissions:
  contents: read
```

The workflow is split into two jobs.

Evidence generation job:

```yaml
permissions:
  contents: read
  actions: read
```

Comment update job:

```yaml
permissions:
  contents: read
  actions: read
  pull-requests: write
  issues: write
```

The main `Unit Test Coverage Agent` workflow remains read-only.

## Security model

The workflow separates untrusted PR analysis from write-scoped commenting.

Evidence job:

```text
- uses trusted agent code from the default branch
- fetches PR head through refs/pull/<number>/head
- runs optional Maven tests in the PR worktree
- has no secrets
- has no PR/issue write permissions
- uses deterministic provider only
```

Comment job:

```text
- runs only after evidence job completes
- checks out trusted default-branch agent code
- downloads deterministic JSON artifacts
- validates coverage JSON before rendering the comment
- has PR/issue write permissions only for comment creation/update
- does not execute PR-head code
```

## Flow

```text
manual workflow_dispatch
        |
        v
checkout trusted default-branch agent code
        |
        v
fetch PR head via refs/pull/<number>/head
        |
        v
create isolated PR worktree
        |
        v
generate deterministic coverage artifacts without secrets/write credentials
        |
        v
upload artifacts
        |
        v
trusted comment job downloads artifacts
        |
        v
render comment from validated JSON artifacts
        |
        v
find existing bot comment by marker
        |
        v
update existing comment or create a new one
```

## Comment marker

The rendered comment includes a stable marker:

```text
<!-- unit-test-coverage-agent-comment -->
```

The workflow searches PR issue comments for this marker only in comments authored by:

```text
github-actions[bot]
```

If a matching comment is found, the workflow updates it.

If no matching comment is found, the workflow creates a new comment.

This avoids duplicate coverage comments across repeated manual runs.

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
- expose secrets to PR-head code;
- run PR-head code with PR/issue write permissions;
- mutate code;
- create commits;
- create PRs;
- deploy;
- enforce thresholds;
- delete or weaken tests;
- post raw unvalidated model output;
- edit comments that are not authored by `github-actions[bot]`;
- edit comments that do not contain the stable marker.

## Usage

Open GitHub Actions:

```text
Actions -> Unit Test Coverage PR Comment -> Run workflow
```

Inputs:

```text
pr_number: <PR number>
run_tests: true | false
```

Recommended first run:

```text
run_tests: false
```

Use `run_tests: true` when you want the workflow to generate Surefire and JaCoCo evidence before commenting.

LLM/LangChain reasoning is intentionally not available in this write-scoped comment workflow. Use the read-only `Unit Test Coverage Agent` workflow for optional LangChain analysis.

## Current limitations

The workflow updates only the first matching `github-actions[bot]` comment containing the marker.

It does not delete older duplicate comments if they already exist from previous versions of the workflow.