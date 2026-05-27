from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChangedFile:
    path: str
    category: str
    service: str | None = None


@dataclass(frozen=True)
class GitDiffEvidence:
    base_ref: str
    head_ref: str
    changed_files: tuple[ChangedFile, ...]
    raw_changed_files: tuple[str, ...]


@dataclass(frozen=True)
class SurefireSuite:
    file: str
    tests: int
    failures: int
    errors: int
    skipped: int
    time: float | None


@dataclass(frozen=True)
class SurefireEvidence:
    reports_found: int
    suites: tuple[SurefireSuite, ...]
    total_tests: int = 0
    total_failures: int = 0
    total_errors: int = 0
    total_skipped: int = 0
    failed_suites: tuple[SurefireSuite, ...] = ()


@dataclass(frozen=True)
class JacocoMethodCoverage:
    name: str
    descriptor: str
    line: int | None
    instruction_covered: int
    instruction_missed: int
    line_covered: int
    line_missed: int
    branch_covered: int
    branch_missed: int


@dataclass(frozen=True)
class JacocoClassCoverage:
    file: str
    package: str
    class_name: str
    source_file: str | None
    instruction_covered: int
    instruction_missed: int
    line_covered: int
    line_missed: int
    branch_covered: int
    branch_missed: int
    method_covered: int
    method_missed: int
    methods: tuple[JacocoMethodCoverage, ...]


@dataclass(frozen=True)
class JacocoEvidence:
    reports_found: int
    classes: tuple[JacocoClassCoverage, ...]


@dataclass(frozen=True)
class ChangedClassCoverage:
    source_file: str
    service: str | None
    expected_class_name: str
    matched_class_name: str | None
    report_file: str | None
    status: str
    line_coverage_percent: float | None
    branch_coverage_percent: float | None
    method_coverage_percent: float | None
    lines_covered: int
    lines_missed: int
    methods_covered: int
    methods_missed: int
    uncovered_methods: tuple[str, ...]


@dataclass(frozen=True)
class CoveragePolicy:
    minimum_line_coverage_for_changed_classes: float
    minimum_method_coverage_for_changed_classes: float
    minimum_branch_coverage_for_changed_classes: float
    require_test_changes_when_production_code_changes: bool
    require_related_test_change_when_production_code_changes: bool
    fail_on_unknown_coverage: bool
    fail_on_missing_surefire_evidence: bool
    fail_on_missing_jacoco_evidence: bool
    fail_on_maven_verification_failure: bool
    fail_on_test_failures: bool




@dataclass(frozen=True)
class RelatedTestEvidence:
    production_file: str
    expected_class_name: str
    expected_test_files: tuple[str, ...]
    matched_test_files: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class CoverageAssessment:
    schema_version: str
    coverage_status: str
    changed_production_files: tuple[str, ...]
    changed_test_files: tuple[str, ...]
    changed_services: tuple[str, ...]
    surefire_reports_found: int
    jacoco_reports_found: int
    test_total_count: int
    test_failure_count: int
    test_error_count: int
    test_skipped_count: int
    failed_test_suites: tuple[SurefireSuite, ...]
    test_execution_failures: tuple[str, ...]
    changed_class_coverage: tuple[ChangedClassCoverage, ...]
    related_test_evidence: tuple[RelatedTestEvidence, ...]
    covered_classes: tuple[str, ...]
    partially_covered_classes: tuple[str, ...]
    uncovered_classes: tuple[str, ...]
    unknown_coverage_files: tuple[str, ...]
    missing_related_test_files: tuple[str, ...]
    policy: CoveragePolicy
    policy_violations: tuple[str, ...]
    policy_warnings: tuple[str, ...]
    missing_test_scenarios: tuple[str, ...]
    recommended_tests: tuple[str, ...]
    confidence: str
    blocking_reasons: tuple[str, ...]
    merge_recommendation: str
    safety_boundary: str


def as_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {field_name: as_jsonable(getattr(value, field_name)) for field_name in value.__dataclass_fields__}
    if isinstance(value, tuple):
        return [as_jsonable(item) for item in value]
    if isinstance(value, list):
        return [as_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: as_jsonable(item) for key, item in value.items()}
    return value
