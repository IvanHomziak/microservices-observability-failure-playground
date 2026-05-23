from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from .models import SurefireEvidence, SurefireSuite


def _int_attr(element: ElementTree.Element, name: str) -> int:
    raw = element.attrib.get(name, "0")
    try:
        return int(float(raw))
    except ValueError:
        return 0


def _float_attr(element: ElementTree.Element, name: str) -> float | None:
    raw = element.attrib.get(name)
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def load_surefire_evidence(repository_root: Path) -> SurefireEvidence:
    suites: list[SurefireSuite] = []
    for path in sorted(repository_root.glob("*/target/surefire-reports/TEST-*.xml")):
        try:
            root = ElementTree.parse(path).getroot()
        except (ElementTree.ParseError, OSError):
            continue

        suite_elements = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
        for suite in suite_elements:
            suites.append(
                SurefireSuite(
                    file=str(path.relative_to(repository_root)),
                    tests=_int_attr(suite, "tests"),
                    failures=_int_attr(suite, "failures"),
                    errors=_int_attr(suite, "errors"),
                    skipped=_int_attr(suite, "skipped"),
                    time=_float_attr(suite, "time"),
                )
            )

    return SurefireEvidence(reports_found=len(suites), suites=tuple(suites))
