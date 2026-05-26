# Coverage Validation Demo Feature

## Purpose

This branch contains a small synthetic feature used to validate the Unit Test Coverage Agent report.

The goal is to create a safe and deterministic diff containing:

```text
orders-service/src/main/java/.../OrderRiskClassifier.java
orders-service/src/test/java/.../OrderRiskClassifierTest.java
```

This allows the coverage agent to verify:

- changed production Java file detection;
- changed test Java file detection;
- Surefire XML collection;
- JaCoCo XML collection;
- changed-code-to-coverage mapping;
- patch proposal behavior;
- coverage policy behavior;
- PR comment rendering.

## Feature

The demo feature adds:

```text
OrderRiskClassifier
```

It classifies an order as:

```text
LOW
MEDIUM
HIGH
```

based on amount and currency.

## Why this is intentionally simple

The class is pure Java and has no dependencies on:

- Spring context;
- database;
- Kafka;
- HTTP clients;
- Testcontainers;
- external services.

This makes it suitable for stable CI validation of Surefire and JaCoCo artifacts.

## How to validate

Run:

```text
Actions -> Unit Test Coverage Agent -> Run workflow
```

Inputs:

```text
base_ref: origin/main
head_ref: HEAD
run_tests: true
provider: deterministic
```

Expected changed files:

```text
orders-service/src/main/java/com/playground/ordersservice/app/OrderRiskClassifier.java
orders-service/src/test/java/com/playground/ordersservice/app/OrderRiskClassifierTest.java
```

Expected artifacts:

```text
unit-test-coverage-report.md
unit-test-coverage-report.json
unit-test-coverage-patch-proposal.md
unit-test-coverage-patch-proposal.json
changed-files.txt
surefire-files.txt
jacoco-files.txt
orders-service/target/surefire-reports/TEST-*.xml
orders-service/target/site/jacoco/jacoco.xml
```

## Expected report behavior

The report should map:

```text
OrderRiskClassifier.java -> com.playground.ordersservice.app.OrderRiskClassifier
```

and show real line/method coverage from JaCoCo.

The policy behavior depends on the generated percentages and `coverage-policy.yml`.

## Important

This branch exists only for POC validation.

It is not intended as a business feature for production.
