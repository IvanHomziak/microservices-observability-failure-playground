# Agentic GitHub Actions POC Demo Script

## Audience

This script is for a short technical or management-facing demo of the Agentic GitHub Actions POC.

Target duration:

```text
15-25 minutes
```

## Demo goal

Show that the repository now contains safe, evidence-first GitHub Actions agents that can:

- analyze CI failures;
- review changed-code test coverage;
- generate coverage artifacts;
- suggest test work;
- post or update a PR comment;
- evaluate configurable coverage policy;
- optionally enforce policy violations as a failing check.

## Key message

The POC is not an autonomous code-writing bot.

It is an evidence-first automation layer:

```text
repository evidence -> deterministic analysis -> optional LLM reasoning -> validated artifacts -> human review
```

## Opening explanation

Use this summary:

```text
We built two GitHub Actions agents.

The first agent analyzes failed CI runs and produces a reasoning report.

The second agent reviews whether changed Java production code is covered by tests. It reads Git diff, Surefire XML, JaCoCo XML, maps changed Java classes to coverage evidence, evaluates policy, generates patch proposal artifacts, and can post a validated PR comment.

The design is intentionally safe: no automatic code mutation, no auto-commits, no auto-PRs, no deployments, and no pull_request_target.
```

## Demo part 1: Repository structure

Show these paths:

```text
agents/ci_failure_reasoning_agent/
agents/unit_test_coverage_agent/
coverage-policy.yml
.github/workflows/ci-failure-reasoning-agent.yml
.github/workflows/unit-test-coverage-agent.yml
.github/workflows/unit-test-coverage-pr-comment.yml
.github/workflows/unit-test-coverage-policy-check.yml
docs/poc-validation-runbook.md
```

Explain:

```text
The agents are implemented as small Python packages with explicit JSON contracts and local validation.
```

## Demo part 2: Coverage policy

Open:

```text
coverage-policy.yml
```

Explain:

```text
This file defines repository-level expectations for changed-code coverage.
The policy is advisory by default but can be used by the optional enforcement workflow.
```

Highlight fields:

```text
minimum_line_coverage_for_changed_classes
minimum_method_coverage_for_changed_classes
require_test_changes_when_production_code_changes
fail_on_unknown_coverage
fail_on_missing_surefire_evidence
fail_on_missing_jacoco_evidence
```

## Demo part 3: Unit Test Coverage Agent workflow

Open:

```text
Actions -> Unit Test Coverage Agent -> Run workflow
```

Recommended demo inputs:

```text
base_ref: origin/main
head_ref: HEAD
run_tests: false
provider: deterministic
model: gpt-4.1-mini
```

Explain:

```text
This generates a deterministic coverage report and patch proposal artifacts without using secrets or LLM calls.
```

Show expected artifacts:

```text
unit-test-coverage-report.md
unit-test-coverage-report.json
unit-test-coverage-patch-proposal.md
unit-test-coverage-patch-proposal.json
coverage-reasoning-prompt.md
```

## Demo part 4: Optional LangChain reasoning

Only show this if `OPENAI_API_KEY` is configured.

Inputs:

```text
provider: langchain-openai
model: gpt-4.1-mini
```

Explain:

```text
LangChain receives only the deterministic evidence contract.
The model must return JSON.
The JSON is validated locally.
The final markdown report is rendered from validated JSON, not raw model text.
```

If not configured, say:

```text
The POC supports optional LangChain/OpenAI reasoning, but this demo will stay deterministic to avoid secrets dependency.
```

## Demo part 5: PR comment workflow

Open:

```text
Actions -> Unit Test Coverage PR Comment -> Run workflow
```

Inputs:

```text
pr_number: <open PR number>
run_tests: false
```

Explain:

```text
This workflow is split into two jobs.
The evidence job analyzes PR code with read-only permissions and no secrets.
The comment job has write permission only to post or update the PR comment, and it does not execute PR-head code.
```

Show expected marker in the PR comment:

```text
<!-- unit-test-coverage-agent-comment -->
```

Explain:

```text
Repeated runs update the existing bot comment instead of spamming duplicate comments.
```

## Demo part 6: Policy enforcement workflow

Open:

```text
Actions -> Unit Test Coverage Policy Check -> Run workflow
```

Inputs:

```text
base_ref: origin/main
head_ref: HEAD
run_tests: false
```

Explain:

```text
This workflow is still manual-only. It fails only when the validated coverage report contains policy_violations.
Warnings do not fail the job.
```

Emphasize:

```text
This is a candidate for a required check later, but it should not be enabled as branch protection until false positives are understood.
```

## Demo part 7: CI Failure Reasoning Agent

Open:

```text
Actions -> CI Failure Reasoning Agent -> Run workflow
```

Explain:

```text
This agent analyzes failed GitHub Actions runs and produces a failure reasoning report.
It supports deterministic reasoning and optional OpenAI reasoning.
```

## Safety slide narrative

Use this wording:

```text
The POC is intentionally not fully autonomous.
It does not write code, delete tests, commit changes, create PRs, or deploy.
The only write-scoped workflow is the manual PR comment workflow, and it isolates PR code execution from write credentials.
```

## Expected questions and answers

### Can the agent automatically fix missing tests?

Current answer:

```text
No. It generates an advisory patch proposal artifact. Automatic code generation and patch application are intentionally out of scope for this POC.
```

### Can this block PRs?

Current answer:

```text
Not by default. The policy check workflow can fail manually based on policy violations. It can become a required check later, after tuning and false-positive analysis.
```

### Does it use LLMs?

Current answer:

```text
LLM usage is optional. Deterministic mode works without secrets. LangChain/OpenAI mode is explicit opt-in and works over validated evidence contracts.
```

### Is it safe for fork PRs?

Current answer:

```text
The PR comment workflow fetches PR code through pull refs and runs PR-head code only in a read-only job without secrets or write permissions.
```

### What is missing for production?

Current answer:

```text
Production rollout would still need enterprise security review, observability, audit logging, cost tracking, approval workflow for LLM usage, branch protection strategy, and operational ownership.
```

## Demo closing

Close with:

```text
The POC proves the architecture: evidence-first agents inside GitHub Actions, safe defaults, optional LLM reasoning, validated artifacts, and human-controlled enforcement.

The next step is to run it on several real pull requests, collect false positives, tune coverage-policy.yml, and decide whether the policy check should become a required branch protection check.
```
