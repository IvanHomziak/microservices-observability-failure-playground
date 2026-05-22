from __future__ import annotations

import json
from typing import Any

from .schemas import ReasoningReport

SCHEMA_VERSION = "1.0"
ALLOWED_CONFIDENCE = {"low", "medium", "high"}

REQUIRED_FIELDS: dict[str, type] = {
    "schema_version": str,
    "executive_summary": str,
    "evidence_inspected": list,
    "failed_workflow": str,
    "failed_jobs_and_steps": list,
    "symptoms": list,
    "root_cause_hypotheses": list,
    "confidence": str,
    "missing_evidence": list,
    "recommended_fix": list,
    "files_likely_affected": list,
    "files_not_to_change_casually": list,
    "validation_plan": list,
    "risk_assessment": str,
    "safety_boundary": str,
}

NON_EMPTY_LIST_FIELDS = {
    "evidence_inspected",
    "failed_jobs_and_steps",
    "symptoms",
    "root_cause_hypotheses",
    "missing_evidence",
    "recommended_fix",
    "files_likely_affected",
    "files_not_to_change_casually",
    "validation_plan",
}


def report_to_contract(report: ReasoningReport) -> dict[str, Any]:
    """Convert a reasoning report into a stable JSON contract.

    This contract is intentionally explicit so future LLM providers can be
    validated against the same shape before their output is trusted.
    """

    return {
        "schema_version": SCHEMA_VERSION,
        "executive_summary": report.executive_summary,
        "evidence_inspected": list(report.evidence_inspected),
        "failed_workflow": report.failed_workflow,
        "failed_jobs_and_steps": list(report.failed_jobs_and_steps),
        "symptoms": list(report.symptoms),
        "root_cause_hypotheses": list(report.root_cause_hypotheses),
        "confidence": report.confidence,
        "missing_evidence": list(report.missing_evidence),
        "recommended_fix": list(report.recommended_fix),
        "files_likely_affected": list(report.files_likely_affected),
        "files_not_to_change_casually": list(report.files_not_to_change_casually),
        "validation_plan": list(report.validation_plan),
        "risk_assessment": report.risk_assessment,
        "safety_boundary": (
            "Read-only advisory output. This JSON does not authorize code mutation, PR creation, "
            "deployment, secrets access, workflow permission escalation, or automatic remediation."
        ),
    }


def validate_contract(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in payload:
            errors.append(f"Missing required field: {field}")
            continue
        if not isinstance(payload[field], expected_type):
            errors.append(
                f"Invalid type for {field}: expected {expected_type.__name__}, got {type(payload[field]).__name__}"
            )

    confidence = payload.get("confidence")
    if isinstance(confidence, str) and confidence not in ALLOWED_CONFIDENCE:
        errors.append(f"Invalid confidence value: {confidence}")

    for field in NON_EMPTY_LIST_FIELDS:
        value = payload.get(field)
        if isinstance(value, list):
            if not value:
                errors.append(f"List field must not be empty: {field}")
            for index, item in enumerate(value):
                if not isinstance(item, str):
                    errors.append(f"Invalid list item type for {field}[{index}]: expected str")
                elif not item.strip():
                    errors.append(f"Blank list item for {field}[{index}]")

    for field in ("executive_summary", "failed_workflow", "risk_assessment", "safety_boundary"):
        value = payload.get(field)
        if isinstance(value, str) and not value.strip():
            errors.append(f"String field must not be blank: {field}")

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Unsupported schema_version: {payload.get('schema_version')}")

    return errors


def render_contract_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


def _list_items(payload: dict[str, Any], field: str) -> list[str]:
    value = payload.get(field)
    if isinstance(value, list):
        return [str(item) for item in value]
    return ["Invalid or missing field"]


def _append_list_section(lines: list[str], title: str, items: list[str]) -> None:
    lines.append(f"## {title}")
    lines.append("")
    for item in items:
        lines.append(f"- {item}")
    lines.append("")


def render_contract_markdown(payload: dict[str, Any]) -> str:
    """Render a validated JSON contract as markdown.

    The payload is validated first so providers cannot bypass the schema by
    returning arbitrary markdown.
    """

    errors = validate_contract(payload)
    if errors:
        raise ValueError(f"Cannot render invalid contract: {'; '.join(errors)}")

    lines: list[str] = []
    lines.append("# Agent Diagnostic Report")
    lines.append("")
    lines.append("## Executive summary")
    lines.append("")
    lines.append(str(payload["executive_summary"]))
    lines.append("")
    _append_list_section(lines, "Evidence inspected", _list_items(payload, "evidence_inspected"))
    lines.append("## Failed workflow")
    lines.append("")
    lines.append(str(payload["failed_workflow"]))
    lines.append("")
    _append_list_section(lines, "Failed jobs and steps", _list_items(payload, "failed_jobs_and_steps"))
    _append_list_section(lines, "Symptoms", _list_items(payload, "symptoms"))
    _append_list_section(lines, "Root-cause hypotheses", _list_items(payload, "root_cause_hypotheses"))
    lines.append("## Confidence")
    lines.append("")
    lines.append(f"`{payload['confidence']}`")
    lines.append("")
    _append_list_section(lines, "Missing evidence", _list_items(payload, "missing_evidence"))
    _append_list_section(lines, "Recommended fix", _list_items(payload, "recommended_fix"))
    _append_list_section(lines, "Files likely affected", _list_items(payload, "files_likely_affected"))
    _append_list_section(lines, "Files not to change casually", _list_items(payload, "files_not_to_change_casually"))
    _append_list_section(lines, "Validation plan", _list_items(payload, "validation_plan"))
    lines.append("## Risk assessment")
    lines.append("")
    lines.append(str(payload["risk_assessment"]))
    lines.append("")
    lines.append("## Boundary")
    lines.append("")
    lines.append(str(payload["safety_boundary"]))
    lines.append("")
    return "\n".join(lines)


def contract_from_report(report: ReasoningReport) -> dict[str, Any]:
    payload = report_to_contract(report)
    errors = validate_contract(payload)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Invalid reasoning report contract: {joined}")
    return payload
