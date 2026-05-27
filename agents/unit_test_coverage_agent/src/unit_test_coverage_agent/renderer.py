from __future__ import annotations

from typing import Any


def _append_list(lines: list[str], title: str, values: list[str]) -> None:
    lines.append(f"## {title}")
    lines.append("")
    if not values:
        lines.append("- None")
    else:
        for value in values:
            lines.append(f"- {value}")
    lines.append("")


def _format_percent(value: Any) -> str:
    if value is None:
        return "n/a"
    return f"{value}%"


def _append_policy(lines: list[str], payload: dict[str, Any]) -> None:
    lines.append("## Coverage policy")
    lines.append("")
    policy = payload.get("policy", {})
    if not isinstance(policy, dict):
        lines.append("Policy data is unavailable.")
        lines.append("")
        return

    lines.append("| Setting | Value |")
    lines.append("|---|---:|")
    for key, value in policy.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.append("")


def _append_changed_class_coverage(lines: list[str], payload: dict[str, Any]) -> None:
    lines.append("## Changed class coverage")
    lines.append("")
    rows = payload.get("changed_class_coverage", [])
    if not rows:
        lines.append("No changed production classes detected.")
        lines.append("")
        return

    lines.append("| Source file | Expected class | Status | Line % | Method % | Branch % | Uncovered methods |")
    lines.append("|---|---|---:|---:|---:|---:|---|")
    for row in rows:
        uncovered_methods = row.get("uncovered_methods") or []
        uncovered_text = ", ".join(f"`{method}`" for method in uncovered_methods) if uncovered_methods else "-"
        lines.append(
            "| "
            f"`{row.get('source_file', '')}` | "
            f"`{row.get('expected_class_name', '')}` | "
            f"`{row.get('status', '')}` | "
            f"{_format_percent(row.get('line_coverage_percent'))} | "
            f"{_format_percent(row.get('method_coverage_percent'))} | "
            f"{_format_percent(row.get('branch_coverage_percent'))} | "
            f"{uncovered_text} |"
        )
    lines.append("")




def _append_related_test_evidence(lines: list[str], payload: dict[str, Any]) -> None:
    lines.append("## Related test evidence")
    lines.append("")
    rows = payload.get("related_test_evidence", [])
    if not rows:
        lines.append("No changed production classes require related test evidence.")
        lines.append("")
        return

    lines.append("| Production file | Expected class | Status | Matched test files |")
    lines.append("|---|---|---:|---|")
    for row in rows:
        matched = row.get("matched_test_files") or []
        matched_text = ", ".join(f"`{item}`" for item in matched) if matched else "-"
        lines.append(f"| `{row.get('production_file', '')}` | `{row.get('expected_class_name', '')}` | `{row.get('status', '')}` | {matched_text} |")
    lines.append("")

def _append_failed_test_suites(lines: list[str], payload: dict[str, Any]) -> None:
    lines.append("## Failed test suites")
    lines.append("")
    suites = payload.get("failed_test_suites", [])
    if not suites:
        lines.append("- None")
        lines.append("")
        return

    lines.append("| File | Tests | Failures | Errors | Skipped |")
    lines.append("|---|---:|---:|---:|---:|")
    for suite in suites:
        lines.append(
            f"| `{suite.get('file', '')}` | {suite.get('tests', 0)} | {suite.get('failures', 0)} | {suite.get('errors', 0)} | {suite.get('skipped', 0)} |"
        )
    lines.append("")


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Unit Test Coverage Agent Report")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Coverage status: `{payload['coverage_status']}`")
    lines.append(f"- Merge recommendation: `{payload['merge_recommendation']}`")
    lines.append(f"- Confidence: `{payload['confidence']}`")
    lines.append(f"- Surefire reports found: `{payload['surefire_reports_found']}`")
    lines.append(f"- JaCoCo reports found: `{payload['jacoco_reports_found']}`")
    lines.append(f"- Tests total: `{payload['test_total_count']}`")
    lines.append(f"- Test failures: `{payload['test_failure_count']}`")
    lines.append(f"- Test errors: `{payload['test_error_count']}`")
    lines.append(f"- Test skipped: `{payload['test_skipped_count']}`")
    lines.append(f"- Failed test suites count: `{len(payload.get('failed_test_suites', []))}`")
    lines.append(f"- Policy violations: `{len(payload.get('policy_violations', []))}`")
    lines.append(f"- Policy warnings: `{len(payload.get('policy_warnings', []))}`")
    lines.append(f"- Test execution failures: `{len(payload.get('test_execution_failures', []))}`")
    lines.append("")

    _append_policy(lines, payload)
    _append_list(lines, "Changed services", payload["changed_services"])
    _append_list(lines, "Changed production files", payload["changed_production_files"])
    _append_list(lines, "Changed test files", payload["changed_test_files"])
    _append_failed_test_suites(lines, payload)
    _append_changed_class_coverage(lines, payload)
    _append_related_test_evidence(lines, payload)
    _append_list(lines, "Covered classes", payload["covered_classes"])
    _append_list(lines, "Partially covered classes", payload["partially_covered_classes"])
    _append_list(lines, "Uncovered classes", payload["uncovered_classes"])
    _append_list(lines, "Unknown coverage files", payload["unknown_coverage_files"])
    _append_list(lines, "Missing related test files", payload.get("missing_related_test_files", []))
    _append_list(lines, "Policy violations", payload.get("policy_violations", []))
    _append_list(lines, "Policy warnings", payload.get("policy_warnings", []))
    _append_list(lines, "Test execution failures", payload.get("test_execution_failures", []))
    _append_list(lines, "Missing test scenarios", payload["missing_test_scenarios"])
    _append_list(lines, "Recommended tests", payload["recommended_tests"])
    _append_list(lines, "Blocking reasons", payload["blocking_reasons"])

    lines.append("## Safety boundary")
    lines.append("")
    lines.append(payload["safety_boundary"])
    lines.append("")
    return "\n".join(lines)
