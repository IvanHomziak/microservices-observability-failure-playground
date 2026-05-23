from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from unit_test_coverage_agent.assessment import assess_coverage
from unit_test_coverage_agent.git_diff import classify_file
from unit_test_coverage_agent.jacoco_loader import load_jacoco_evidence
from unit_test_coverage_agent.models import GitDiffEvidence
from unit_test_coverage_agent.output_schema import assessment_to_contract, validate_contract
from unit_test_coverage_agent.patch_proposal import build_patch_proposal, patch_proposal_to_dict, render_patch_proposal_markdown
from unit_test_coverage_agent.prompt_builder import build_coverage_reasoning_prompt
from unit_test_coverage_agent.providers import get_provider
from unit_test_coverage_agent.renderer import render_markdown
from unit_test_coverage_agent.surefire_loader import load_surefire_evidence


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


JACOCO_WITH_METHODS = """<?xml version="1.0" encoding="UTF-8"?>
<report name="orders-service">
  <package name="com/example">
    <class name="com/example/OrderService" sourcefilename="OrderService.java">
      <method name="createOrder" desc="()V" line="10">
        <counter type="INSTRUCTION" missed="0" covered="8"/>
        <counter type="LINE" missed="0" covered="3"/>
      </method>
      <method name="cancelOrder" desc="()V" line="20">
        <counter type="INSTRUCTION" missed="7" covered="0"/>
        <counter type="LINE" missed="2" covered="0"/>
      </method>
      <counter type="INSTRUCTION" missed="8" covered="9"/>
      <counter type="LINE" missed="2" covered="4"/>
      <counter type="BRANCH" missed="1" covered="1"/>
      <counter type="METHOD" missed="1" covered="1"/>
    </class>
    <sourcefile name="OrderService.java"/>
  </package>
</report>
"""


def build_partial_contract() -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        write(root / "orders-service" / "target" / "site" / "jacoco" / "jacoco.xml", JACOCO_WITH_METHODS)
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
        return assessment_to_contract(assessment)


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

    def test_load_jacoco_evidence_includes_method_counters(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(root / "orders-service" / "target" / "site" / "jacoco" / "jacoco.xml", JACOCO_WITH_METHODS)

            evidence = load_jacoco_evidence(root)

            self.assertEqual(1, evidence.reports_found)
            self.assertEqual("com/example/OrderService", evidence.classes[0].class_name)
            self.assertEqual(4, evidence.classes[0].line_covered)
            self.assertEqual(2, len(evidence.classes[0].methods))
            self.assertEqual("cancelOrder", evidence.classes[0].methods[1].name)
            self.assertEqual(0, evidence.classes[0].methods[1].line_covered)

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
        self.assertEqual("unknown", contract["changed_class_coverage"][0]["status"])

    def test_assessment_partial_with_uncovered_method(self) -> None:
        contract = build_partial_contract()
        markdown = render_markdown(contract)

        self.assertEqual("partial", contract["coverage_status"])
        self.assertEqual("manual_review", contract["merge_recommendation"])
        self.assertIn("com.example.OrderService", contract["partially_covered_classes"])
        self.assertEqual("partial", contract["changed_class_coverage"][0]["status"])
        self.assertEqual(66.67, contract["changed_class_coverage"][0]["line_coverage_percent"])
        self.assertIn("cancelOrder()V", contract["changed_class_coverage"][0]["uncovered_methods"])
        self.assertIn("Changed class coverage", markdown)
        self.assertIn("cancelOrder()V", markdown)

    def test_assessment_sufficient_with_full_jacoco_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / "orders-service" / "target" / "site" / "jacoco" / "jacoco.xml",
                """<report name="orders-service"><package name="com/example"><class name="com/example/OrderService" sourcefilename="OrderService.java"><method name="createOrder" desc="()V" line="10"><counter type="LINE" missed="0" covered="3"/><counter type="INSTRUCTION" missed="0" covered="8"/></method><counter type="LINE" missed="0" covered="4"/><counter type="METHOD" missed="0" covered="1"/><counter type="BRANCH" missed="0" covered="0"/></class><sourcefile name="OrderService.java"/></package></report>""",
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
            self.assertFalse(validate_contract(contract))

    def test_prompt_builder_contains_safety_constraints(self) -> None:
        contract = build_partial_contract()
        prompt = build_coverage_reasoning_prompt(contract)

        self.assertIn("Reason only from the deterministic coverage evidence", prompt)
        self.assertIn("Do not invent files, classes, methods, tests, coverage percentages, or validation results", prompt)
        self.assertIn("Return only JSON", prompt)
        self.assertIn("cancelOrder", prompt)

    def test_deterministic_provider_returns_valid_contract_without_external_call(self) -> None:
        contract = build_partial_contract()
        provider = get_provider("deterministic")

        result = provider.refine(contract)

        self.assertEqual("deterministic", result.provider_name)
        self.assertFalse(result.used_external_call)
        self.assertFalse(validate_contract(result.contract))

    def test_langchain_provider_requires_api_key(self) -> None:
        contract = build_partial_contract()
        provider = get_provider("langchain-openai")

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                provider.refine(contract)

    def test_patch_proposal_generated_for_partial_coverage(self) -> None:
        contract = build_partial_contract()
        proposal = build_patch_proposal(contract)
        payload = patch_proposal_to_dict(proposal)
        markdown = render_patch_proposal_markdown(proposal)

        self.assertEqual("proposal_available", payload["proposal_status"])
        self.assertEqual("manual_review", payload["merge_recommendation"])
        self.assertEqual(1, len(payload["proposed_test_scenarios"]))
        scenario = payload["proposed_test_scenarios"][0]
        self.assertEqual("com.example.OrderService", scenario["production_class"])
        self.assertEqual("orders-service/src/test/java/com/example/OrderServiceTest.java", scenario["suggested_test_file"])
        self.assertIn("shouldCoverCancelOrder", scenario["suggested_test_methods"])
        self.assertIn("cd orders-service && mvn -B -ntp verify", payload["validation_commands"])
        self.assertIn("does not authorize code mutation", payload["safety_boundary"])
        self.assertIn("Unit Test Coverage Patch Proposal", markdown)
        self.assertIn("shouldCoverCancelOrder", markdown)


if __name__ == "__main__":
    unittest.main()
