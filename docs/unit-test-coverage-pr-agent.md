# Unit Test Coverage PR Agent

## Purpose

This workflow automatically validates unit test coverage evidence for pull requests.

It exists because manual `workflow_dispatch` execution can be unreliable in GitHub UI/API. Pull request validation should not depend on manual dispatch.

## Workflow

```text
.github/workflows/unit-test-coverage-pr-agent.yml
```

## Trigger

```yaml
on:
  pull_request:
    paths:
      - "**/src/main/java/**"
      - "**/src/test/java/**"
      - "**/pom.xml"
      - "coverage-policy.yml"
      - "agents/unit_test_coverage_agent/**"
      - ".github/workflows/unit-test-coverage-pr-agent.yml"
```

## Security model

This workflow is intentionally limited:

```text
pull_request only
deterministic only
no OpenAI
no LangChain
no secrets
no PR comments
no write permissions
no code mutation
no commits
no PR creation
no deployment
```

Permissions:

```yaml
permissions:
  contents: read
  actions: read
```

## Flow

```text
pull request update
        |
        v
checkout PR code
        |
        v
validate coverage agent Python package
        |
        v
run Maven verify for services
        |
        v
generate deterministic coverage report
        |
        v
upload coverage artifacts
```

## Generated artifacts

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

## How to validate with PR #89

After this workflow is merged into `main`, update the validation branch:

```text
feature/coverage-validation-demo
```

by pushing any small commit.

That should automatically trigger:

```text
Unit Test Coverage PR Agent
```

on PR #89.

Expected changed class mapping:

```text
orders-service/src/main/java/com/playground/ordersservice/app/OrderRiskClassifier.java
-> com.playground.ordersservice.app.OrderRiskClassifier
```

## Difference from manual workflow

Manual workflow:

```text
.github/workflows/unit-test-coverage-agent.yml
```

supports:

```text
workflow_dispatch
deterministic provider
optional langchain-openai provider
```

PR workflow:

```text
.github/workflows/unit-test-coverage-pr-agent.yml
```

supports only:

```text
pull_request
deterministic provider
```

This separation prevents accidental mixing of PR code, secrets, and LLM provider configuration.
