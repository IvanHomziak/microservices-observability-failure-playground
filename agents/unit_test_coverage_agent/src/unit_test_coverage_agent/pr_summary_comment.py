from __future__ import annotations

from typing import Any

COMMENT_MARKER = "<!-- unit-test-coverage-agent-comment -->"


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _truncate_markdown(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars].rstrip() + "\n\n...truncated..."


def _limit_items(items: list[Any], max_items: int) -> tuple[list[Any], bool]:
    return items[:max_items], len(items) > max_items


def _fmt_percent(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, (int, float)):
        return f"{value:.2f}"
    return str(value)


def render_pr_summary_comment(
    contract: dict,
    patch_proposal: dict | None = None,
    full_report_markdown: str | None = None,
    patch_proposal_markdown: str | None = None,
    *,
    llm_summary: dict[str, Any] | None = None,
    llm_note: str | None = None,
    max_full_report_chars: int = 30000,
    max_patch_proposal_chars: int = 20000,
    max_inline_items: int = 20,
) -> str:
    patch_proposal = patch_proposal or {}

    policy_violations = [str(v) for v in _as_list(contract.get("policy_violations"))]
    policy_warnings = [str(v) for v in _as_list(contract.get("policy_warnings"))]
    changed_prod = _as_list(contract.get("changed_production_files"))
    changed_test = _as_list(contract.get("changed_test_files"))
    test_exec_failures = _as_list(contract.get("test_execution_failures"))
    failed_suites = _as_list(contract.get("failed_test_suites"))
    changed_cov = _as_list(contract.get("changed_class_coverage"))
    related_evidence = _as_list(contract.get("related_test_evidence"))
    suggested_tests = _as_list(patch_proposal.get("proposed_test_scenarios"))

    lines: list[str] = [
        COMMENT_MARKER,
        "",
        "## Unit Test Coverage Agent",
        "",
        f"**Status:** `{contract.get('coverage_status', 'unknown')}`",
        f"**Recommendation:** `{contract.get('merge_recommendation', 'unknown')}`",
        f"**Confidence:** `{contract.get('confidence', 'unknown')}`",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Policy violations | {len(policy_violations)} |",
        f"| Policy warnings | {len(policy_warnings)} |",
        f"| Changed production files | {len(changed_prod)} |",
        f"| Changed test files | {len(changed_test)} |",
        f"| Test execution failures | {len(test_exec_failures)} |",
        f"| Surefire reports | {contract.get('surefire_reports_found', 0)} |",
        f"| JaCoCo reports | {contract.get('jacoco_reports_found', 0)} |",
        "",
    ]

    if llm_summary or llm_note:
        lines.extend([
            "### OpenAI-enhanced advisory summary",
            "",
        ])
        if llm_summary:
            lines.extend([
                str(llm_summary.get("executive_summary", "")).strip(),
                "",
                f"- Risk assessment: `{llm_summary.get('risk_assessment', 'unknown')}`",
                "",
                "#### Reviewer guidance",
                "",
            ])
            lines.extend([f"- {item}" for item in _as_list(llm_summary.get("reviewer_guidance"))])
            lines.extend(["", "#### Developer next steps", ""])
            lines.extend([f"- {item}" for item in _as_list(llm_summary.get("developer_next_steps"))])
            lines.extend(["", "#### Limitations", ""])
            lines.extend([f"- {item}" for item in _as_list(llm_summary.get("limitations"))])
            lines.append("")
        if llm_note:
            lines.extend([f"_{llm_note}_", ""])
        lines.extend([
            "_This advisory section cannot override the deterministic status, recommendation, policy findings, changed files, coverage percentages, affected services, test failure counts, or Maven failure status shown below._",
            "",
        ])

    shown, truncated = _limit_items(policy_violations, max_inline_items)
    if shown:
        lines.extend(["### Policy violations", ""])
        lines.extend([f"- {item}" for item in shown])
        if truncated:
            lines.append("")
            lines.append(f"_Only first {max_inline_items} items shown. See workflow artifacts for the full report._")
        lines.append("")

    shown, truncated = _limit_items(policy_warnings, max_inline_items)
    if shown:
        lines.extend(["### Policy warnings", ""])
        lines.extend([f"- {item}" for item in shown])
        if truncated:
            lines.append("")
            lines.append(f"_Only first {max_inline_items} items shown. See workflow artifacts for the full report._")
        lines.append("")

    if changed_cov:
        rows, cov_trunc = _limit_items(changed_cov, 30)
        lines.extend([
            "### Changed class coverage",
            "",
            "| Class | Status | Line % | Method % | Branch % | Mapping | Confidence |",
            "|---|---:|---:|---:|---:|---|---:|",
        ])
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"| `{row.get('expected_class_name', 'unknown')}` | `{row.get('status', 'unknown')}` | "
                f"{_fmt_percent(row.get('line_coverage_percent'))} | {_fmt_percent(row.get('method_coverage_percent'))} | "
                f"{_fmt_percent(row.get('branch_coverage_percent'))} | `{row.get('mapping_strategy', 'n/a')}` | "
                f"`{row.get('mapping_confidence', 'n/a')}` |"
            )
        if cov_trunc:
            lines.append("")
            lines.append("_Only first 30 items shown. See workflow artifacts for the full report._")
        lines.append("")

    if any(k in contract for k in ["test_total_count", "test_failure_count", "test_error_count", "test_skipped_count"]):
        lines.extend([
            "### Test execution",
            "",
            f"- Total tests: `{contract.get('test_total_count', 'n/a')}`",
            f"- Failures: `{contract.get('test_failure_count', 'n/a')}`",
            f"- Errors: `{contract.get('test_error_count', 'n/a')}`",
            f"- Skipped: `{contract.get('test_skipped_count', 'n/a')}`",
            "",
        ])

    if failed_suites:
        lines.extend([
            "### Failed test suites",
            "",
            "| File | Tests | Failures | Errors | Skipped |",
            "|---|---:|---:|---:|---:|",
        ])
        for item in failed_suites[:max_inline_items]:
            if isinstance(item, dict):
                lines.append(
                    f"| `{item.get('file', 'unknown')}` | {item.get('tests', 'n/a')} | {item.get('failures', 'n/a')} | {item.get('errors', 'n/a')} | {item.get('skipped', 'n/a')} |"
                )
        if len(failed_suites) > max_inline_items:
            lines.append("")
            lines.append(f"_Only first {max_inline_items} items shown. See workflow artifacts for the full report._")
        lines.append("")

    if related_evidence:
        lines.extend([
            "### Related test evidence",
            "",
            "| Production class | Status | Matched tests |",
            "|---|---:|---|",
        ])
        for item in related_evidence[:max_inline_items]:
            if not isinstance(item, dict):
                continue
            matched = ", ".join(f"`{x}`" for x in _as_list(item.get("matched_test_files"))) or "-"
            lines.append(f"| `{item.get('expected_class_name', 'unknown')}` | `{item.get('status', 'unknown')}` | {matched} |")
        if len(related_evidence) > max_inline_items:
            lines.append("")
            lines.append(f"_Only first {max_inline_items} items shown. See workflow artifacts for the full report._")
        lines.append("")

    lines.extend([
        "### Patch proposal",
        "",
        f"- Proposal status: `{patch_proposal.get('proposal_status', 'unknown')}`",
        f"- Suggested test scenarios: `{len(suggested_tests)}`",
        "",
    ])

    shown, truncated = _limit_items(suggested_tests, max_inline_items)
    if shown:
        for item in shown:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('production_class', 'unknown')}` -> `{item.get('suggested_test_file', 'unknown')}`")
        if truncated:
            lines.append("")
            lines.append(f"_Only first {max_inline_items} items shown. See workflow artifacts for the full report._")
        lines.append("")

    if full_report_markdown:
        lines.extend([
            "<details>",
            "<summary>Full coverage report</summary>",
            "",
            _truncate_markdown(full_report_markdown, max_full_report_chars),
            "",
            "</details>",
            "",
        ])

    if patch_proposal_markdown:
        lines.extend([
            "<details>",
            "<summary>Patch proposal details</summary>",
            "",
            _truncate_markdown(patch_proposal_markdown, max_patch_proposal_chars),
            "",
            "</details>",
            "",
        ])

    lines.extend([
        "### Safety boundary",
        "",
        "This comment is generated from validated artifacts. It does not authorize code mutation, deployment, or automatic remediation.",
        "",
    ])
    return "\n".join(lines)
