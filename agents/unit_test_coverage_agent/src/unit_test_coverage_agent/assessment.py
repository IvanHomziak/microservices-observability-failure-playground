from __future__ import annotations

from .models import CoverageAssessment, GitDiffEvidence, JacocoEvidence, SurefireEvidence

SCHEMA_VERSION = "1.0"
SAFETY_BOUNDARY = (
    "Read-only advisory output. This report does not authorize code mutation, test deletion, "
    "PR creation, deployment, secrets access, workflow permission escalation, or automatic remediation."
)


def _unique(values: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return tuple(result)


def _java_class_name_from_path(path: str) -> str:
    marker = "/src/main/java/"
    if marker not in path:
        return path
    relative = path.split(marker, 1)[1]
    if relative.endswith(".java"):
        relative = relative[:-5]
    return relative.replace("/", ".")


def assess_coverage(git: GitDiffEvidence, surefire: SurefireEvidence, jacoco: JacocoEvidence) -> CoverageAssessment:
    production_files = [item.path for item in git.changed_files if item.category == "production-java"]
    test_files = [item.path for item in git.changed_files if item.category == "test-java"]
    changed_services = _unique([item.service for item in git.changed_files if item.service])

    jacoco_class_names = {item.class_name.replace("/", "."): item for item in jacoco.classes}
    covered_classes: list[str] = []
    uncovered_classes: list[str] = []
    unknown_files: list[str] = []

    for file_path in production_files:
        class_name = _java_class_name_from_path(file_path)
        coverage = jacoco_class_names.get(class_name)
        if coverage is None:
            unknown_files.append(file_path)
            continue
        if coverage.line_covered > 0 or coverage.method_covered > 0:
            covered_classes.append(class_name)
        else:
            uncovered_classes.append(class_name)

    missing_test_scenarios: list[str] = []
    recommended_tests: list[str] = []
    blocking_reasons: list[str] = []

    if production_files and not test_files:
        missing_test_scenarios.append("Production Java files changed, but no Java test files changed in the diff.")
        recommended_tests.append("Add or update unit tests for changed production classes.")

    if production_files and jacoco.reports_found == 0:
        missing_test_scenarios.append("No JaCoCo XML reports were found, so changed-code coverage is unknown.")
        recommended_tests.append("Run service tests with JaCoCo XML report generation enabled.")

    if production_files and surefire.reports_found == 0:
        missing_test_scenarios.append("No Surefire XML reports were found, so test execution evidence is missing.")
        recommended_tests.append("Run Maven tests and publish target/surefire-reports artifacts.")

    if uncovered_classes:
        blocking_reasons.append("At least one changed class appears uncovered according to JaCoCo evidence.")

    if production_files and not jacoco.reports_found:
        coverage_status = "unknown"
        merge_recommendation = "manual_review"
        confidence = "low"
    elif uncovered_classes:
        coverage_status = "insufficient"
        merge_recommendation = "block"
        confidence = "medium"
    elif production_files and covered_classes:
        coverage_status = "sufficient"
        merge_recommendation = "approve"
        confidence = "medium"
    elif production_files:
        coverage_status = "unknown"
        merge_recommendation = "manual_review"
        confidence = "low"
    else:
        coverage_status = "not_applicable"
        merge_recommendation = "approve"
        confidence = "medium"

    return CoverageAssessment(
        schema_version=SCHEMA_VERSION,
        coverage_status=coverage_status,
        changed_production_files=tuple(production_files),
        changed_test_files=tuple(test_files),
        changed_services=changed_services,
        surefire_reports_found=surefire.reports_found,
        jacoco_reports_found=jacoco.reports_found,
        covered_classes=tuple(covered_classes),
        uncovered_classes=tuple(uncovered_classes),
        unknown_coverage_files=tuple(unknown_files),
        missing_test_scenarios=tuple(missing_test_scenarios or ("No deterministic missing-test scenario was detected.",)),
        recommended_tests=tuple(recommended_tests or ("No deterministic test recommendation was generated.",)),
        confidence=confidence,
        blocking_reasons=tuple(blocking_reasons or ("No deterministic blocking reason was detected.",)),
        merge_recommendation=merge_recommendation,
        safety_boundary=SAFETY_BOUNDARY,
    )
