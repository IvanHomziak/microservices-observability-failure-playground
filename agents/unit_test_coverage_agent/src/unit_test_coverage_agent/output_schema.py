from __future__ import annotations

import json
from typing import Any

from .models import CoverageAssessment, as_jsonable

ALLOWED_COVERAGE_STATUS = {"sufficient", "insufficient", "partial", "unknown", "not_applicable", "policy_violation"}
ALLOWED_CLASS_COVERAGE_STATUS = {"covered", "partial", "uncovered", "unknown"}
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
    "test_total_count": int,
    "test_failure_count": int,
    "test_error_count": int,
    "test_skipped_count": int,
    "failed_test_suites": list,
    "test_execution_failures": list,
    "changed_class_coverage": list,
    "related_test_evidence": list,
    "covered_classes": list,
    "partially_covered_classes": list,
    "uncovered_classes": list,
    "unknown_coverage_files": list,
    "missing_related_test_files": list,
    "policy": dict,
    "policy_violations": list,
    "policy_warnings": list,
    "missing_test_scenarios": list,
    "recommended_tests": list,
    "confidence": str,
    "blocking_reasons": list,
    "merge_recommendation": str,
    "safety_boundary": str,
}

REQUIRED_POLICY_FIELDS: dict[str, type] = {
    "minimum_line_coverage_for_changed_classes": (int, float),
    "minimum_method_coverage_for_changed_classes": (int, float),
    "minimum_branch_coverage_for_changed_classes": (int, float),
    "require_test_changes_when_production_code_changes": bool,
    "require_related_test_change_when_production_code_changes": bool,
    "fail_on_unknown_coverage": bool,
    "fail_on_missing_surefire_evidence": bool,
    "fail_on_missing_jacoco_evidence": bool,
    "fail_on_maven_verification_failure": bool,
    "fail_on_test_failures": bool,
}

REQUIRED_CHANGED_CLASS_FIELDS: dict[str, type] = {
    "source_file": str,
    "expected_class_name": str,
    "status": str,
    "lines_covered": int,
    "lines_missed": int,
    "methods_covered": int,
    "methods_missed": int,
    "uncovered_methods": list,
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

    policy = payload.get("policy")
    if isinstance(policy, dict):
        for field, expected_type in REQUIRED_POLICY_FIELDS.items():
            if field not in policy:
                errors.append(f"Missing policy.{field}")
                continue
            if not isinstance(policy[field], expected_type):
                errors.append(f"Invalid type for policy.{field}")

    for field in ("missing_test_scenarios", "recommended_tests", "blocking_reasons"):
        value = payload.get(field)
        if isinstance(value, list):
            if not value:
                errors.append(f"List field must not be empty: {field}")
            for index, item in enumerate(value):
                if not isinstance(item, str) or not item.strip():
                    errors.append(f"Invalid list item for {field}[{index}]")

    for field in ("policy_violations", "policy_warnings", "test_execution_failures"):
        value = payload.get(field)
        if isinstance(value, list):
            for index, item in enumerate(value):
                if not isinstance(item, str) or not item.strip():
                    errors.append(f"Invalid list item for {field}[{index}]")

    failed_test_suites = payload.get("failed_test_suites")
    if isinstance(failed_test_suites, list):
        for index, item in enumerate(failed_test_suites):
            if not isinstance(item, dict):
                errors.append(f"Invalid failed_test_suites[{index}]: expected object")
                continue
            for field, expected_type in REQUIRED_FAILED_SUITE_FIELDS.items():
                if field not in item:
                    errors.append(f"Missing failed_test_suites[{index}].{field}")
                    continue
                if not isinstance(item[field], expected_type):
                    errors.append(f"Invalid type for failed_test_suites[{index}].{field}: expected {expected_type.__name__}")

    related_test_evidence = payload.get("related_test_evidence")
    if isinstance(related_test_evidence, list):
        for index, item in enumerate(related_test_evidence):
            if not isinstance(item, dict):
                errors.append(f"Invalid related_test_evidence[{index}]: expected object")
                continue
            for field, expected_type in REQUIRED_RELATED_TEST_FIELDS.items():
                if field not in item:
                    errors.append(f"Missing related_test_evidence[{index}].{field}")
                    continue
                if not isinstance(item[field], expected_type):
                    errors.append(f"Invalid type for related_test_evidence[{index}].{field}: expected {expected_type.__name__}")
            status = item.get("status")
            if isinstance(status, str) and status not in ALLOWED_RELATED_TEST_STATUS:
                errors.append(f"Invalid related_test_evidence[{index}].status: {status}")
            for list_field in ("expected_test_files", "matched_test_files"):
                lst = item.get(list_field)
                if isinstance(lst, list):
                    for j, value in enumerate(lst):
                        if not isinstance(value, str):
                            errors.append(f"Invalid related_test_evidence[{index}].{list_field}[{j}]: expected string")

    changed_class_coverage = payload.get("changed_class_coverage")
    if isinstance(changed_class_coverage, list):
        for index, item in enumerate(changed_class_coverage):
            if not isinstance(item, dict):
                errors.append(f"Invalid changed_class_coverage[{index}]: expected object")
                continue
            for field, expected_type in REQUIRED_CHANGED_CLASS_FIELDS.items():
                if field not in item:
                    errors.append(f"Missing changed_class_coverage[{index}].{field}")
                    continue
                if not isinstance(item[field], expected_type):
                    errors.append(
                        f"Invalid type for changed_class_coverage[{index}].{field}: expected {expected_type.__name__}"
                    )
            status = item.get("status")
            if isinstance(status, str) and status not in ALLOWED_CLASS_COVERAGE_STATUS:
                errors.append(f"Invalid changed_class_coverage[{index}].status: {status}")
            for percent_field in ("line_coverage_percent", "branch_coverage_percent", "method_coverage_percent"):
                value = item.get(percent_field)
                if value is not None and not isinstance(value, (int, float)):
                    errors.append(f"Invalid changed_class_coverage[{index}].{percent_field}: expected number or null")

    boundary = payload.get("safety_boundary")
    if isinstance(boundary, str) and "does not authorize code mutation" not in boundary:
        errors.append("safety_boundary must explicitly prohibit code mutation")

    return errors


def render_contract_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)


REQUIRED_FAILED_SUITE_FIELDS: dict[str, type] = {
    "file": str,
    "tests": int,
    "failures": int,
    "errors": int,
    "skipped": int,
}


REQUIRED_RELATED_TEST_FIELDS: dict[str, type] = {
    "production_file": str,
    "expected_class_name": str,
    "expected_test_files": list,
    "matched_test_files": list,
    "status": str,
}
ALLOWED_RELATED_TEST_STATUS = {"matched", "missing", "not_applicable"}
