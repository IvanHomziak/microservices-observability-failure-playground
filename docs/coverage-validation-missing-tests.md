# Coverage Validation Fixture (Negative PR)

## Purpose

This is a **negative validation PR**. It intentionally adds production Java code without adding matching Java tests to validate that the Unit Test Coverage PR Agent blocks non-compliant pull requests.

## Expected Outcome

- Expected result: workflow failure.
- Expected failure point: `Enforce coverage policy`.
- **DO NOT MERGE.**

## Invalid Validation Signals

- If failure happens at `Detect affected services`, this validation is invalid.
- If failure happens due to Java compilation errors, the fixture is broken and validation is invalid.

## Expected Artifacts

- `affected-services.txt`
- `changed-files.txt`
- `surefire-files.txt`
- `jacoco-files.txt`
- `unit-test-coverage-report.md`
- `unit-test-coverage-report.json`
- `unit-test-coverage-patch-proposal.md`
- `unit-test-coverage-patch-proposal.json`
- `pr-comment.md` (if enabled)

## Expected Workflow Path

1. Checkout pull request code -> success
2. Setup Java 21 -> success
3. Setup Python -> success
4. Validate coverage agent package -> success
5. Detect affected services -> success
6. `affected-services.txt` contains `orders-service`
7. Run Maven tests and JaCoCo reports for affected services -> success
8. Generate deterministic coverage report -> success
9. Enforce coverage policy -> failure
10. Upload coverage agent artifacts -> success

## Expected Policy Violations

At least one of:

- production Java files changed, but no Java test files changed
- changed production class has no related changed test file
- changed class has unknown coverage
- changed class coverage below line/method/branch threshold

## Validation Success Criteria

Successful validation means all of the following are true:

- workflow fails at `Enforce coverage policy`
- artifacts are uploaded
- GitHub branch protection blocks merge
- PR remains open/red or is later closed without merge

Validation is not successful if:

- workflow fails at `Detect affected services`
- workflow fails because Java does not compile
- workflow does not run
- PR can be merged despite failed Unit Test Coverage PR Agent
