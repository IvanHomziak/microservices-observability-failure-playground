# Coverage Validation Negative Fixture (Missing Tests)

## Summary
This change is a **negative validation PR fixture** for the Unit Test Coverage PR Agent.

## Purpose
It intentionally adds production Java code without adding any corresponding Java test files.

## Expected failure
The expected result is that the workflow fails at **Enforce coverage policy**.

This PR is considered a successful validation artifact only when:
- Detect affected services succeeds.
- `affected-services.txt` contains `orders-service`.
- Maven verify runs for `orders-service`.
- Coverage report generation runs.
- Policy enforcement runs and fails due to coverage policy violations.

If the workflow fails earlier at service detection, this validation is invalid.
If the workflow fails due to Java compilation errors, the fixture must be corrected.

## Expected artifacts
Expected artifacts from the coverage workflow include:
- affected services output (`affected-services.txt`)
- Maven/verification logs for `orders-service`
- coverage report output
- policy enforcement output indicating violations
- PR comment output if comment publishing is enabled

## Do not merge
**Do not merge this PR.**

This PR must remain open/red as a validation artifact, or be closed after validation is complete.
