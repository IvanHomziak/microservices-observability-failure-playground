# Agentic GitHub Actions POC Validation Runbook

## Purpose

This runbook explains how to validate the Agentic GitHub Actions POC end to end.

The POC contains two main agents:

```text
CI Failure Reasoning Agent
Unit Test Coverage Agent
```

and supporting workflows for coverage reports, PR comments, patch proposal artifacts, and optional policy enforcement.

## Current POC scope

The POC demonstrates:

- deterministic CI failure analysis;
- optional OpenAI reasoning for CI failures;
- changed-code unit test coverage review;
- Surefire XML parsing;
- JaCoCo XML parsing;
- changed Java class coverage mapping;
- optional LangChain/OpenAI coverage reasoning;
- test patch proposal artifacts;
- manual PR coverage comments;
- configurable coverage policy;
- optional deterministic policy enforcement.

## Safety boundaries

The POC must not:

- use `pull_request_target`;
- expose secrets to untrusted pull request code;
- run PR-head code with write permissions;
- mutate code automatically;
- create commits automatically;
- create pull requests automatically;
- deploy anything;
- delete or weaken tests;
- post raw unvalidated model output.

## Workflows to validate

| Workflow | File | Purpose | Expected permission model |
|---|---|---|---|
| CI Failure Reasoning Agent | `.github/workflows/ci-failure-reasoning-agent.yml` | Analyze failed CI runs | Read-oriented; OpenAI only when explicitly selected |
| Unit Test Coverage Agent | `.github/workflows/unit-test-coverage-agent.yml` | Generate coverage report and patch proposal artifacts | Read-only |
| Unit Test Coverage PR Comment | `.github/workflows/unit-test-coverage-pr-comment.yml` | Manually post or update PR comment from validated artifacts | Split jobs: read-only evidence, write-scoped comment update |
| Unit Test Coverage Policy Check | `.github/workflows/unit-test-coverage-policy-check.yml` | Optional deterministic enforcement of policy violations | Read-only, deterministic-only |

## Required repository setup

### Required for deterministic mode

No repository secrets are required.

### Required for optional OpenAI/LangChain modes

Configure repository or environment secret:

```text
OPENAI_API_KEY
```

Optional model input defaults to:

```text
gpt-4.1-mini
```

Do not use OpenAI/LangChain mode in write-scoped PR comment workflows.

## Validation sequence

Run the validation in this order.

## Step 1: Validate Python agent packages through existing workflows

Open GitHub Actions and run:

```text
Actions -> Unit Test Coverage Agent -> Run workflow
```

Recommended inputs:

```text
base_ref: origin/main
head_ref: HEAD
run_tests: false
provider: deterministic
model: gpt-4.1-mini
```

Expected result:

```text
workflow completes successfully
agent package compiles
unit tests pass
coverage artifacts are uploaded
```

Expected artifacts:

```text
unit-test-coverage-report.md
unit-test-coverage-report.json
unit-test-coverage-patch-proposal.md
unit-test-coverage-patch-proposal.json
coverage-reasoning-prompt.md
changed-files.txt
surefire-files.txt
jacoco-files.txt
```

## Step 2: Validate Unit Test Coverage Agent with test execution

Run the same workflow again with:

```text
run_tests: true
provider: deterministic
```

Expected result:

```text
Maven verify runs for Java services
Surefire XML files are collected when tests exist
JaCoCo XML files are collected when coverage reports are generated
coverage report includes policy findings
```

Expected JaCoCo path per service:

```text
<service>/target/site/jacoco/jacoco.xml
```

Expected Surefire path per service:

```text
<service>/target/surefire-reports/TEST-*.xml
```

## Step 3: Validate optional LangChain coverage reasoning

Only run this if `OPENAI_API_KEY` is configured.

Open:

```text
Actions -> Unit Test Coverage Agent -> Run workflow
```

Inputs:

```text
run_tests: true
provider: langchain-openai
model: gpt-4.1-mini
```

Expected result:

```text
LangChain dependencies are installed only for this mode
LLM receives deterministic coverage evidence contract
LLM returns JSON only
JSON is validated locally
Markdown report is rendered from validated JSON
```

Failure expectations:

```text
missing OPENAI_API_KEY -> workflow fails
invalid model JSON -> workflow fails closed
```

## Step 4: Validate PR comment workflow

Open:

```text
Actions -> Unit Test Coverage PR Comment -> Run workflow
```

Inputs:

```text
pr_number: <open PR number>
run_tests: false
```

Expected result:

```text
workflow resolves PR base/head refs
trusted default-branch agent code is used
PR head is fetched via refs/pull/<number>/head
coverage artifacts are generated without secrets or write permissions
comment job downloads validated artifacts
comment job posts or updates one github-actions[bot] comment
```

Expected PR comment marker:

```text
<!-- unit-test-coverage-agent-comment -->
```

Repeated runs should update the existing bot comment instead of creating duplicates.

## Step 5: Validate policy enforcement workflow

Open:

```text
Actions -> Unit Test Coverage Policy Check -> Run workflow
```

Recommended first inputs:

```text
base_ref: origin/main
head_ref: HEAD
run_tests: false
```

Expected behavior:

```text
policy_violations empty -> workflow passes
policy_violations non-empty -> workflow fails
policy_warnings do not fail the workflow
artifacts are uploaded even when enforcement fails
```

Expected enforcement CLI:

```text
python -m unit_test_coverage_agent.enforce_policy --coverage-json coverage-agent/output/unit-test-coverage-report.json
```

## Step 6: Validate CI Failure Reasoning Agent

Open:

```text
Actions -> CI Failure Reasoning Agent -> Run workflow
```

Recommended deterministic mode:

```text
provider: deterministic
```

Expected result:

```text
failed workflow run evidence is collected
reasoning report is generated
artifacts are uploaded
no write permissions are required
```

Optional OpenAI mode requires:

```text
OPENAI_API_KEY
```

## How to interpret coverage status

| Status | Meaning |
|---|---|
| `sufficient` | Changed class coverage appears sufficient according to available evidence and policy |
| `partial` | Changed classes have some coverage but not complete coverage |
| `insufficient` | Changed classes appear uncovered or materially under-covered |
| `unknown` | Evidence is missing or cannot be mapped |
| `policy_violation` | Coverage evidence violates configured repository policy |
| `not_applicable` | No changed production Java files detected |

## How to interpret merge recommendation

| Recommendation | Meaning |
|---|---|
| `approve` | No deterministic blocker found |
| `manual_review` | Human review required; evidence is missing, partial, or violates advisory policy |
| `block` | Strong deterministic evidence indicates insufficient coverage |

## Expected POC artifacts

Across all workflows, expected artifacts include:

```text
unit-test-coverage-report.md
unit-test-coverage-report.json
unit-test-coverage-patch-proposal.md
unit-test-coverage-patch-proposal.json
coverage-reasoning-prompt.md
pr-comment.md
changed-files.txt
surefire-files.txt
jacoco-files.txt
maven-failed-services.txt
```

Some artifacts are conditional and appear only when the workflow path creates them.

## Known limitations

The POC does not yet provide:

- automatic Java test generation;
- automatic patch application;
- automatic PR creation;
- branch protection configuration;
- historical dashboard;
- cost telemetry;
- LangSmith tracing;
- enterprise approval workflow for LLM usage;
- full production observability.

## POC completion criteria

The POC can be considered complete when:

- all four main workflows can be triggered manually;
- deterministic Unit Test Coverage Agent produces valid artifacts;
- PR comment workflow posts or updates one validated comment;
- policy check workflow passes/fails according to `policy_violations`;
- CI Failure Reasoning Agent produces a report for a failed run;
- safety checks show no `pull_request_target` usage;
- no workflow exposes secrets to PR-head code;
- the team can follow this runbook without additional explanation.
