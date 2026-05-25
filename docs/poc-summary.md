# Agentic GitHub Actions POC Summary

## Executive summary

This POC implements safe, evidence-first GitHub Actions agents for software delivery workflows.

The POC focuses on two agent capabilities:

1. CI failure reasoning
2. Unit test coverage review for changed Java code

The implementation intentionally avoids unsafe autonomy. The agents do not mutate code, create commits, create pull requests, deploy, delete tests, or bypass human review.

## What was built

## 1. CI Failure Reasoning Agent

Purpose:

```text
failed GitHub Actions run -> evidence collection -> failure reasoning report
```

Capabilities:

- collect failed CI run evidence;
- generate deterministic failure analysis;
- optionally use OpenAI reasoning;
- output artifacts for human review.

## 2. Unit Test Coverage Agent

Purpose:

```text
changed Java code -> test/coverage evidence -> coverage assessment -> patch proposal -> optional PR comment/policy check
```

Capabilities:

- detect changed files through Git diff;
- classify production Java vs test Java changes;
- parse Surefire XML test evidence;
- parse JaCoCo XML coverage evidence;
- map changed Java source files to JaCoCo class coverage;
- detect partial, unknown, uncovered, and sufficient coverage;
- evaluate repository coverage policy;
- generate coverage reports;
- generate advisory patch proposal artifacts;
- optionally use LangChain/OpenAI for coverage reasoning;
- manually post or update PR comments from validated artifacts;
- optionally fail a manual policy check workflow when policy violations exist.

## Workflows created

| Workflow | Purpose |
|---|---|
| `ci-failure-reasoning-agent.yml` | Analyze CI failures |
| `unit-test-coverage-agent.yml` | Generate coverage report and patch proposal artifacts |
| `unit-test-coverage-pr-comment.yml` | Manually post/update a PR comment from validated coverage artifacts |
| `unit-test-coverage-policy-check.yml` | Optional deterministic policy enforcement workflow |

## Safety model

The POC follows these safety principles:

- deterministic mode works without secrets;
- LLM usage is explicit opt-in;
- LLM output must be validated JSON;
- markdown reports are rendered from validated JSON, not raw model text;
- no automatic code mutation;
- no automatic commits;
- no automatic pull request creation;
- no deployments;
- no `pull_request_target` usage;
- no secrets are exposed to PR-head code;
- PR-head code is not executed with write permissions;
- write permissions are isolated to manual PR comment update workflows.

## Evidence-first architecture

The agent design follows this pattern:

```text
repository evidence
    -> deterministic parser/collector
    -> validated JSON contract
    -> optional LLM reasoning
    -> local schema validation
    -> report/comment/artifact rendering
```

This reduces hallucination risk because the model does not invent repository facts. It can only reason over bounded evidence.

## Coverage policy

The repository now has a policy file:

```text
coverage-policy.yml
```

It defines expectations such as:

```text
minimum_line_coverage_for_changed_classes
minimum_method_coverage_for_changed_classes
require_test_changes_when_production_code_changes
fail_on_unknown_coverage
fail_on_missing_surefire_evidence
fail_on_missing_jacoco_evidence
```

The policy is advisory by default. It can also be used by the optional manual enforcement workflow.

## Business value

The POC demonstrates that agentic automation can reduce engineering review effort by:

- making CI failures easier to interpret;
- making changed-code test coverage visible;
- surfacing missing or weak tests earlier;
- creating consistent coverage review comments;
- reducing manual inspection of JaCoCo/Surefire artifacts;
- providing a safer path toward policy-based quality gates.

## What the POC does not do

The POC does not yet:

- generate Java test code automatically;
- apply patches;
- create commits;
- create pull requests;
- deploy changes;
- configure branch protection;
- maintain historical dashboards;
- track LLM cost;
- integrate LangSmith tracing;
- provide enterprise approval workflows for LLM usage.

## POC readiness

Current readiness estimate:

```text
Internal technical demo: 95%
Production rollout: 70%
```

The POC is suitable for internal demonstration and controlled experimentation.

It is not yet production-ready as an enforced enterprise quality gate.

## Recommended next steps

1. Run the POC on multiple real pull requests.
2. Compare agent output with human reviewer expectations.
3. Tune `coverage-policy.yml` to reduce false positives.
4. Decide which workflows should remain manual and which can become required checks.
5. Add audit/cost/observability controls before broader rollout.
6. Consider human-approved patch generation only after reporting quality is stable.

## Production rollout requirements

Before production use, add:

- formal security review;
- audit logging;
- workflow ownership model;
- approval model for LLM usage;
- cost telemetry;
- retention policy for artifacts;
- branch protection strategy;
- false-positive monitoring;
- operational runbook;
- incident handling process for agent failures.

## Final recommendation

Use this POC as a controlled internal demo and evaluation platform.

Do not immediately enable branch protection or automatic remediation.

First validate quality across real PRs, tune policy thresholds, and gather reviewer feedback.
