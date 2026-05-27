from __future__ import annotations

from dataclasses import dataclass

from .models import ChangedClassCoverage, CoverageAssessment, CoveragePolicy, GitDiffEvidence, JacocoClassCoverage, JacocoEvidence, SurefireEvidence
from .policy import DEFAULT_POLICY, evaluate_policy
from .related_tests import build_related_test_evidence

SCHEMA_VERSION = "1.0"
SAFETY_BOUNDARY = (
    "Read-only advisory output. This report does not authorize code mutation, test deletion, "
    "PR creation, deployment, secrets access, workflow permission escalation, or automatic remediation."
)


def _unique(values: list[str | None]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
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


def _percent(covered: int, missed: int) -> float | None:
    total = covered + missed
    if total == 0:
        return None
    return round((covered / total) * 100, 2)


def _class_status(coverage: JacocoClassCoverage | None) -> str:
    if coverage is None:
        return "unknown"
    if coverage.line_covered == 0 and coverage.method_covered == 0:
        return "uncovered"
    if coverage.line_missed > 0 or coverage.method_missed > 0 or coverage.branch_missed > 0:
        return "partial"
    return "covered"


def _uncovered_methods(coverage: JacocoClassCoverage) -> tuple[str, ...]:
    methods: list[str] = []
    for method in coverage.methods:
        if method.name in {"<init>", "<clinit>"}:
            continue
        has_executable_counters = (method.instruction_covered + method.instruction_missed + method.line_covered + method.line_missed) > 0
        if has_executable_counters and method.instruction_covered == 0 and method.line_covered == 0:
            methods.append(f"{method.name}{method.descriptor}")
    return tuple(methods)


@dataclass(frozen=True)
class CoverageMatch:
    coverage: JacocoClassCoverage | None
    strategy: str
    confidence: str
    candidates: tuple[str, ...]


def _class_name(coverage: JacocoClassCoverage) -> str:
    return coverage.class_name.replace("/", ".")


def _candidate_names(items: list[JacocoClassCoverage]) -> tuple[str, ...]:
    return tuple(sorted({_class_name(item) for item in items})[:10])


def _service_from_path(path: str) -> str | None:
    parts = path.split("/", 1)
    return parts[0] if parts else None


def _find_coverage_match(file_path: str, service: str | None, jacoco: JacocoEvidence) -> CoverageMatch:
    expected_class_name = _java_class_name_from_path(file_path)
    source_file_name = file_path.rsplit("/", 1)[-1]
    expected_package = ".".join(expected_class_name.split(".")[:-1])
    expected_package_slash = expected_package.replace(".", "/")
    service_name = service or _service_from_path(file_path)

    exact = [item for item in jacoco.classes if _class_name(item) == expected_class_name]
    if len(exact) == 1:
        return CoverageMatch(exact[0], "exact_class_name", "high", _candidate_names(exact))

    nested = [item for item in jacoco.classes if _class_name(item).split("$", 1)[0] == expected_class_name and "$" in _class_name(item)]
    if len(nested) == 1:
        confidence = "high" if service_name and service_name in nested[0].file else "medium"
        return CoverageMatch(nested[0], "nested_top_level_class", confidence, _candidate_names(nested))
    if len(nested) > 1:
        return CoverageMatch(None, "unmatched", "low", _candidate_names(nested))

    pkg_source = [
        item for item in jacoco.classes if (item.source_file == source_file_name and item.package == expected_package_slash)
    ]
    if len(pkg_source) == 1:
        return CoverageMatch(pkg_source[0], "package_sourcefilename", "high", _candidate_names(pkg_source))
    if len(pkg_source) > 1:
        return CoverageMatch(None, "unmatched", "low", _candidate_names(pkg_source))

    source_matches = [item for item in jacoco.classes if item.source_file == source_file_name]
    if service_name:
        service_scoped = [item for item in source_matches if service_name in item.file]
        if len(service_scoped) == 1:
            return CoverageMatch(service_scoped[0], "sourcefilename_service_scoped", "medium", _candidate_names(service_scoped))
        if len(service_scoped) > 1:
            return CoverageMatch(None, "unmatched", "low", _candidate_names(service_scoped))

    if len(source_matches) == 1:
        return CoverageMatch(source_matches[0], "sourcefilename_unscoped", "low", _candidate_names(source_matches))

    return CoverageMatch(None, "unmatched", "low", _candidate_names(source_matches))


def _changed_class_coverage(production_files: list[str], git: GitDiffEvidence, jacoco: JacocoEvidence) -> tuple[ChangedClassCoverage, ...]:
    service_by_path = {item.path: item.service for item in git.changed_files}
    results: list[ChangedClassCoverage] = []

    for file_path in production_files:
        expected_class_name = _java_class_name_from_path(file_path)
        match = _find_coverage_match(file_path, service_by_path.get(file_path), jacoco)
        coverage = match.coverage
        status = _class_status(coverage)
        uncovered_methods = _uncovered_methods(coverage) if coverage else ()

        results.append(
            ChangedClassCoverage(
                source_file=file_path,
                service=service_by_path.get(file_path),
                expected_class_name=expected_class_name,
                matched_class_name=coverage.class_name.replace("/", ".") if coverage else None,
                report_file=coverage.file if coverage else None,
                status=status,
                line_coverage_percent=_percent(coverage.line_covered, coverage.line_missed) if coverage else None,
                branch_coverage_percent=_percent(coverage.branch_covered, coverage.branch_missed) if coverage else None,
                method_coverage_percent=_percent(coverage.method_covered, coverage.method_missed) if coverage else None,
                lines_covered=coverage.line_covered if coverage else 0,
                lines_missed=coverage.line_missed if coverage else 0,
                methods_covered=coverage.method_covered if coverage else 0,
                methods_missed=coverage.method_missed if coverage else 0,
                mapping_strategy=match.strategy,
                mapping_confidence=match.confidence,
                mapping_candidates=match.candidates,
                uncovered_methods=uncovered_methods,
            )
        )

    return tuple(results)


def assess_coverage(
    git: GitDiffEvidence,
    surefire: SurefireEvidence,
    jacoco: JacocoEvidence,
    policy: CoveragePolicy = DEFAULT_POLICY,
    test_execution_failures: tuple[str, ...] = (),
) -> CoverageAssessment:
    production_files = [item.path for item in git.changed_files if item.category == "production-java"]
    test_files = [item.path for item in git.changed_files if item.category == "test-java"]
    changed_services = _unique([item.service for item in git.changed_files])
    changed_class_coverage = _changed_class_coverage(production_files, git, jacoco)
    related_test_evidence = build_related_test_evidence(production_files, test_files)

    covered_classes = [item.expected_class_name for item in changed_class_coverage if item.status == "covered"]
    partially_covered_classes = [item.expected_class_name for item in changed_class_coverage if item.status == "partial"]
    uncovered_classes = [item.expected_class_name for item in changed_class_coverage if item.status == "uncovered"]
    unknown_files = [item.source_file for item in changed_class_coverage if item.status == "unknown"]
    missing_related_test_files = [item.production_file for item in related_test_evidence if item.status == "missing"]

    missing_test_scenarios: list[str] = []
    recommended_tests: list[str] = []
    blocking_reasons: list[str] = []

    if production_files and not test_files:
        missing_test_scenarios.append("Production Java files changed, but no Java test files changed in the diff.")
        recommended_tests.append("Add or update unit tests for changed production classes.")

    for item in related_test_evidence:
        if item.status == "missing":
            missing_test_scenarios.append(f"Changed production class `{item.expected_class_name}` has no related changed test file.")
            recommended_tests.append(f"Add or update a related test for `{item.expected_class_name}`.")

    if production_files and jacoco.reports_found == 0:
        missing_test_scenarios.append("No JaCoCo XML reports were found, so changed-code coverage is unknown.")
        recommended_tests.append("Run service tests with JaCoCo XML report generation enabled.")

    for service in test_execution_failures:
        missing_test_scenarios.append(
            f"Maven verification failed for `{service}`, so test and coverage evidence may be incomplete."
        )
        recommended_tests.append(f"Fix Maven verification for `{service}` before trusting coverage results.")

    if production_files and surefire.reports_found == 0:
        missing_test_scenarios.append("No Surefire XML reports were found, so test execution evidence is missing.")
        recommended_tests.append("Run Maven tests and publish target/surefire-reports artifacts.")

    if surefire.total_failures > 0 or surefire.total_errors > 0:
        missing_test_scenarios.append("Surefire reported failing unit tests, so coverage evidence may not represent a valid passing build.")
        recommended_tests.append("Fix failing unit tests before trusting coverage results.")

    for class_coverage in changed_class_coverage:
        if class_coverage.status == "unknown":
            recommended_tests.append(f"Generate JaCoCo evidence for changed class `{class_coverage.expected_class_name}`.")
        elif class_coverage.status == "uncovered":
            blocking_reasons.append(f"Changed class `{class_coverage.expected_class_name}` appears uncovered.")
            recommended_tests.append(f"Add tests that execute `{class_coverage.expected_class_name}`.")
        elif class_coverage.status == "partial":
            recommended_tests.append(f"Review missing line/branch/method coverage for `{class_coverage.expected_class_name}`.")
            for method in class_coverage.uncovered_methods:
                recommended_tests.append(f"Add a test covering `{class_coverage.expected_class_name}.{method}`.")

    policy_violations, policy_warnings = evaluate_policy(
        policy=policy,
        production_files=production_files,
        test_files=test_files,
        surefire_reports_found=surefire.reports_found,
        jacoco_reports_found=jacoco.reports_found,
        test_failure_count=surefire.total_failures,
        test_error_count=surefire.total_errors,
        failed_test_suites=surefire.failed_suites,
        test_execution_failures=test_execution_failures,
        changed_class_coverage=changed_class_coverage,
        related_test_evidence=related_test_evidence,
    )
    blocking_reasons.extend(policy_violations)

    if policy_violations:
        coverage_status = "policy_violation"
        merge_recommendation = "manual_review"
        confidence = "medium"
    elif uncovered_classes:
        coverage_status = "insufficient"
        merge_recommendation = "block"
        confidence = "medium"
    elif production_files and (unknown_files or jacoco.reports_found == 0):
        coverage_status = "unknown"
        merge_recommendation = "manual_review"
        confidence = "low"
    elif production_files and partially_covered_classes:
        coverage_status = "partial"
        merge_recommendation = "manual_review"
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
        test_total_count=surefire.total_tests,
        test_failure_count=surefire.total_failures,
        test_error_count=surefire.total_errors,
        test_skipped_count=surefire.total_skipped,
        failed_test_suites=surefire.failed_suites,
        test_execution_failures=test_execution_failures,
        changed_class_coverage=changed_class_coverage,
        related_test_evidence=related_test_evidence,
        covered_classes=tuple(covered_classes),
        partially_covered_classes=tuple(partially_covered_classes),
        uncovered_classes=tuple(uncovered_classes),
        unknown_coverage_files=tuple(unknown_files),
        missing_related_test_files=tuple(missing_related_test_files),
        policy=policy,
        policy_violations=policy_violations,
        policy_warnings=policy_warnings,
        missing_test_scenarios=tuple(_unique(missing_test_scenarios) or ("No deterministic missing-test scenario was detected.",)),
        recommended_tests=tuple(_unique(recommended_tests) or ("No deterministic test recommendation was generated.",)),
        confidence=confidence,
        blocking_reasons=tuple(_unique(blocking_reasons) or ("No deterministic blocking reason was detected.",)),
        merge_recommendation=merge_recommendation,
        safety_boundary=SAFETY_BOUNDARY,
    )
