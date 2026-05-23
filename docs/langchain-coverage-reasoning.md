# LangChain Coverage Reasoning Layer

## Purpose

This document describes Story 4 for the Unit Test Coverage Agent: adding an optional LangChain reasoning layer over deterministic coverage evidence.

The goal is not to let an LLM guess coverage.

The goal is:

```text
deterministic evidence -> validated JSON contract -> LangChain reasoning -> validated JSON contract -> markdown report
```

## Providers

Supported providers:

```text
deterministic
langchain-openai
```

Default:

```text
deterministic
```

`deterministic` performs no external call.

`langchain-openai` is explicit opt-in and requires:

```text
OPENAI_API_KEY
```

Optional model override:

```text
OPENAI_MODEL
```

Default model:

```text
gpt-4.1-mini
```

## Runtime behavior

The agent always builds deterministic coverage evidence first.

That evidence includes:

- changed files;
- changed production files;
- changed test files;
- changed services;
- Surefire report count;
- JaCoCo report count;
- changed class coverage mapping;
- covered classes;
- partially covered classes;
- uncovered classes;
- unknown coverage files;
- missing test scenarios;
- recommended tests;
- merge recommendation;
- safety boundary.

Then the selected provider receives this contract.

The LangChain provider may refine recommendations only when supported by the deterministic evidence.

## Prompt artifact

The workflow writes:

```text
coverage-reasoning-prompt.md
```

This file is an audit artifact showing the bounded prompt sent to the optional LangChain provider.

## Validation model

The LangChain provider must return JSON only.

The response is parsed and validated against the local coverage output schema.

If validation fails, the workflow fails closed.

Markdown is rendered from validated JSON only.

Raw model text is never trusted as the final report.

## GitHub Actions workflow

Workflow:

```text
.github/workflows/unit-test-coverage-agent.yml
```

Manual inputs:

```text
base_ref
head_ref
run_tests
provider
model
```

Permissions remain read-only:

```yaml
contents: read
actions: read
```

## How to run deterministic mode

```text
Actions -> Unit Test Coverage Agent -> Run workflow
provider: deterministic
run_tests: true
```

## How to run LangChain mode

First configure repository or environment secret:

```text
OPENAI_API_KEY
```

Then run:

```text
Actions -> Unit Test Coverage Agent -> Run workflow
provider: langchain-openai
model: gpt-4.1-mini
run_tests: true
```

## Safety constraints

The LangChain provider must not:

- invent files, classes, methods, tests, coverage percentages, or validation results;
- mutate code;
- create commits;
- create PRs;
- delete tests;
- weaken verification;
- deploy;
- access write permissions;
- use `pull_request_target`.

## Current limitations

This layer is advisory only.

It does not:

- generate test code;
- create patch proposals;
- comment on PRs;
- enforce coverage thresholds;
- block merges automatically.

## Next story

Next step:

```text
Story 5: Patch proposal artifact
```

The agent should propose what tests to add, but still without committing changes automatically.
