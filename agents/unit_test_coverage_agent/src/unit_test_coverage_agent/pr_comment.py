from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .output_schema import validate_contract

COMMENT_MARKER = "<!-- unit-test-coverage-agent-comment -->"


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value) for value in values]


def _table_rows_for_changed_classes(coverage_contract: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    changed_class_coverage = coverage_contract.get("changed_class_coverage", [])
    if not isinstance(changed_class_coverage, list):
        return rows

    for item in changed_class_coverage:
        if not isinstance(item, dict):
            continue
        source_file = item.get("source_file", "")
        expected_class = item.get("expected_class_name", "")
        status = item.get("status", "")
        line_percent = item.get("line_coverage_percent")
        method_percent = item.get("method_coverage_percent")
        branch_percent = item.get("branch_coverage_percent")
        rows.append(
            "| "
            f"`{source_file}` | "
            f"`{expected_class}` | "
            f"`{status}` | "
            f"{line_percent if line_percent is not None else 'n/a'} | "
            f"{method_percent if method_percent is not None else 'n/a'} | "
            f"{branch_percent if branch_percent is not None else 'n/a'} |"
        )
    return rows


def _proposal_rows(patch_proposal: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    scenarios = patch_proposal.get("proposed_test_scenarios", [])
    if not isinstance(scenarios, list):
        return rows
    for item in scenarios[:10]:
        if not isinstance(item, dict):
            continue
        production_class = item.get("production_class", "")
        suggested_test_file = item.get("suggested_test_file", "")
        suggested_methods = item.get("suggested_test_methods", [])
        methods = ", ".join(f"`{method}`" for method in _list(suggested_methods)[:5]) or "-"
        rows.append(f"| `{production_class}` | `{suggested_test_file}` | {methods} |")
    return rows


def render_pr_comment(coverage_contract: dict[str, Any], patch_proposal: dict[str, Any]) -> str:
    errors = validate_contract(coverage_contract)
    if errors:
        raise ValueError("Invalid coverage contract: " + "; ".join(errors))

    lines: list[str] = []
    lines.append(COMMENT_MARKER)
    lines.append("## Unit Test Coverage Agent")
    lines.append("")
    lines.append("### Summary")
    lines.append("")
    lines.append(f"- Coverage status: `{coverage_contract['coverage_status']}`")
    lines.append(f"- Merge recommendation: `{coverage_contract['merge_recommendation']}`")
    lines.append(f"- Confidence: `{coverage_contract['confidence']}`")
    lines.append(f"- Surefire reports found: `{coverage_contract['surefire_reports_found']}`")
    lines.append(f"- JaCoCo reports found: `{coverage_contract['jacoco_reports_found']}`")
    lines.append(f"- Patch proposal status: `{patch_proposal.get('proposal_status', 'unknown')}`")
    lines.append("")

    changed_rows = _table_rows_for_changed_classes(coverage_contract)
    if changed_rows:
        lines.append("### Changed class coverage")
        lines.append("")
        lines.append("| Source file | Class | Status | Line % | Method % | Branch % |")
        lines.append("|---|---|---:|---:|---:|---:|")
        lines.extend(changed_rows)
        lines.append("")

    blocking_reasons = _list(coverage_contract.get("blocking_reasons"))
    if blocking_reasons:
        lines.append("### Blocking/manual review reasons")
        lines.append("")
        for reason in blocking_reasons:
            lines.append(f"- {reason}")
        lines.append("")

    proposal_rows = _proposal_rows(patch_proposal)
    if proposal_rows:
        lines.append("### Proposed test work")
        lines.append("")
        lines.append("| Production class | Suggested test file | Suggested test methods |")
        lines.append("|---|---|---|")
        lines.extend(proposal_rows)
        lines.append("")

    validation_commands = _list(patch_proposal.get("validation_commands"))
    if validation_commands:
        lines.append("### Validation commands")
        lines.append("")
        for command in validation_commands:
            lines.append(f"- `{command}`")
        lines.append("")

    lines.append("### Safety boundary")
    lines.append("")
    lines.append(
        "This comment is advisory only. It does not authorize code mutation, test deletion, commit creation, "
        "PR creation, deployment, secrets access, workflow permission escalation, or automatic remediation."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a PR comment from validated unit test coverage agent artifacts.")
    parser.add_argument("--coverage-json", required=True, type=Path)
    parser.add_argument("--patch-proposal-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    coverage_contract = _load_json(args.coverage_json)
    patch_proposal = _load_json(args.patch_proposal_json)
    comment = render_pr_comment(coverage_contract, patch_proposal)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(comment + "\n", encoding="utf-8")
    print(f"Wrote PR comment to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
