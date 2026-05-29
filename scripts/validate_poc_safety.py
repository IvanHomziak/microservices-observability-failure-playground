from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_WORKFLOWS = [
    ".github/workflows/ci-failure-reasoning-agent.yml",
    ".github/workflows/unit-test-coverage-agent.yml",
    ".github/workflows/unit-test-coverage-pr-comment.yml",
    ".github/workflows/unit-test-coverage-policy-check.yml",
]

EXPECTED_DOCS = [
    "docs/poc-validation-runbook.md",
    "docs/poc-demo-script.md",
    "docs/poc-summary.md",
    "docs/coverage-policy-configuration.md",
    "docs/coverage-policy-enforcement-workflow.md",
    "docs/coverage-pr-comment-integration.md",
    "docs/coverage-patch-proposal-artifact.md",
    "docs/langchain-coverage-reasoning.md",
    "docs/changed-code-coverage-mapping.md",
    "docs/jacoco-coverage-enablement.md",
    "docs/unit-test-coverage-agent.md",
]

EXPECTED_AGENT_MODULES = [
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/main.py",
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/assessment.py",
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/policy.py",
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/enforce_policy.py",
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/pr_comment.py",
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/patch_proposal.py",
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/providers.py",
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/prompt_builder.py",
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/jacoco_loader.py",
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/surefire_loader.py",
    "agents/unit_test_coverage_agent/src/unit_test_coverage_agent/git_diff.py",
]

READ_ONLY_WORKFLOWS = [
    ".github/workflows/unit-test-coverage-agent.yml",
    ".github/workflows/unit-test-coverage-policy-check.yml",
]

PR_COMMENT_WORKFLOW = ".github/workflows/unit-test-coverage-pr-comment.yml"
POLICY_CHECK_WORKFLOW = ".github/workflows/unit-test-coverage-policy-check.yml"


def read(path: str) -> str:
    return (REPOSITORY_ROOT / path).read_text(encoding="utf-8")


def assert_exists(path: str, failures: list[str]) -> None:
    if not (REPOSITORY_ROOT / path).exists():
        failures.append(f"Missing required file: {path}")


def assert_not_contains(path: str, text: str, failures: list[str]) -> None:
    file_path = REPOSITORY_ROOT / path
    if not file_path.exists():
        failures.append(f"Cannot inspect missing file: {path}")
        return
    content = read(path)
    if text in content:
        failures.append(f"Forbidden text `{text}` found in {path}")


def assert_contains(path: str, text: str, failures: list[str]) -> None:
    file_path = REPOSITORY_ROOT / path
    if not file_path.exists():
        failures.append(f"Cannot inspect missing file: {path}")
        return
    content = read(path)
    if text not in content:
        failures.append(f"Expected text `{text}` not found in {path}")


def assert_not_contains_segment(path: str, segment_name: str, segment: str, text: str, failures: list[str]) -> None:
    if text in segment:
        failures.append(f"Forbidden text `{text}` found in {path} segment `{segment_name}`")


def workflow_segment(content: str, start_marker: str, end_marker: str | None = None) -> str:
    if start_marker not in content:
        return ""
    _, _, tail = content.partition(start_marker)
    if end_marker is None or end_marker not in tail:
        return tail
    segment, _, _ = tail.partition(end_marker)
    return segment


def validate_expected_files(failures: list[str]) -> None:
    for path in EXPECTED_WORKFLOWS:
        assert_exists(path, failures)
    for path in EXPECTED_DOCS:
        assert_exists(path, failures)
    for path in EXPECTED_AGENT_MODULES:
        assert_exists(path, failures)
    assert_exists("coverage-policy.yml", failures)
    assert_exists("agents/unit_test_coverage_agent/tests/test_unit_test_coverage_agent.py", failures)


def validate_no_pull_request_target(failures: list[str]) -> None:
    for workflow in EXPECTED_WORKFLOWS:
        assert_not_contains(workflow, "pull_request_target", failures)


def validate_read_only_workflows(failures: list[str]) -> None:
    for workflow in READ_ONLY_WORKFLOWS:
        assert_not_contains(workflow, "pull-requests: write", failures)
        assert_not_contains(workflow, "issues: write", failures)


def validate_pr_comment_workflow_isolation(failures: list[str]) -> None:
    workflow = PR_COMMENT_WORKFLOW
    assert_contains(workflow, "Generate coverage evidence without write credentials", failures)
    assert_contains(workflow, "Render and update PR comment with write credentials", failures)
    assert_contains(workflow, "refs/pull/${PR_NUMBER}/head", failures)
    assert_contains(workflow, "github-actions[bot]", failures)
    assert_contains(workflow, "COMMENT_MARKER", failures)
    assert_contains(workflow, "pull-requests: write", failures)
    assert_contains(workflow, "issues: write", failures)
    assert_contains(workflow, "use_llm_summary", failures)
    assert_contains(workflow, "USE_LLM_SUMMARY", failures)
    assert_contains(workflow, "OPENAI_API_KEY", failures)
    assert_contains(workflow, "inputs.use_llm_summary && secrets.OPENAI_API_KEY || ''", failures)
    assert_contains(workflow, "OPENAI_API_KEY repository secret is required when use_llm_summary=true", failures)
    assert_not_contains(workflow, "langchain-openai", failures)
    assert_not_contains(workflow, "provider:", failures)

    content = read(workflow)
    evidence_job = workflow_segment(content, "generate-coverage-evidence:", "update-pr-comment:")
    comment_job = workflow_segment(content, "update-pr-comment:")
    if not evidence_job:
        failures.append(f"Could not locate generate-coverage-evidence job in {workflow}")
    if not comment_job:
        failures.append(f"Could not locate update-pr-comment job in {workflow}")

    assert_not_contains_segment(workflow, "generate-coverage-evidence", evidence_job, "OPENAI_API_KEY", failures)
    assert_not_contains_segment(workflow, "generate-coverage-evidence", evidence_job, "secrets.OPENAI_API_KEY", failures)
    assert_not_contains_segment(workflow, "generate-coverage-evidence", evidence_job, "USE_LLM_SUMMARY", failures)


def validate_policy_check_workflow(failures: list[str]) -> None:
    workflow = POLICY_CHECK_WORKFLOW
    assert_contains(workflow, "python -m unit_test_coverage_agent.enforce_policy", failures)
    assert_contains(workflow, "--provider deterministic", failures)
    assert_not_contains(workflow, "OPENAI_API_KEY", failures)
    assert_not_contains(workflow, "langchain-openai", failures)
    assert_not_contains(workflow, "pull-requests: write", failures)
    assert_not_contains(workflow, "issues: write", failures)


def validate_unit_test_coverage_agent_workflow(failures: list[str]) -> None:
    workflow = ".github/workflows/unit-test-coverage-agent.yml"
    assert_contains(workflow, "provider:", failures)
    assert_contains(workflow, "deterministic", failures)
    assert_contains(workflow, "langchain-openai", failures)
    assert_contains(workflow, "OPENAI_API_KEY", failures)
    assert_not_contains(workflow, "pull-requests: write", failures)
    assert_not_contains(workflow, "issues: write", failures)


def main() -> int:
    failures: list[str] = []

    validate_expected_files(failures)
    validate_no_pull_request_target(failures)
    validate_read_only_workflows(failures)
    validate_pr_comment_workflow_isolation(failures)
    validate_policy_check_workflow(failures)
    validate_unit_test_coverage_agent_workflow(failures)

    if failures:
        print("POC safety validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("POC safety validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
