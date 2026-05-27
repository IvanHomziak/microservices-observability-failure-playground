# Coverage Agent Branch Protection Requirements

## Purpose

This document defines the manual GitHub branch protection configuration required to make the Unit Test Coverage quality gate enforceable on `main`.

## Why branch protection is required

`Unit Test Coverage PR Agent` can fail on a pull request, but a failed check alone does not guarantee merge blocking.

GitHub only blocks merge when branch protection is configured to require that check.

Therefore, `Unit Test Coverage PR Agent` must be configured as a required status check on `main`.

## Required checks

Recommended minimum required checks:

- `Unit Test Coverage PR Agent`
- `Java Build Test`
- `PR Fast Feedback`
- `POC Safety Validation`

Optional but recommended checks:

- `Runtime Smoke`
- `Docker Compose Contracts`

## Manual setup steps

GitHub UI path:

```text
Settings -> Branches -> Branch protection rules -> main
```

Required configuration:

- Enable **Require a pull request before merging**.
- Enable **Require status checks to pass before merging**.
- Enable **Require branches to be up to date before merging**.
- Select required checks:
  - `Unit Test Coverage PR Agent`
  - `Java Build Test`
  - `PR Fast Feedback`
  - `POC Safety Validation`
- Do not allow bypass unless explicitly needed for repository admins.
- Optionally enable **Require conversation resolution before merging**.

## Validation procedure

After configuring branch protection:

1. Open a negative validation PR that should fail coverage policy.
2. Confirm `Unit Test Coverage PR Agent` fails.
3. Confirm merge is blocked.
4. Open a positive validation PR that should pass coverage policy.
5. Confirm `Unit Test Coverage PR Agent` passes.
6. Confirm merge is allowed.

## Troubleshooting

- If a check is not visible in required checks, run the workflow at least once on a PR.
- If a workflow does not start, verify path filters and trigger conditions.
- If a workflow fails before policy enforcement, inspect workflow logs.
- If a workflow passes a bad PR, inspect `.github/workflows/coverage-policy-pr.yml`.
- If GitHub allows merge despite a red check, branch protection is misconfigured.

## Safety boundary

- Branch protection is configured in GitHub repository settings, not by repository code.
- This documentation change only records required manual configuration.
- No secrets are required for this branch protection setup.
- No OpenAI or LangChain configuration is required for this branch protection setup.
