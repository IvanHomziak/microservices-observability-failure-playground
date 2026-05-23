from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from unit_test_coverage_agent.assessment import assess_coverage
from unit_test_coverage_agent.git_diff import classify_file
from unit_test_coverage_agent.jacoco_loader import load_jacoco_evidence
from unit_test_coverage_agent.models import GitDiffEvidence
from unit_test_coverage_agent.output_schema import assessment_to_contract, validate_contract
from unit_test_coverage_agent.surefire_loader import load_surefire_evidence


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestUnitTestCoverageAgent(unittest.TestCase):
    def test_classify_changed_files(self) -> None:
        self.assertEqual("production-java", classify_file("orders-service/src/main/java/com/example/OrderService.java").category)
        self.assertEqual("test-java", classify_file("orders-service/src/test/java/com/example/OrderServiceTest.java").category)
        self.assertEqual("build-config", classify_file("orders-service/pom.xml").category)
        self.assertEqual("workflow", classify_file(".github/workflows/unit-test-coverage-agent.yml").category)
        self.assertEqual("docs", classify_file("docs/example.md").category)

    def test_load_surefire_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / "orders-service" / "target" / "surefire-reports" / "TEST-com.example.OrderServiceTest.xml",
                '<testsuite tests="3" failures="1" errors="0" skipped="0" time="0.12"></testsuite>',
            )

            evidence = load_surefire_evidence(root)

            self.assertEqual(1, evidence.reports_found)
            self.assertEqual(3, evidence.suites[0].tests)
            self.assertEqual(1, evidence.suites[0].failures)

    def test_load_jacoco_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / "orders-service" / "target" / "site" / "jacoco" / "jacoco.xml",
                """<?xml version="1.0" encoding="UTF-8"?>
<report name="orders-service">
  <package name="com/example">
    <class name="com/example/OrderService" sourcefilename="OrderService.java">
      <counter type="INSTRUCTION" missed="1" covered="9"/>
      <counter type="LINE" missed="0" covered="4"/>
      <counter type="BRANCH" missed="0" covered="0"/>
      <counter type="METHOD" missed="0" covered="2"/>
    </class>
    <sourcefile name="OrderService.java"/>
  </package>
</report>
""",
            )

            evidence = load_jacoco_evidence(root)

            self.assertEqual(1, evidence.reports_found)
            self.assertEqual("com/example/OrderService", evidence.classes[0].class_name)
            self.assertEqual(4, evidence.classes[0].line_covered)

    def test_assessment_unknown_without_jacoco(self) -> None:
        git = GitDiffEvidence(
            base_ref="origin/main",
            head_ref="HEAD",
            raw_changed_files=("orders-service/src/main/java/com/example/OrderService.java",),
            changed_files=(classify_file("orders-service/src/main/java/com/example/OrderService.java"),),
        )
        from unit_test_coverage_agent.models import JacocoEvidence, SurefireEvidence

        assessment = assess_coverage(git, SurefireEvidence(0, ()), JacocoEvidence(0, ()))
        contract = assessment_to_contract(assessment)

        self.assertEqual("unknown", contract["coverage_status"])
        self.assertEqual("manual_review", contract["merge_recommendation"])
        self.assertFalse(validate_contract(contract))
        self.assertIn("orders-service/src/main/java/com/example/OrderService.java", contract["unknown_coverage_files"])

    def test_assessment_sufficient_with_jacoco_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / "orders-service" / "target" / "site" / "jacoco" / "jacoco.xml",
                """<report name="orders-service"><package name="com/example"><class name="com/example/OrderService" sourcefilename="OrderService.java"><counter type="LINE" missed="0" covered="4"/><counter type="METHOD" missed="0" covered="2"/></class><sourcefile name="OrderService.java"/></package></report>""",
            )
            git = GitDiffEvidence(
                base_ref="origin/main",
                head_ref="HEAD",
                raw_changed_files=(
                    "orders-service/src/main/java/com/example/OrderService.java",
                    "orders-service/src/test/java/com/example/OrderServiceTest.java",
                ),
                changed_files=(
                    classify_file("orders-service/src/main/java/com/example/OrderService.java"),
                    classify_file("orders-service/src/test/java/com/example/OrderServiceTest.java"),
                ),
            )
            from unit_test_coverage_agent.models import SurefireEvidence

            assessment = assess_coverage(git, SurefireEvidence(1, ()), load_jacoco_evidence(root))
            contract = assessment_to_contract(assessment)

            self.assertEqual("sufficient", contract["coverage_status"])
            self.assertEqual("approve", contract["merge_recommendation"])
            self.assertIn("com.example.OrderService", contract["covered_classes"])


if __name__ == "__main__":
    unittest.main()
