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
    lines.append("")

    _append_list(lines, "Changed services", payload["changed_services"])
    _append_list(lines, "Changed production files", payload["changed_production_files"])
    _append_list(lines, "Changed test files", payload["changed_test_files"])
    _append_list(lines, "Covered classes", payload["covered_classes"])
    _append_list(lines, "Uncovered classes", payload["uncovered_classes"])
    _append_list(lines, "Unknown coverage files", payload["unknown_coverage_files"])
    _append_list(lines, "Missing test scenarios", payload["missing_test_scenarios"])
    _append_list(lines, "Recommended tests", payload["recommended_tests"])
    _append_list(lines, "Blocking reasons", payload["blocking_reasons"])

    lines.append("## Safety boundary")
    lines.append("")
    lines.append(payload["safety_boundary"])
    lines.append("")
    return "\n".join(lines)
