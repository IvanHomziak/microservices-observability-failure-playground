# Coverage Patch Proposal Artifact

## Purpose

This document describes Story 5 for the Unit Test Coverage Agent: generating an advisory patch proposal artifact.

The goal is to suggest what tests should be added or improved based on validated coverage evidence.

The agent must not apply patches automatically.

## Flow

```text
coverage report contract
        |
        v
patch proposal generator
        |
        v
unit-test-coverage-patch-proposal.md
unit-test-coverage-patch-proposal.json
```

## Generated artifacts

The workflow now uploads:

```text
coverage-agent/output/unit-test-coverage-patch-proposal.md
coverage-agent/output/unit-test-coverage-patch-proposal.json
```

These artifacts are generated alongside:

```text
coverage-agent/output/unit-test-coverage-report.md
coverage-agent/output/unit-test-coverage-report.json
coverage-agent/output/coverage-reasoning-prompt.md
```

## Proposal content

Each proposed test scenario includes:

```text
production_class
source_file
suggested_test_file
suggested_test_class
suggested_test_methods
rationale
```

The proposal also includes:

```text
validation_commands
notes
safety_boundary
```

## When proposals are generated

A test proposal is generated for changed production classes with status:

```text
unknown
uncovered
partial
```

No proposal is generated for classes with status:

```text
covered
```

## Example proposal

For:

```text
orders-service/src/main/java/com/example/OrderService.java
```

The agent may suggest:

```text
orders-service/src/test/java/com/example/OrderServiceTest.java
```

and methods such as:

```text
shouldCoverCancelOrder
shouldRejectInvalidInputForOrderService
shouldHandleFailurePathForOrderService
```

## Validation commands

Validation commands are generated per changed service, for example:

```bash
cd orders-service && mvn -B -ntp verify
```

## Safety boundary

The proposal is advisory only.

It does not authorize:

- code mutation;
- test deletion;
- commit creation;
- PR creation;
- deployment;
- secrets access;
- workflow permission escalation;
- automatic remediation.

## Current limitations

This story does not generate real Java test code.

It does not produce a git patch.

It does not comment on PRs.

It does not enforce coverage thresholds.

## Next story

Next step:

```text
Story 6: PR comment integration
```

That should remain manual/trusted-branch only and post comments from validated artifacts, not raw model text.
