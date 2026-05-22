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


def contract_from_report(report: ReasoningReport) -> dict[str, Any]:
    payload = report_to_contract(report)
    errors = validate_contract(payload)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"Invalid reasoning report contract: {joined}")
    return payload
