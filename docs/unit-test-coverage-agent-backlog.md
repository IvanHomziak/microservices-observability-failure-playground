# Unit Test Coverage Agent Backlog

## Goal

Build an agent that evaluates whether changed production code is adequately covered by unit or integration tests.

The agent must be evidence-first:

```text
changed code -> deterministic evidence -> coverage reasoning -> validated report
```

It must not guess coverage from code text alone.

## Story 1: Deterministic coverage evidence scaffold

As an engineer, I want a deterministic coverage evidence pipeline so that later LangChain reasoning works over facts instead of guesses.

### Scope

- Create `agents/unit_test_coverage_agent/` Python package.
- Collect changed files using Git diff.
- Classify changed files as production, test, build/config, docs, or other.
- Parse existing Surefire XML reports when present.
- Parse existing JaCoCo XML reports when present.
- Generate `unit-test-coverage-report.md`.
- Generate `unit-test-coverage-report.json`.
- Upload raw evidence artifacts from a manual GitHub Actions workflow.

### Acceptance criteria

- Agent runs locally as a CLI.
- Agent runs in a manual GitHub Actions workflow.
- No LLM calls.
- No LangChain dependency yet.
- No secrets.
- No write permissions.
- Missing JaCoCo/Surefire evidence is reported explicitly as `unknown`, not guessed.

## Story 2: JaCoCo enablement for Java services

As an engineer, I want each Java service to produce JaCoCo XML coverage so that the coverage agent can reason from actual line/branch/method coverage.

### Scope

- Inspect all service `pom.xml` files.
- Add or standardize `jacoco-maven-plugin` where missing.
- Ensure `mvn test jacoco:report` produces `target/site/jacoco/jacoco.xml`.
- Do not fail PRs on thresholds yet.

### Acceptance criteria

- All relevant services can generate JaCoCo XML.
- Agent report includes JaCoCo summaries when test execution produced coverage files.

## Story 3: Changed-code-to-coverage mapping

As an engineer, I want changed production files mapped to coverage evidence so that the report identifies uncovered changed classes.

### Scope

- Map changed Java production files to JaCoCo package/class names.
- Extract class-level and method-level coverage counters.
- Mark changed classes as covered, uncovered, partially covered, or unknown.

### Acceptance criteria

- Report includes changed production class coverage status.
- Missing coverage evidence remains `unknown`.

## Story 4: LangChain reasoning layer

As an engineer, I want LangChain to review deterministic coverage evidence and produce a structured review so that test gaps are easier to understand.

### Scope

- Add LangChain and provider package dependencies.
- Add bounded prompt builder.
- Add provider abstraction: deterministic and OpenAI/LangChain.
- Validate LangChain output against local JSON schema.
- Render markdown only from validated JSON.

### Acceptance criteria

- Default mode remains deterministic.
- LangChain mode is explicit opt-in.
- No code mutation.
- No PR creation.
- Output fails closed if schema validation fails.

## Story 5: Patch proposal artifact

As an engineer, I want the agent to propose tests to add without writing code automatically.

### Scope

- Generate a file-level test proposal.
- Recommend test classes/methods/scenarios.
- Include suggested validation commands.

### Acceptance criteria

- Artifact only.
- No commits.
- No PR creation.
- No automatic test generation.

## Story 6: PR comment integration

As an engineer, I want a human-readable coverage summary posted to PRs after the safety model is validated.

### Scope

- Add optional PR comment workflow.
- Use minimal write permission only for PR comments.
- Never expose secrets to PR workflows from forks.

### Acceptance criteria

- Manual or trusted-branch only.
- No auto-fix.
- Comment content is generated from validated JSON.

## Story 7: Human-approved remediation

As an engineer, I want the agent to propose a patch after explicit human approval.

### Scope

- Generate patch proposal.
- Store patch as artifact.
- Do not apply patch automatically.

### Acceptance criteria

- No direct commit.
- No direct PR creation.
- Patch must be reviewed manually.
