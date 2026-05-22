# Agentic CI/CD POC

## Purpose

This document explains the CI/CD workflow model used by this repository after splitting the original monolithic `ci.yml` into dedicated GitHub Actions workflows.

The goal of this POC is not to remove YAML from GitHub Actions entirely. GitHub Actions still requires workflow files under `.github/workflows/`.

The goal is to demonstrate CI/CD without manually maintaining large YAML pipelines by hand: an agent can propose or update focused workflow files, while GitHub Actions executes deterministic validation and a human reviews the resulting pull request.

## Core idea

The operating model is:

```text
Human intent -> Agent proposes/changes repository files -> GitHub Actions validates -> Human reviews and merges
```

The agent does not replace GitHub Actions.

The agent writes or updates workflow logic. GitHub Actions executes the workflow logic.

## Repository context

This repository is a deterministic microservices failure playground for AI diagnostics workflows.

The CI/CD model must protect:

- deterministic scenario behavior;
- verifier scripts;
- Docker Compose runtime contracts;
- evidence generation for diagnostics agents;
- documentation alignment;
- safe PR validation boundaries.

See `AGENTS.md` for mandatory repository-level instructions for AI agents and coding assistants.

## Workflow inventory

| Workflow | File | Trigger model | Purpose |
|---|---|---|---|
| PR Fast Feedback | `.github/workflows/pr-fast-feedback.yml` | PR / push / manual | Fast repository structure, script syntax, Compose, and workflow-safety checks |
| Java Build Test | `.github/workflows/java-build-test.yml` | PR / push / manual | Maven test matrix for Java services |
| Docker Compose Contracts | `.github/workflows/compose-contracts.yml` | PR / push / manual | Docker Compose base, scenario override, and profile contract validation |
| Runtime Smoke | `.github/workflows/runtime-smoke.yml` | PR / push / manual, path-limited | Starts default runtime and runs `verify-milestone-1.sh` |
| Readiness Gate | `.github/workflows/readiness-gate.yml` | manual-only | Runs full deterministic readiness verification |
| Agentic CI/CD Planner | `.github/workflows/agentic-cicd-planner.yml` | manual-only | Generates repository context and CI/CD planning artifact |

## Automatic PR validation workflows

The following workflows are appropriate as automatic PR checks after they are stable:

1. `pr-fast-feedback.yml`
2. `java-build-test.yml`
3. `compose-contracts.yml`
4. `runtime-smoke.yml`

These workflows are designed to provide useful validation while remaining safe for PR execution.

They must not use secrets, deploy, publish Docker images, mutate cloud infrastructure, or auto-merge code.

## Manual-only workflows

The following workflows should remain manual-only unless explicitly promoted by a human decision:

1. `readiness-gate.yml`
2. `agentic-cicd-planner.yml`

### Why Readiness Gate is manual-only

`readiness-gate.yml` runs full deterministic readiness verification through `scripts/verify-readiness.sh`.

That script may execute many scenario verifiers, including synchronous, Kafka, async, and observability paths. It is too heavy to be required on every PR by default.

### Why Agentic Planner is manual-only

`agentic-cicd-planner.yml` is advisory. It generates a repository context and CI/CD planning artifact.

It should not block ordinary PRs, and it should not mutate code automatically.

## Required check recommendation

Recommended required checks for branch protection:

- PR Fast Feedback
- Java Build Test
- Docker Compose Contracts
- Runtime Smoke

Do not require:

- Readiness Gate
- Agentic CI/CD Planner

Those are manual workflows.

## Agent usage model

The agent should use the workflows as feedback, not as hidden magic.

Example loop:

```text
1. Human asks the agent to add or improve a CI/CD workflow.
2. Agent reads repository evidence: AGENTS.md, workflows, scripts, Docker Compose, scenario docs.
3. Agent makes a small change in a branch.
4. GitHub Actions runs automatic checks.
5. If a check fails, the agent inspects the failed job logs and artifacts.
6. Agent proposes or commits a targeted fix.
7. Human reviews the final PR and merges only after acceptable validation.
```

## Safety boundaries

PR workflows must remain safe for untrusted code.

They must not:

- use `pull_request_target`;
- read secrets;
- deploy;
- publish images;
- mutate cloud infrastructure;
- auto-merge;
- run PR comments or issue text as shell commands;
- grant broad write permissions.

Default workflow permission should be:

```yaml
permissions:
  contents: read
```

Escalated permissions require explicit justification in the PR description.

## Why the legacy `ci.yml` was removed

The old `.github/workflows/ci.yml` mixed several responsibilities in one file:

- Java build/test;
- shell validation;
- Docker Compose validation.

Those responsibilities are now covered by dedicated workflows.

Removing the legacy workflow reduces duplicate checks, lowers CI noise, and makes the workflow model easier for humans and agents to reason about.

## Validation strategy

Use the smallest meaningful validation first:

1. Static shell validation: `bash -n scripts/*.sh`
2. Base Compose validation: `docker compose config`
3. Scenario Compose override validation
4. Java tests for affected services
5. Runtime smoke: `./scripts/verify-milestone-1.sh`
6. Scenario-specific verifier
7. Full readiness gate: `./scripts/verify-readiness.sh`

## Known limitations

This POC does not yet implement a fully autonomous agent that creates PRs from inside GitHub Actions.

The current safe model is:

- agent-assisted workflow authoring and review;
- deterministic GitHub Actions validation;
- manual human approval;
- manual agentic planning artifact generation.

A future version may add controlled PR creation by an agent, but only after explicit review of permissions, token scope, prompt-injection risks, and branch protection behavior.

## Future evolution

Possible next steps:

1. Add a report artifact summarizing CI/CD health across all dedicated workflows.
2. Add a non-mutating diagnostics workflow that analyzes failed workflow logs and produces a markdown report.
3. Add controlled issue-to-plan automation, treating issue text as untrusted input.
4. Add protected release workflows only if image publication or deployment becomes necessary.
5. Add documentation that maps each failure scenario to its expected evidence and CI verification coverage.
