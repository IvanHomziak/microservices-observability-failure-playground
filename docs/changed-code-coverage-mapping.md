# Changed-code Coverage Mapping

## Purpose

This document describes Story 3 for the Unit Test Coverage Agent: mapping changed Java production files to JaCoCo class-level and method-level coverage evidence.

The goal is to make the coverage report precise enough for a future LangChain reasoning layer.

## Problem

The initial coverage agent could say whether a changed class looked covered, uncovered, or unknown, but it did not expose enough detail:

- which changed source file mapped to which JaCoCo class;
- whether the class was fully covered or only partially covered;
- line/method/branch coverage percentages;
- which methods appear uncovered.

Without this mapping, an LLM would have to infer too much from raw evidence.

## New mapping flow

```text
changed Java source file
        |
        v
expected Java class name
        |
        v
JaCoCo class entry
        |
        v
class status + percentages + uncovered methods
```

Example:

```text
orders-service/src/main/java/com/example/OrderService.java
        -> com.example.OrderService
        -> com/example/OrderService in jacoco.xml
```

## New JSON fields

The coverage report now includes:

```text
changed_class_coverage
partially_covered_classes
```

Each `changed_class_coverage` item contains:

```text
source_file
service
expected_class_name
matched_class_name
report_file
status
line_coverage_percent
branch_coverage_percent
method_coverage_percent
lines_covered
lines_missed
methods_covered
methods_missed
uncovered_methods
```

## Class status values

```text
covered
partial
uncovered
unknown
```

## Overall coverage status values

```text
sufficient
partial
insufficient
unknown
not_applicable
```

## Method-level evidence

The JaCoCo loader now parses method counters from `jacoco.xml`.

A method is reported as uncovered when it has executable counters but no covered instructions and no covered lines.

Constructors and class initializers are ignored for uncovered-method recommendations:

```text
<init>
<clinit>
```

## Safety model

This remains an advisory report.

The agent does not:

- mutate code;
- generate tests automatically;
- create PRs;
- enforce thresholds;
- deploy anything.

## Why this matters before LangChain

LangChain should reason over structured facts, not raw guesses.

This story makes the deterministic evidence contract strong enough for the next step:

```text
validated coverage evidence -> LangChain reasoning -> validated recommendation
```
