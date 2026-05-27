from __future__ import annotations

from pathlib import Path

from .models import ChangedClassCoverage, CoveragePolicy, SurefireSuite

DEFAULT_POLICY = CoveragePolicy(
    minimum_line_coverage_for_changed_classes=70.0,
    minimum_method_coverage_for_changed_classes=70.0,
    require_test_changes_when_production_code_changes=True,
    fail_on_unknown_coverage=False,
    fail_on_missing_surefire_evidence=False,
    fail_on_missing_jacoco_evidence=False,
    fail_on_maven_verification_failure=False,
    fail_on_test_failures=False,
)


def _parse_bool(raw: str, *, field: str) -> bool:
    normalized = raw.strip().lower()
    if normalized in {"true", "yes", "1"}:
        return True
    if normalized in {"false", "no", "0"}:
        return False
    raise ValueError(f"Invalid boolean value for {field}: {raw}")


def _parse_float(raw: str, *, field: str) -> float:
    try:
        value = float(raw.strip())
    except ValueError as exc:
        raise ValueError(f"Invalid numeric value for {field}: {raw}") from exc
    if value < 0 or value > 100:
        raise ValueError(f"Policy percentage must be between 0 and 100 for {field}: {value}")
    return value


def _read_simple_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Invalid policy line {line_number}: expected 'key: value'")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid policy line {line_number}: blank key")
        if "#" in value:
            value = value.split("#", 1)[0].strip()
        values[key] = value
    return values


def load_policy(repository_root: Path, policy_path: Path | None = None) -> CoveragePolicy:
    if policy_path is not None:
        path = policy_path
        if not path.exists():
            raise FileNotFoundError(f"Explicit coverage policy file does not exist: {path}")
    else:
        path = repository_root / "coverage-policy.yml"

    raw = _read_simple_yaml(path)

    allowed = set(DEFAULT_POLICY.__dataclass_fields__.keys())
    unknown = sorted(set(raw.keys()) - allowed)
    if unknown:
        raise ValueError(f"Unknown coverage policy keys: {', '.join(unknown)}")

    return CoveragePolicy(
        minimum_line_coverage_for_changed_classes=_parse_float(
            raw.get(
                "minimum_line_coverage_for_changed_classes",
                str(DEFAULT_POLICY.minimum_line_coverage_for_changed_classes),
            ),
            field="minimum_line_coverage_for_changed_classes",
        ),
        minimum_method_coverage_for_changed_classes=_parse_float(
            raw.get(
                "minimum_method_coverage_for_changed_classes",
                str(DEFAULT_POLICY.minimum_method_coverage_for_changed_classes),
            ),
            field="minimum_method_coverage_for_changed_classes",
        ),
        require_test_changes_when_production_code_changes=_parse_bool(
            raw.get(
                "require_test_changes_when_production_code_changes",
                str(DEFAULT_POLICY.require_test_changes_when_production_code_changes),
            ),
            field="require_test_changes_when_production_code_changes",
        ),
        fail_on_unknown_coverage=_parse_bool(
            raw.get("fail_on_unknown_coverage", str(DEFAULT_POLICY.fail_on_unknown_coverage)),
            field="fail_on_unknown_coverage",
        ),
        fail_on_missing_surefire_evidence=_parse_bool(
            raw.get(
                "fail_on_missing_surefire_evidence",
                str(DEFAULT_POLICY.fail_on_missing_surefire_evidence),
            ),
            field="fail_on_missing_surefire_evidence",
        ),
        fail_on_missing_jacoco_evidence=_parse_bool(
            raw.get(
                "fail_on_missing_jacoco_evidence",
                str(DEFAULT_POLICY.fail_on_missing_jacoco_evidence),
            ),
            field="fail_on_missing_jacoco_evidence",
        ),
        fail_on_maven_verification_failure=_parse_bool(
            raw.get(
                "fail_on_maven_verification_failure",
                str(DEFAULT_POLICY.fail_on_maven_verification_failure),
            ),
            field="fail_on_maven_verification_failure",
        ),
        fail_on_test_failures=_parse_bool(
            raw.get("fail_on_test_failures", str(DEFAULT_POLICY.fail_on_test_failures)),
            field="fail_on_test_failures",
        ),
    )


def evaluate_policy(
    *,
    policy: CoveragePolicy,
    production_files: list[str],
    test_files: list[str],
    surefire_reports_found: int,
    jacoco_reports_found: int,
    changed_class_coverage: tuple[ChangedClassCoverage, ...],
    test_execution_failures: list[str] | tuple[str, ...],
    test_failure_count: int = 0,
    test_error_count: int = 0,
    failed_test_suites: tuple[SurefireSuite, ...] = (),
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    violations: list[str] = []
    warnings: list[str] = []

    if policy.require_test_changes_when_production_code_changes and production_files and not test_files:
        violations.append("Policy violation: production Java files changed, but no Java test files changed.")

    if policy.fail_on_missing_surefire_evidence and production_files and surefire_reports_found == 0:
        violations.append("Policy violation: Surefire XML evidence is required but was not found.")
    elif production_files and surefire_reports_found == 0:
        warnings.append("Policy warning: Surefire XML evidence is missing.")

    if policy.fail_on_missing_jacoco_evidence and production_files and jacoco_reports_found == 0:
        violations.append("Policy violation: JaCoCo XML evidence is required but was not found.")
    elif production_files and jacoco_reports_found == 0:
        warnings.append("Policy warning: JaCoCo XML evidence is missing.")

    for service in test_execution_failures:
        message = (
            f"Maven verification failed for `{service}`, so coverage evidence may be incomplete or unreliable."
        )
        if policy.fail_on_maven_verification_failure:
            violations.append(f"Policy violation: {message}")
        else:
            warnings.append(f"Policy warning: {message}")


    if test_failure_count > 0 or test_error_count > 0:
        message = (
            f"unit tests failed with {test_failure_count} failure(s) and {test_error_count} error(s)."
        )
        suite_files = ", ".join(sorted({suite.file for suite in failed_test_suites}))
        if policy.fail_on_test_failures:
            violations.append(f"Policy violation: {message}")
            if suite_files:
                violations.append(f"Policy violation: failing Surefire suites: {suite_files}")
        else:
            warnings.append(f"Policy warning: {message}")

    for item in changed_class_coverage:
        if item.status == "unknown":
            message = f"Changed class `{item.expected_class_name}` has unknown coverage."
            if policy.fail_on_unknown_coverage:
                violations.append(f"Policy violation: {message}")
            else:
                warnings.append(f"Policy warning: {message}")
            continue

        if item.line_coverage_percent is not None and item.line_coverage_percent < policy.minimum_line_coverage_for_changed_classes:
            violations.append(
                "Policy violation: "
                f"changed class `{item.expected_class_name}` line coverage is "
                f"{item.line_coverage_percent}% below required {policy.minimum_line_coverage_for_changed_classes}%."
            )

        if item.method_coverage_percent is not None and item.method_coverage_percent < policy.minimum_method_coverage_for_changed_classes:
            violations.append(
                "Policy violation: "
                f"changed class `{item.expected_class_name}` method coverage is "
                f"{item.method_coverage_percent}% below required {policy.minimum_method_coverage_for_changed_classes}%."
            )

    return tuple(dict.fromkeys(violations)), tuple(dict.fromkeys(warnings))
