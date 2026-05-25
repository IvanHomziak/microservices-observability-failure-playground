# Coverage Policy Enforcement Workflow

## Purpose

This document describes the optional policy enforcement workflow for the Unit Test Coverage Agent.

The advisory coverage workflow reports policy violations.

The enforcement workflow turns policy violations into a failing GitHub Actions job.

## Workflow

Workflow:

```text
.github/workflows/unit-test-coverage-policy-check.yml
```

Trigger:

```yaml
on:
  workflow_dispatch:
```

Inputs:

```text
base_ref
head_ref
run_tests
```

## Runtime model

The workflow is deterministic-only.

It does not use:

- LangChain;
- OpenAI;
- secrets;
- PR comments;
- write permissions;
- deployments.

## Permissions

```yaml
permissions:
  contents: read
  actions: read
```

## Flow

```text
checkout repository
        |
        v
validate coverage agent package
        |
        v
optionally run Maven verify for service coverage evidence
        |
        v
generate deterministic coverage report
        |
        v
validate coverage JSON contract
        |
        v
fail job if policy_violations is not empty
```

## Enforcement logic

Implemented in:

```text
agents/unit_test_coverage_agent/src/unit_test_coverage_agent/enforce_policy.py
```

The enforcement CLI reads:

```text
coverage-agent/output/unit-test-coverage-report.json
```

It validates the JSON contract using the local output schema.

Then it checks:

```text
policy_violations
```

If `policy_violations` is empty:

```text
exit code 0
```

If `policy_violations` has at least one item:

```text
exit code 1
```

Policy warnings do not fail the job.

## Artifacts

Artifacts are uploaded even when enforcement fails:

```text
coverage-agent/output/unit-test-coverage-report.md
coverage-agent/output/unit-test-coverage-report.json
coverage-agent/output/unit-test-coverage-patch-proposal.md
coverage-agent/output/unit-test-coverage-patch-proposal.json
coverage-agent/output/coverage-reasoning-prompt.md
coverage-agent/raw/changed-files.txt
coverage-agent/raw/surefire-files.txt
coverage-agent/raw/jacoco-files.txt
*/target/surefire-reports/TEST-*.xml
*/target/site/jacoco/jacoco.xml
```

## Safety boundary

This workflow does not:

- mutate code;
- delete tests;
- create commits;
- create pull requests;
- post comments;
- deploy;
- access secrets;
- use write permissions;
- use `pull_request_target`.

## Recommended rollout

Start with manual runs only.

Recommended sequence:

1. Run manually against a known PR or branch.
2. Review artifacts.
3. Tune `coverage-policy.yml`.
4. Run in advisory mode for several PRs.
5. Only then consider making it a required check.

Do not enable required branch protection until false positives are understood.
