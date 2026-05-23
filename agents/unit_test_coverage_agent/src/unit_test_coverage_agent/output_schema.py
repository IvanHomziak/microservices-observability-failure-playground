from __future__ import annotations

import json
from typing import Any

from .models import CoverageAssessment, as_jsonable

ALLOWED_COVERAGE_STATUS = {"sufficient", "insufficient", "unknown", "not_applicable"}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
ALLOWED_MERGE_RECOMMENDATION = {"approve", "block", "manual_review"}

REQUIRED_FIELDS: dict[str, type] = {
    "schema_version": str,
    "coverage_status": str,
    "changed_production_files": list,
    "changed_test_files": list,
    "changed_services": list,
    "surefire_reports_found": int,
    "jacoco_reports_found": int,
    "covered_classes": list,
    "uncovered_classes": list,
    "unknown_coverage_files": list,
    "missing_test_scenarios": list,
    "recommended_tests": list,
    "confidence": str,
    "blocking_reasons": list,
    "merge_recommendation": str,
    "safety_boundary": str,
}


def assessment_to_contract(assessment: CoverageAssessment) -> dict[str, Any]:
    payload = as_jsonable(assessment)
    errors = validate_contract(payload)
    if errors:
        raise ValueError("Invalid coverage assessment contract: " + "; ".join(errors))
    return payload


def validate_contract(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in payload:
            errors.append(f"Missing required field: {field}")
            continue
        if not isinstance(payload[field], expected_type):
            errors.append(f"Invalid type for {field}: expected {expected_type.__name__}, got {type(payload[field]).__name__}")

    if payload.get("schema_version") != "1.0":
        errors.append(f"Unsupported schema_version: {payload.get('schema_version')}")

    if isinstance(payload.get("coverage_status"), str) and payload["coverage_status"] not in ALLOWED_COVERAGE_STATUS:
        errors.append(f"Invalid coverage_status: {payload['coverage_status']}")

    if isinstance(payload.get("confidence"), str) and payload["confidence"] not in ALLOWED_CONFIDENCE:
        errors.append(f"Invalid confidence: {payload['confidence']}")

    if isinstance(payload.get("merge_recommendation"), str) and payload["merge_recommendation"] not in ALLOWED_MERGE_RECOMMENDATION:
        errors.append(f"Invalid merge_recommendation: {payload['merge_recommendation']}")

    for field in ("missing_test_scenarios", "recommended_tests", "blocking_reasons"):
        value = payload.get(field)
        if isinstance(value, list):
            if not value:
                errors.append(f"List field must not be empty: {field}")
            for index, item in enumerate(value):
                if not isinstance(item, str) or not item.strip():
                    errors.append(f"Invalid list item for {field}[{index}]")

    boundary = payload.get("safety_boundary")
    if isinstance(boundary, str) and "does not authorize code mutation" not in boundary:
        errors.append("safety_boundary must explicitly prohibit code mutation")

    return errors


def render_contract_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
