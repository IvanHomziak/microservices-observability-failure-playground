from __future__ import annotations

from .schemas import ReasoningReport


def _section_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


def render_markdown(report: ReasoningReport) -> str:
    lines: list[str] = []
    lines.append("# Agent Diagnostic Report")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append(report.executive_summary)
    lines.append("")

    lines.append("## Evidence inspected")
    lines.append("")
    lines.extend(_section_list(report.evidence_inspected))
    lines.append("")

    lines.append("## Failed workflow")
    lines.append("")
    lines.append(report.failed_workflow)
    lines.append("")

    lines.append("## Failed jobs and steps")
    lines.append("")
    lines.extend(_section_list(report.failed_jobs_and_steps))
    lines.append("")

    lines.append("## Symptoms")
    lines.append("")
    lines.extend(_section_list(report.symptoms))
    lines.append("")

    lines.append("## Root-cause hypotheses")
    lines.append("")
    lines.extend(_section_list(report.root_cause_hypotheses))
    lines.append("")

    lines.append("## Confidence")
    lines.append("")
    lines.append(f"`{report.confidence}`")
    lines.append("")

    lines.append("## Missing evidence")
    lines.append("")
    lines.extend(_section_list(report.missing_evidence))
    lines.append("")

    lines.append("## Recommended fix")
    lines.append("")
    lines.extend(_section_list(report.recommended_fix))
    lines.append("")

    lines.append("## Files likely affected")
    lines.append("")
    lines.extend(_section_list(report.files_likely_affected))
    lines.append("")

    lines.append("## Files not to change casually")
    lines.append("")
    lines.extend(_section_list(report.files_not_to_change_casually))
    lines.append("")

    lines.append("## Validation plan")
    lines.append("")
    lines.extend(_section_list(report.validation_plan))
    lines.append("")

    lines.append("## Risk assessment")
    lines.append("")
    lines.append(report.risk_assessment)
    lines.append("")

    lines.append("## Boundary")
    lines.append("")
    lines.append("This report is read-only and advisory. It does not authorize automatic code mutation, PR creation, deployment, or workflow permission escalation.")
    lines.append("")
    return "\n".join(lines)
