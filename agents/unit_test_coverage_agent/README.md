# Unit Test Coverage Agent

Deterministic scaffold for collecting unit-test coverage evidence for changed Java code.

## Scope

Current version:

- collects changed files from Git diff;
- classifies changed files;
- parses existing Surefire XML reports;
- parses existing JaCoCo XML reports;
- generates validated JSON and markdown reports;
- does not call an LLM;
- does not use LangChain yet;
- does not mutate code;
- does not create PRs.

## Inputs

```text
base_ref
head_ref
```

Example:

```bash
PYTHONPATH=agents/unit_test_coverage_agent/src \
python -m unit_test_coverage_agent.main \
  --repository-root . \
  --base-ref origin/main \
  --head-ref HEAD \
  --output coverage-agent/output/unit-test-coverage-report.md \
  --json-output coverage-agent/output/unit-test-coverage-report.json
```

## Evidence sources

The agent reads:

```text
git diff --name-only <base_ref>...<head_ref>
*/target/surefire-reports/TEST-*.xml
*/target/site/jacoco/jacoco.xml
```

## Output

```text
unit-test-coverage-report.md
unit-test-coverage-report.json
```

## Coverage status values

```text
sufficient
insufficient
unknown
not_applicable
```

## Safety boundary

The report is advisory only. It does not authorize code mutation, test deletion, PR creation, deployment, secrets access, workflow permission escalation, or automatic remediation.

## Tests

```bash
cd agents/unit_test_coverage_agent
python -m unittest discover -s tests
```

## Future LangChain layer

LangChain should be added after deterministic coverage evidence is stable. The LangChain layer must reason over generated evidence, not raw repository guesses.
