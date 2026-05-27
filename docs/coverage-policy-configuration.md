# Coverage Policy Configuration

## Purpose

This document describes the configurable policy layer for the Unit Test Coverage Agent.

The goal is to make the agent policy-driven instead of only descriptive.

The policy is advisory by default. It affects generated reports, patch proposals, and PR comments, but it does not configure GitHub branch protection or enforce merge blocking by itself.

## Policy file

Default file:

```text
coverage-policy.yml
```

Example:

```yaml
minimum_line_coverage_for_changed_classes: 70
minimum_method_coverage_for_changed_classes: 70
minimum_branch_coverage_for_changed_classes: 60
require_test_changes_when_production_code_changes: true
fail_on_unknown_coverage: false
fail_on_missing_surefire_evidence: false
fail_on_missing_jacoco_evidence: false
```

If the default `<repository-root>/coverage-policy.yml` file is absent, the agent uses built-in defaults.

If an explicit policy path is passed through:

```bash
--policy <path>
```

that file must exist. Missing explicit policy files fail fast to avoid silently using defaults after a typo.

## Supported settings

| Setting | Meaning |
|---|---|
| `minimum_line_coverage_for_changed_classes` | Minimum required line coverage percentage for changed Java classes |
| `minimum_method_coverage_for_changed_classes` | Minimum required method coverage percentage for changed Java classes |
| `minimum_branch_coverage_for_changed_classes` | Minimum required branch coverage percentage for changed Java classes when JaCoCo reports branch counters for that class |
| `require_test_changes_when_production_code_changes` | Adds a policy violation when production Java changes but no Java test files changed |
| `fail_on_unknown_coverage` | Turns unknown changed-class coverage into a policy violation instead of warning |
| `fail_on_missing_surefire_evidence` | Turns missing Surefire XML evidence into a policy violation instead of warning |
| `fail_on_missing_jacoco_evidence` | Turns missing JaCoCo XML evidence into a policy violation instead of warning |

## Parser constraints

The policy loader intentionally supports a small YAML subset:

```text
key: value
```

It does not require `PyYAML` or external dependencies.

Supported values:

```text
number: 0..100
boolean: true | false | yes | no | 1 | 0
```

Unknown keys fail fast.

Invalid percentages fail fast.

Invalid booleans fail fast.

Missing explicit policy files fail fast.

## Output contract additions

The coverage report JSON now includes:

```text
policy
policy_violations
policy_warnings
```

When policy violations exist, the agent reports:

```text
coverage_status: policy_violation
merge_recommendation: manual_review
```

## PR comment behavior

The PR comment includes:

```text
Policy violations: <count>
Policy warnings: <count>
```

and renders detailed policy findings when present.

## Safety boundary

This policy layer is still advisory.

It does not:

- mutate code;
- delete tests;
- create commits;
- create PRs;
- deploy;
- modify branch protection;
- prevent merge by itself;
- automatically remediate violations.

A future story may add a separate optional enforcement workflow, but that should be explicit and reviewed independently.

## Recommended rollout

Start with advisory values:

```yaml
fail_on_unknown_coverage: false
fail_on_missing_surefire_evidence: false
fail_on_missing_jacoco_evidence: false
```

Then tighten gradually after the evidence pipeline is stable.

Recommended later hardening:

```yaml
fail_on_missing_jacoco_evidence: true
fail_on_missing_surefire_evidence: true
fail_on_unknown_coverage: true
```

Only after this has proven reliable should branch protection or required checks be considered.


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
