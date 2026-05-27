from __future__ import annotations

from .models import RelatedTestEvidence

TEST_SUFFIXES = ("Test", "Tests", "IT", "IntegrationTest")


def _class_name_from_production_path(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return name[:-5] if name.endswith(".java") else name


def _expected_test_files(production_file: str) -> tuple[str, ...]:
    if "/src/main/java/" not in production_file or not production_file.endswith(".java"):
        return ()

    class_name = _class_name_from_production_path(production_file)
    service_root, java_path = production_file.split('/src/main/java/', 1)
    package_parts = java_path.rsplit('/', 1)[0].split('/') if '/' in java_path else []

    candidates: list[str] = []

    # same package candidates
    for suffix in TEST_SUFFIXES:
        candidates.append(
            f"{service_root}/src/test/java/{'/'.join(package_parts)}/{class_name}{suffix}.java".replace('//','/')
        )

    # parent package variation for *Test only
    if len(package_parts) > 1:
        parent = '/'.join(package_parts[:-1])
        candidates.append(f"{service_root}/src/test/java/{parent}/{class_name}Test.java")

    return tuple(dict.fromkeys(candidates))


def build_related_test_evidence(production_files: list[str], test_files: list[str]) -> tuple[RelatedTestEvidence, ...]:
    normalized_tests = set(test_files)
    test_by_name: dict[str, list[str]] = {}
    for file in test_files:
        test_by_name.setdefault(file.rsplit('/', 1)[-1], []).append(file)

    evidence: list[RelatedTestEvidence] = []
    for production_file in production_files:
        class_name = _class_name_from_production_path(production_file)
        expected_files = _expected_test_files(production_file)

        if not expected_files:
            evidence.append(RelatedTestEvidence(production_file, class_name, (), (), 'not_applicable'))
            continue

        matched = [f for f in expected_files if f in normalized_tests]
        if not matched:
            for suffix in TEST_SUFFIXES:
                filename = f"{class_name}{suffix}.java"
                matched.extend(test_by_name.get(filename, []))

        status = 'matched' if matched else 'missing'
        evidence.append(
            RelatedTestEvidence(
                production_file=production_file,
                expected_class_name=class_name,
                expected_test_files=expected_files,
                matched_test_files=tuple(sorted(dict.fromkeys(matched))),
                status=status,
            )
        )
    return tuple(evidence)
