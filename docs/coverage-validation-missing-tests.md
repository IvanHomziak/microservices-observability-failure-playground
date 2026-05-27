# Coverage validation (negative): missing tests

This branch intentionally adds production Java code without adding or modifying any Java test file.

## Purpose

This is a negative validation PR for the Unit Test Coverage PR Agent. It is expected to fail strict coverage/test-change policy checks.

This PR should not be treated as a real production feature.

## Expected violations

- Production Java files changed, but no Java test files changed.
- Related test file missing (if related-test heuristic from PR-4 is enabled).
- Unknown or insufficient coverage for the changed class, depending on JaCoCo mapping/evidence.

## Expected artifacts

- `unit-test-coverage-report.md`
- `unit-test-coverage-report.json`
- `unit-test-coverage-patch-proposal.md`
- `changed-files.txt`
- `affected-services.txt`
- `surefire-files.txt`
- `jacoco-files.txt`
