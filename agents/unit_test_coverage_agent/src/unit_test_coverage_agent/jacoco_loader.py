from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from .models import JacocoClassCoverage, JacocoEvidence


def _counter(element: ElementTree.Element, counter_type: str) -> tuple[int, int]:
    for counter in element.findall("counter"):
        if counter.attrib.get("type") == counter_type:
            covered = int(counter.attrib.get("covered", "0"))
            missed = int(counter.attrib.get("missed", "0"))
            return covered, missed
    return 0, 0


def load_jacoco_evidence(repository_root: Path) -> JacocoEvidence:
    classes: list[JacocoClassCoverage] = []

    for path in sorted(repository_root.glob("*/target/site/jacoco/jacoco.xml")):
        try:
            root = ElementTree.parse(path).getroot()
        except (ElementTree.ParseError, OSError):
            continue

        for package in root.findall("package"):
            package_name = package.attrib.get("name", "")
            source_files = {source.attrib.get("name") for source in package.findall("sourcefile")}
            for class_element in package.findall("class"):
                class_name = class_element.attrib.get("name", "")
                source_file = class_element.attrib.get("sourcefilename")
                instruction_covered, instruction_missed = _counter(class_element, "INSTRUCTION")
                line_covered, line_missed = _counter(class_element, "LINE")
                branch_covered, branch_missed = _counter(class_element, "BRANCH")
                method_covered, method_missed = _counter(class_element, "METHOD")

                classes.append(
                    JacocoClassCoverage(
                        file=str(path.relative_to(repository_root)),
                        package=package_name,
                        class_name=class_name,
                        source_file=source_file if source_file in source_files or source_file else source_file,
                        instruction_covered=instruction_covered,
                        instruction_missed=instruction_missed,
                        line_covered=line_covered,
                        line_missed=line_missed,
                        branch_covered=branch_covered,
                        branch_missed=branch_missed,
                        method_covered=method_covered,
                        method_missed=method_missed,
                    )
                )

    return JacocoEvidence(reports_found=len({item.file for item in classes}), classes=tuple(classes))
