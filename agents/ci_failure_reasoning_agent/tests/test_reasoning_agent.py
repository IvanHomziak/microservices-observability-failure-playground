from __future__ import annotations

import json
from pathlib import Path

from ci_failure_reasoning_agent.evidence_loader import load_evidence_pack
from ci_failure_reasoning_agent.reasoner import reason
from ci_failure_reasoning_agent.renderer import render_markdown


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_evidence_pack_reports_missing_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write(repo / "AGENTS.md", "# AGENTS\n")
    evidence = tmp_path / "triage"
    evidence.mkdir()

    pack = load_evidence_pack(evidence, repo)

    assert str(evidence / "raw" / "run.json") in pack.missing_files
    assert str(evidence / "raw" / "jobs.json") in pack.missing_files
    assert str(evidence / "output" / "ci-failure-diagnostics-report.md") in pack.missing_files


def test_reasoner_extracts_maven_failure_category(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write(repo / "AGENTS.md", "# AGENTS\nDo not hallucinate.\n")

    evidence = tmp_path / "triage"
    write(
        evidence / "raw" / "run.json",
        json.dumps(
            {
                "name": "Java Build Test",
                "displayTitle": "PR validation",
                "event": "pull_request",
                "headBranch": "feature/example",
                "headSha": "abc123",
                "status": "completed",
                "conclusion": "failure",
            }
        ),
    )
    write(
        evidence / "raw" / "jobs.json",
        json.dumps(
            {
                "jobs": [
                    {
                        "name": "Maven test (orders-service)",
                        "status": "completed",
                        "conclusion": "failure",
                        "steps": [
                            {
                                "name": "Run Maven tests with retry",
                                "number": 4,
                                "status": "completed",
                                "conclusion": "failure",
                            }
                        ],
                    }
                ]
            }
        ),
    )
    write(
        evidence / "output" / "ci-failure-diagnostics-report.md",
        """# CI Failure Diagnostics Report

## Failed jobs and steps

| Job | Conclusion | Status | Failed steps | Job URL |
|---|---|---|---|---|
| `Maven test (orders-service)` | `failure` | `completed` | #4 Run Maven tests with retry (failure) |  |

## Category summary

| Category | Count |
|---|---:|
| `maven-build-or-test-failure` | 1 |
""",
    )
    write(
        evidence / "output" / "agent-fix-plan.md",
        """# Agent Fix Plan

## Files likely involved

- `orders-service/src/test/**`
- `orders-service/pom.xml`

## Files or behavior that must not be changed casually

- Do not delete tests without proving they are invalid.

## Validation commands

- `cd orders-service && mvn test`
""",
    )
    write(evidence / "logs" / "workflow-run.log", "BUILD FAILURE\n")

    pack = load_evidence_pack(evidence, repo)
    report = reason(pack)
    rendered = render_markdown(report)

    assert report.confidence == "medium"
    assert "maven-build-or-test-failure" in rendered
    assert "orders-service/src/test/**" in rendered
    assert "cd orders-service && mvn test" in rendered


def test_reasoner_downgrades_confidence_when_required_evidence_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    evidence = tmp_path / "triage"
    write(
        evidence / "output" / "ci-failure-diagnostics-report.md",
        "| `docker-compose-contract-failure` | 1 |\n",
    )

    pack = load_evidence_pack(evidence, repo)
    report = reason(pack)

    assert report.confidence == "low"
    assert report.missing_evidence
