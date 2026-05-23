# JaCoCo Coverage Enablement

## Purpose

This document describes Story 2 for the Unit Test Coverage Agent: enabling JaCoCo XML coverage evidence for Java services.

The Unit Test Coverage Agent must reason from factual coverage evidence, not from code guesses.

JaCoCo XML is the primary evidence source for changed-code coverage.

## Services updated

JaCoCo Maven plugin was added to:

```text
api-gateway
orders-service
payments-service
inventory-service
notification-service
audit-service
```

## Maven configuration

Each service now defines:

```xml
<jacoco.version>0.8.12</jacoco.version>
```

and configures:

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>${jacoco.version}</version>
    <executions>
        <execution>
            <id>prepare-agent</id>
            <goals>
                <goal>prepare-agent</goal>
            </goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>verify</phase>
            <goals>
                <goal>report</goal>
            </goals>
        </execution>
    </executions>
</plugin>
```

## Expected output

After running:

```bash
mvn -B -ntp verify
```

service-level coverage XML should be available at:

```text
target/site/jacoco/jacoco.xml
```

The coverage agent reads these files using:

```text
*/target/site/jacoco/jacoco.xml
```

## Workflow update

The `Unit Test Coverage Agent` workflow now uses `mvn verify` when `run_tests=true`.

This produces both:

```text
target/surefire-reports/TEST-*.xml
target/site/jacoco/jacoco.xml
```

The workflow continues even if one service fails tests, so it can still collect partial evidence from other services.

Failed services are recorded in:

```text
coverage-agent/raw/maven-failed-services.txt
```

when present.

## Current limitations

This story does not add hard coverage thresholds.

It does not fail PRs because of low coverage.

The current goal is evidence generation, not enforcement.

Threshold enforcement should be a later story after the evidence quality is stable.

## Recommended local validation

For one service:

```bash
cd orders-service
mvn -B -ntp verify
ls target/site/jacoco/jacoco.xml
```

For the workflow:

```text
Actions -> Unit Test Coverage Agent -> Run workflow
run_tests: true
```

Expected artifact includes:

```text
unit-test-coverage-report.md
unit-test-coverage-report.json
jacoco-files.txt
surefire-files.txt
*/target/site/jacoco/jacoco.xml
*/target/surefire-reports/TEST-*.xml
```
