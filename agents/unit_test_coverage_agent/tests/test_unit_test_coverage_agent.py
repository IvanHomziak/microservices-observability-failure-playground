from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from unit_test_coverage_agent.affected_services import detect_affected_services
from unit_test_coverage_agent.assessment import assess_coverage
from unit_test_coverage_agent.enforce_policy import enforce_policy
from unit_test_coverage_agent.git_diff import classify_file
from unit_test_coverage_agent.jacoco_loader import load_jacoco_evidence
from unit_test_coverage_agent.models import ChangedFile, CoveragePolicy, GitDiffEvidence
from unit_test_coverage_agent.output_schema import assessment_to_contract, validate_contract
from unit_test_coverage_agent.patch_proposal import build_patch_proposal, patch_proposal_to_dict, render_patch_proposal_markdown
from unit_test_coverage_agent.policy import load_policy
from unit_test_coverage_agent.pr_comment import COMMENT_MARKER, render_pr_comment
from unit_test_coverage_agent.pr_summary_comment import _truncate_markdown, render_pr_summary_comment
from unit_test_coverage_agent.prompt_builder import build_coverage_reasoning_prompt
from unit_test_coverage_agent.providers import LangChainOpenAICoverageProvider, get_provider
from unit_test_coverage_agent.renderer import render_markdown
from unit_test_coverage_agent.related_tests import build_related_test_evidence
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

        assessment = assess_coverage(git, SurefireEvidence(1, (), total_tests=1), load_jacoco_evidence(root))
        return assessment_to_contract(assessment)


class TestUnitTestCoverageAgent(unittest.TestCase):
    def test_classify_changed_files(self) -> None:
        self.assertEqual("production-java", classify_file("orders-service/src/main/java/com/example/OrderService.java").category)
        self.assertEqual("test-java", classify_file("orders-service/src/test/java/com/example/OrderServiceTest.java").category)
        self.assertEqual("build-config", classify_file("orders-service/pom.xml").category)
        self.assertEqual("workflow", classify_file(".github/workflows/unit-test-coverage-agent.yml").category)
        self.assertEqual("docs", classify_file("docs/example.md").category)


    def test_detect_affected_services_service_local_java_change(self) -> None:
        git = GitDiffEvidence(
            base_ref="origin/main",
            head_ref="HEAD",
            raw_changed_files=("orders-service/src/main/java/com/example/OrderService.java",),
            changed_files=(classify_file("orders-service/src/main/java/com/example/OrderService.java"),),
        )
        self.assertEqual(("orders-service",), detect_affected_services(git))

    def test_detect_affected_services_global_change_returns_all_services(self) -> None:
        git = GitDiffEvidence(
            base_ref="origin/main",
            head_ref="HEAD",
            raw_changed_files=("agents/unit_test_coverage_agent/src/unit_test_coverage_agent/main.py",),
            changed_files=(classify_file("agents/unit_test_coverage_agent/src/unit_test_coverage_agent/main.py"),),
        )
        self.assertEqual(
            ("api-gateway", "audit-service", "inventory-service", "notification-service", "orders-service", "payments-service"),
            detect_affected_services(git),
        )

    def test_detect_affected_services_docs_only_returns_empty(self) -> None:
        git = GitDiffEvidence(
            base_ref="origin/main",
            head_ref="HEAD",
            raw_changed_files=("docs/example.md",),
            changed_files=(classify_file("docs/example.md"),),
        )
        self.assertEqual((), detect_affected_services(git))

    def test_detect_affected_services_global_workflow_and_policy_changes_return_all_services(self) -> None:
        for changed_path in (".github/workflows/unit-test-coverage-pr-agent.yml", "coverage-policy-pr.yml"):
            git = GitDiffEvidence(
                base_ref="origin/main",
                head_ref="HEAD",
                raw_changed_files=(changed_path,),
                changed_files=(classify_file(changed_path),),
            )
            self.assertEqual(
                ("api-gateway", "audit-service", "inventory-service", "notification-service", "orders-service", "payments-service"),
                detect_affected_services(git),
            )

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
            self.assertEqual(3, evidence.total_tests)
            self.assertEqual(1, evidence.total_failures)
            self.assertEqual(0, evidence.total_errors)
            self.assertEqual(1, len(evidence.failed_suites))


    def test_load_surefire_evidence_without_failures_has_empty_failed_suites(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / "orders-service" / "target" / "surefire-reports" / "TEST-com.example.OrderServiceTest.xml",
                '<testsuite tests="4" failures="0" errors="0" skipped="1" time="0.12"></testsuite>',
            )

            evidence = load_surefire_evidence(root)

            self.assertEqual(4, evidence.total_tests)
            self.assertEqual(0, evidence.total_failures)
            self.assertEqual(0, evidence.total_errors)
            self.assertEqual(1, evidence.total_skipped)
            self.assertEqual((), evidence.failed_suites)

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
        self.assertEqual((), assessment.test_execution_failures)
        contract = assessment_to_contract(assessment)

        self.assertEqual("policy_violation", contract["coverage_status"])
        self.assertEqual("manual_review", contract["merge_recommendation"])
        self.assertFalse(validate_contract(contract))
        self.assertIn("orders-service/src/main/java/com/example/OrderService.java", contract["unknown_coverage_files"])
        self.assertEqual("unknown", contract["changed_class_coverage"][0]["status"])
        self.assertTrue(contract["policy_violations"])
        self.assertTrue(contract["policy_warnings"])

    def test_assessment_deleted_production_file_affects_service_but_not_coverage_or_no_test_violation(self) -> None:
        changed = ChangedFile(
            path="orders-service/src/main/java/com/example/DeletedFeature.java",
            category="production-java",
            service="orders-service",
            change_status="deleted",
        )
        git = GitDiffEvidence(
            base_ref="origin/main",
            head_ref="HEAD",
            raw_changed_files=(changed.path,),
            changed_files=(changed,),
        )
        from unit_test_coverage_agent.models import JacocoEvidence, SurefireEvidence

        self.assertEqual(("orders-service",), detect_affected_services(git))
        contract = assessment_to_contract(assess_coverage(git, SurefireEvidence(0, ()), JacocoEvidence(0, ())))
        self.assertEqual(["orders-service/src/main/java/com/example/DeletedFeature.java"], contract["deleted_production_files"])
        self.assertEqual([], contract["coverage_relevant_production_files"])
        self.assertEqual([], contract["changed_class_coverage"])
        self.assertNotIn(
            "Policy violation: production Java files changed, but no Java test files changed.",
            contract["policy_violations"],
        )
        self.assertEqual("not_applicable", contract["coverage_status"])

    def test_assessment_added_and_modified_production_files_are_coverage_relevant(self) -> None:
        added = ChangedFile(
            path="orders-service/src/main/java/com/example/NewFeature.java",
            category="production-java",
            service="orders-service",
            change_status="added",
        )
        modified = ChangedFile(
            path="orders-service/src/main/java/com/example/ExistingFeature.java",
            category="production-java",
            service="orders-service",
            change_status="modified",
        )
        git = GitDiffEvidence("origin/main", "HEAD", (added, modified), (added.path, modified.path))
        from unit_test_coverage_agent.models import JacocoEvidence, SurefireEvidence

        contract = assessment_to_contract(assess_coverage(git, SurefireEvidence(0, ()), JacocoEvidence(0, ())))
        self.assertEqual([added.path, modified.path], contract["coverage_relevant_production_files"])
        self.assertEqual([], contract["deleted_production_files"])
        self.assertEqual(("orders-service",), detect_affected_services(git))

    def test_assessment_partial_with_uncovered_method(self) -> None:
        contract = build_partial_contract()
        markdown = render_markdown(contract)

        self.assertEqual("policy_violation", contract["coverage_status"])
        self.assertEqual("manual_review", contract["merge_recommendation"])
        self.assertIn("com.example.OrderService", contract["partially_covered_classes"])
        self.assertEqual("partial", contract["changed_class_coverage"][0]["status"])
        self.assertEqual("exact_class_name", contract["changed_class_coverage"][0]["mapping_strategy"])
        self.assertEqual("high", contract["changed_class_coverage"][0]["mapping_confidence"])
        self.assertEqual(66.67, contract["changed_class_coverage"][0]["line_coverage_percent"])
        self.assertIn("cancelOrder()V", contract["changed_class_coverage"][0]["uncovered_methods"])
        self.assertIn("Changed class coverage", markdown)
        self.assertIn("Coverage mapping details", markdown)
        self.assertIn("Mapping | Confidence", markdown)
        self.assertIn("Coverage policy", markdown)
        self.assertIn("Policy violations", markdown)
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

            assessment = assess_coverage(git, SurefireEvidence(1, (), total_tests=1), load_jacoco_evidence(root))
            contract = assessment_to_contract(assessment)

            self.assertEqual("sufficient", contract["coverage_status"])
            self.assertEqual("approve", contract["merge_recommendation"])
            self.assertIn("com.example.OrderService", contract["covered_classes"])
            self.assertFalse(validate_contract(contract))

    def test_nested_class_mapping_strategy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / "orders-service" / "target" / "site" / "jacoco" / "jacoco.xml",
                """<report name="orders-service"><package name="com/example"><class name="com/example/Foo$Inner" sourcefilename="Foo.java"><counter type="LINE" missed="0" covered="2"/><counter type="METHOD" missed="0" covered="1"/><counter type="BRANCH" missed="0" covered="0"/></class><sourcefile name="Foo.java"/></package></report>""",
            )
            git = GitDiffEvidence(
                base_ref="origin/main",
                head_ref="HEAD",
                raw_changed_files=("orders-service/src/main/java/com/example/Foo.java",),
                changed_files=(classify_file("orders-service/src/main/java/com/example/Foo.java"),),
            )
            from unit_test_coverage_agent.models import SurefireEvidence

            contract = assessment_to_contract(assess_coverage(git, SurefireEvidence(1, (), total_tests=1), load_jacoco_evidence(root)))
            row = contract["changed_class_coverage"][0]
            self.assertEqual("com.example.Foo$Inner", row["matched_class_name"])
            self.assertEqual("nested_top_level_class", row["mapping_strategy"])
            self.assertIn(row["mapping_confidence"], {"high", "medium"})
            self.assertNotEqual("unknown", row["status"])

    def test_service_scoped_sourcefilename_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(root / "orders-service" / "target" / "site" / "jacoco" / "jacoco.xml", """<report><package name="a/b"><class name="a/b/OtherOrder" sourcefilename="Foo.java"><counter type="LINE" missed="0" covered="1"/><counter type="METHOD" missed="0" covered="1"/><counter type="BRANCH" missed="0" covered="0"/></class><sourcefile name="Foo.java"/></package></report>""")
            write(root / "payments-service" / "target" / "site" / "jacoco" / "jacoco.xml", """<report><package name="x/y"><class name="x/y/OtherPayment" sourcefilename="Foo.java"><counter type="LINE" missed="0" covered="1"/><counter type="METHOD" missed="0" covered="1"/><counter type="BRANCH" missed="0" covered="0"/></class><sourcefile name="Foo.java"/></package></report>""")
            git = GitDiffEvidence("origin/main", "HEAD", (classify_file("orders-service/src/main/java/com/example/Foo.java"),), ("orders-service/src/main/java/com/example/Foo.java",))
            from unit_test_coverage_agent.models import SurefireEvidence
            contract = assessment_to_contract(assess_coverage(git, SurefireEvidence(1, (), total_tests=1), load_jacoco_evidence(root)))
            row = contract["changed_class_coverage"][0]
            self.assertEqual("sourcefilename_service_scoped", row["mapping_strategy"])
            self.assertEqual("a.b.OtherOrder", row["matched_class_name"])

    def test_ambiguous_sourcefilename_unmatched(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(root / "orders-service" / "target" / "site" / "jacoco" / "jacoco.xml", """<report><package name="a/b"><class name="a/b/FooA" sourcefilename="Foo.java"><counter type="LINE" missed="0" covered="1"/><counter type="METHOD" missed="0" covered="1"/><counter type="BRANCH" missed="0" covered="0"/></class><sourcefile name="Foo.java"/></package></report>""")
            write(root / "payments-service" / "target" / "site" / "jacoco" / "jacoco.xml", """<report><package name="c/d"><class name="c/d/FooB" sourcefilename="Foo.java"><counter type="LINE" missed="0" covered="1"/><counter type="METHOD" missed="0" covered="1"/><counter type="BRANCH" missed="0" covered="0"/></class><sourcefile name="Foo.java"/></package></report>""")
            git = GitDiffEvidence(
                "origin/main",
                "HEAD",
                (ChangedFile(path="src/main/java/com/example/Foo.java", category="production-java", service=None),),
                ("src/main/java/com/example/Foo.java",),
            )
            from unit_test_coverage_agent.models import SurefireEvidence
            contract = assessment_to_contract(assess_coverage(git, SurefireEvidence(1, (), total_tests=1), load_jacoco_evidence(root)))
            row = contract["changed_class_coverage"][0]
            self.assertEqual("unmatched", row["mapping_strategy"])
            self.assertEqual("unknown", row["status"])
            self.assertIn("a.b.FooA", row["mapping_candidates"])
            self.assertIn("c.d.FooB", row["mapping_candidates"])



    def test_pr_summary_comment_contains_marker_and_summary(self) -> None:
        contract = build_partial_contract()
        patch = {"proposal_status": "proposal_available", "proposed_test_scenarios": [{"production_class": "com.example.OrderService", "suggested_test_file": "OrderServiceTest.java"}]}
        comment = render_pr_summary_comment(contract, patch)
        self.assertIn(COMMENT_MARKER, comment)
        self.assertIn("**Status:** `policy_violation`", comment)
        self.assertIn("**Recommendation:** `manual_review`", comment)
        self.assertIn("| Policy violations |", comment)
        self.assertIn("| Policy warnings |", comment)

    def test_pr_summary_comment_truncates_lists_and_details(self) -> None:
        contract = build_partial_contract()
        contract["policy_violations"] = [f"violation-{i}" for i in range(25)]
        full_md = "x" * 200
        comment = render_pr_summary_comment(contract, {}, full_report_markdown=full_md, max_full_report_chars=50, max_inline_items=20)
        self.assertIn("violation-0", comment)
        self.assertIn("violation-19", comment)
        self.assertNotIn("violation-24", comment)
        self.assertIn("Only first 20 items shown", comment)
        self.assertIn("<details>", comment)
        self.assertIn("...truncated...", comment)

    def test_pr_summary_comment_includes_mapping_and_test_execution_and_safety(self) -> None:
        contract = build_partial_contract()
        contract["test_total_count"] = 11
        contract["test_failure_count"] = 1
        contract["test_error_count"] = 2
        contract["test_skipped_count"] = 3
        contract["failed_test_suites"] = [{"file": "TEST-a.xml", "tests": 1, "failures": 1, "errors": 0, "skipped": 0}]
        contract["related_test_evidence"] = [{
            "production_file": "orders-service/src/main/java/com/example/OrderService.java",
            "expected_class_name": "com.example.OrderService",
            "expected_test_files": ["OrderServiceTest.java"],
            "matched_test_files": ["OrderServiceTest.java"],
            "status": "matched",
        }]
        patch = {"proposal_status": "proposal_available", "proposed_test_scenarios": [{"production_class": "com.example.OrderService", "suggested_test_file": "OrderServiceTest.java"}],}
        comment = render_pr_summary_comment(contract, patch, patch_proposal_markdown="proposal")
        self.assertIn("Changed class coverage", comment)
        self.assertIn("exact_class_name", comment)
        self.assertIn("high", comment)
        self.assertIn("### Test execution", comment)
        self.assertIn("### Failed test suites", comment)
        self.assertIn("### Related test evidence", comment)
        self.assertIn("Patch proposal details", comment)
        self.assertIn("does not authorize code mutation", comment)

    def test_truncate_markdown(self) -> None:
        self.assertEqual("abc", _truncate_markdown("abc", 10))
        self.assertIn("...truncated...", _truncate_markdown("a" * 20, 5))

    def test_policy_loader_reads_simple_yaml_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            policy_path = root / "coverage-policy.yml"
            write(
                policy_path,
                """minimum_line_coverage_for_changed_classes: 80
minimum_method_coverage_for_changed_classes: 75
minimum_branch_coverage_for_changed_classes: 55
require_test_changes_when_production_code_changes: false
fail_on_unknown_coverage: true
fail_on_missing_surefire_evidence: true
fail_on_missing_jacoco_evidence: true
fail_on_maven_verification_failure: true
fail_on_test_failures: true
""",
            )

            policy = load_policy(root)

            self.assertEqual(80.0, policy.minimum_line_coverage_for_changed_classes)
            self.assertEqual(75.0, policy.minimum_method_coverage_for_changed_classes)
            self.assertEqual(55.0, policy.minimum_branch_coverage_for_changed_classes)
            self.assertFalse(policy.require_test_changes_when_production_code_changes)
            self.assertTrue(policy.fail_on_unknown_coverage)
            self.assertTrue(policy.fail_on_missing_surefire_evidence)
            self.assertTrue(policy.fail_on_missing_jacoco_evidence)
            self.assertTrue(policy.fail_on_maven_verification_failure)
            self.assertTrue(policy.fail_on_test_failures)

    def test_policy_loader_fails_when_explicit_policy_path_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaises(FileNotFoundError):
                load_policy(root, root / "missing-policy.yml")

    def test_policy_enforcement_fails_on_policy_violations(self) -> None:
        contract = build_partial_contract()

        passed, violations, warnings = enforce_policy(contract)

        self.assertFalse(passed)
        self.assertTrue(violations)
        self.assertIsInstance(warnings, list)

    def test_policy_enforcement_passes_without_policy_violations(self) -> None:
        contract = build_partial_contract()
        contract["policy_violations"] = []
        contract["coverage_status"] = "partial"

        passed, violations, warnings = enforce_policy(contract)

        self.assertTrue(passed)
        self.assertEqual([], violations)
        self.assertIsInstance(warnings, list)

    def test_prompt_builder_contains_safety_constraints(self) -> None:
        contract = build_partial_contract()
        prompt = build_coverage_reasoning_prompt(contract)

        self.assertIn("Reason only from the deterministic coverage evidence", prompt)
        self.assertIn("Do not invent files, classes, methods, tests, coverage percentages", prompt)
        self.assertIn("Return JSON only", prompt)
        self.assertIn("Pass/fail authority belongs only to deterministic policy evaluation", prompt)
        self.assertIn("Do not change coverage_status, merge_recommendation, policy_violations, or policy_warnings", prompt)
        self.assertIn("cancelOrder", prompt)
        self.assertIn("policy_violations", prompt)

    def test_deterministic_provider_returns_valid_contract_without_external_call(self) -> None:
        contract = build_partial_contract()
        provider = get_provider("deterministic")

        with patch.dict(os.environ, {}, clear=True):
            result = provider.refine(contract)

        self.assertEqual("deterministic", result.provider_name)
        self.assertIsNone(result.model)
        self.assertFalse(result.used_external_call)
        self.assertFalse(validate_contract(result.contract))

    def test_langchain_provider_requires_api_key(self) -> None:
        contract = build_partial_contract()
        provider = get_provider("langchain-openai")

        with patch.dict(os.environ, {"OPENAI_MODEL": "gpt-test", "SECRET_VALUE": "must-not-leak"}, clear=True):
            with self.assertRaises(RuntimeError) as context:
                provider.refine(contract)

        message = str(context.exception)
        self.assertIn("OPENAI_API_KEY is required for provider=langchain-openai", message)
        self.assertNotIn("must-not-leak", message)
        self.assertNotIn("SECRET_VALUE", message)

    def test_invalid_provider_name_fails_clearly(self) -> None:
        with self.assertRaises(ValueError) as context:
            get_provider("unsupported-provider")

        self.assertIn("Unsupported coverage reasoning provider", str(context.exception))

    def test_langchain_provider_uses_openai_model_override_without_startup_validation(self) -> None:
        with patch.dict(os.environ, {"OPENAI_MODEL": "gpt-custom-model"}, clear=True):
            provider = get_provider("langchain-openai")

        self.assertIsInstance(provider, LangChainOpenAICoverageProvider)
        self.assertEqual("gpt-custom-model", provider.model)

    def test_langchain_provider_rejects_invalid_llm_json_response(self) -> None:
        contract = build_partial_contract()
        provider = LangChainOpenAICoverageProvider(model="gpt-test")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch.object(provider, "_invoke", return_value=json.dumps({"coverage_status": "approve everything"})):
                with self.assertRaises(RuntimeError) as context:
                    provider.refine(contract)

        message = str(context.exception)
        self.assertIn("LangChain provider returned invalid coverage contract", message)
        self.assertIn("Missing required field", message)
        self.assertNotIn("test-key", message)

    def test_langchain_provider_rejects_authoritative_policy_changes(self) -> None:
        contract = build_partial_contract()
        modified = dict(contract)
        modified["policy_violations"] = []
        provider = LangChainOpenAICoverageProvider(model="gpt-test")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch.object(provider, "_invoke", return_value=json.dumps(modified)):
                with self.assertRaises(RuntimeError) as context:
                    provider.refine(contract)

        self.assertIn("policy_violations must remain deterministic", str(context.exception))

    def test_langchain_provider_merges_only_advisory_fields(self) -> None:
        contract = build_partial_contract()
        modified = dict(contract)
        modified["recommended_tests"] = ["Add focused assertions for cancelOrder error handling."]
        provider = LangChainOpenAICoverageProvider(model="gpt-test")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch.object(provider, "_invoke", return_value=json.dumps(modified)):
                result = provider.refine(contract)

        self.assertTrue(result.used_external_call)
        self.assertEqual("langchain-openai", result.provider_name)
        self.assertEqual("gpt-test", result.model)
        self.assertEqual(contract["coverage_status"], result.contract["coverage_status"])
        self.assertEqual(contract["merge_recommendation"], result.contract["merge_recommendation"])
        self.assertEqual(contract["policy_violations"], result.contract["policy_violations"])
        self.assertEqual(["Add focused assertions for cancelOrder error handling."], result.contract["recommended_tests"])
        self.assertFalse(validate_contract(result.contract))

    def test_output_schema_rejects_invalid_authoritative_fields_and_safety_boundary(self) -> None:
        contract = build_partial_contract()
        contract["coverage_status"] = "green"
        contract["merge_recommendation"] = "merge_now"
        contract["policy_violations"] = "none"
        contract["policy_warnings"] = "none"
        contract["safety_boundary"] = "advisory report"

        errors = validate_contract(contract)

        self.assertTrue(any("Invalid coverage_status" in error for error in errors))
        self.assertTrue(any("Invalid merge_recommendation" in error for error in errors))
        self.assertTrue(any("Invalid type for policy_violations" in error for error in errors))
        self.assertTrue(any("Invalid type for policy_warnings" in error for error in errors))
        self.assertTrue(any("safety_boundary" in error for error in errors))

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

    def test_pr_comment_is_rendered_from_validated_artifacts(self) -> None:
        contract = build_partial_contract()
        proposal = patch_proposal_to_dict(build_patch_proposal(contract))
        comment = render_pr_comment(contract, proposal)

        self.assertIn(COMMENT_MARKER, comment)
        self.assertIn("Unit Test Coverage Agent", comment)
        self.assertIn("**Status:** `policy_violation`", comment)
        self.assertIn("Policy violations", comment)
        self.assertIn("Proposal status", comment)
        self.assertIn("does not authorize code mutation", comment)


    def test_assessment_maven_failure_can_be_policy_violation(self) -> None:
        git = GitDiffEvidence(
            base_ref="origin/main",
            head_ref="HEAD",
            raw_changed_files=("orders-service/src/main/java/com/example/OrderService.java",),
            changed_files=(classify_file("orders-service/src/main/java/com/example/OrderService.java"),),
        )
        from unit_test_coverage_agent.models import JacocoEvidence, SurefireEvidence

        strict = CoveragePolicy(
            minimum_line_coverage_for_changed_classes=70.0,
            minimum_method_coverage_for_changed_classes=70.0,
            minimum_branch_coverage_for_changed_classes=60.0,
            require_test_changes_when_production_code_changes=False,
            require_related_test_change_when_production_code_changes=True,
            fail_on_unknown_coverage=False,
            fail_on_missing_surefire_evidence=False,
            fail_on_missing_jacoco_evidence=False,
            fail_on_maven_verification_failure=True,
            fail_on_test_failures=True,
        )
        assessment = assess_coverage(
            git,
            SurefireEvidence(0, ()),
            JacocoEvidence(0, ()),
            strict,
            test_execution_failures=("orders-service",),
        )
        contract = assessment_to_contract(assessment)

        self.assertIn("orders-service", contract["test_execution_failures"])
        self.assertTrue(any("Maven verification failed for `orders-service`" in x for x in contract["policy_violations"]))


    def test_assessment_test_failures_can_be_policy_violation(self) -> None:
        git = GitDiffEvidence(
            base_ref="origin/main",
            head_ref="HEAD",
            raw_changed_files=("orders-service/src/main/java/com/example/OrderService.java",),
            changed_files=(classify_file("orders-service/src/main/java/com/example/OrderService.java"),),
        )
        from unit_test_coverage_agent.models import JacocoEvidence, SurefireEvidence, SurefireSuite

        strict = CoveragePolicy(
            minimum_line_coverage_for_changed_classes=70.0,
            minimum_method_coverage_for_changed_classes=70.0,
            minimum_branch_coverage_for_changed_classes=60.0,
            require_test_changes_when_production_code_changes=False,
            require_related_test_change_when_production_code_changes=True,
            fail_on_unknown_coverage=False,
            fail_on_missing_surefire_evidence=False,
            fail_on_missing_jacoco_evidence=False,
            fail_on_maven_verification_failure=False,
            fail_on_test_failures=True,
        )
        surefire = SurefireEvidence(
            reports_found=1,
            suites=(SurefireSuite("orders-service/target/surefire-reports/TEST-x.xml", 5, 1, 1, 0, 0.1),),
            total_tests=5,
            total_failures=1,
            total_errors=1,
            failed_suites=(SurefireSuite("orders-service/target/surefire-reports/TEST-x.xml", 5, 1, 1, 0, 0.1),),
        )
        assessment = assess_coverage(git, surefire, JacocoEvidence(0, ()), strict)
        contract = assessment_to_contract(assessment)

        self.assertEqual("policy_violation", contract["coverage_status"])
        self.assertTrue(any("unit tests failed" in x for x in contract["policy_violations"]))

    def test_assessment_test_failures_can_be_warning_in_advisory_policy(self) -> None:
        git = GitDiffEvidence(
            base_ref="origin/main",
            head_ref="HEAD",
            raw_changed_files=(),
            changed_files=(),
        )
        from unit_test_coverage_agent.models import JacocoEvidence, SurefireEvidence

        advisory = CoveragePolicy(
            minimum_line_coverage_for_changed_classes=70.0,
            minimum_method_coverage_for_changed_classes=70.0,
            minimum_branch_coverage_for_changed_classes=60.0,
            require_test_changes_when_production_code_changes=False,
            require_related_test_change_when_production_code_changes=True,
            fail_on_unknown_coverage=False,
            fail_on_missing_surefire_evidence=False,
            fail_on_missing_jacoco_evidence=False,
            fail_on_maven_verification_failure=False,
            fail_on_test_failures=False,
        )
        assessment = assess_coverage(git, SurefireEvidence(1, (), total_failures=1), JacocoEvidence(0, ()), advisory)
        contract = assessment_to_contract(assessment)
        self.assertFalse(contract["policy_violations"])
        self.assertTrue(any("unit tests failed" in x for x in contract["policy_warnings"]))


    def test_branch_coverage_below_threshold_is_policy_violation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / "orders-service" / "target" / "site" / "jacoco" / "jacoco.xml",
                """<report name="orders-service"><package name="com/example"><class name="com/example/OrderService" sourcefilename="OrderService.java"><method name="createOrder" desc="()V" line="10"><counter type="LINE" missed="0" covered="3"/></method><counter type="LINE" missed="0" covered="10"/><counter type="METHOD" missed="0" covered="2"/><counter type="BRANCH" missed="3" covered="1"/></class><sourcefile name="OrderService.java"/></package></report>""",
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

            assessment = assess_coverage(git, SurefireEvidence(1, (), total_tests=1), load_jacoco_evidence(root))
            contract = assessment_to_contract(assessment)

            self.assertEqual("policy_violation", contract["coverage_status"])
            self.assertEqual("manual_review", contract["merge_recommendation"])
            self.assertTrue(any("branch coverage" in x for x in contract["policy_violations"]))

    def test_branch_coverage_not_enforced_for_classes_with_no_branches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(
                root / "orders-service" / "target" / "site" / "jacoco" / "jacoco.xml",
                """<report name="orders-service"><package name="com/example"><class name="com/example/OrderService" sourcefilename="OrderService.java"><method name="createOrder" desc="()V" line="10"><counter type="LINE" missed="0" covered="3"/></method><counter type="LINE" missed="0" covered="10"/><counter type="METHOD" missed="0" covered="2"/><counter type="BRANCH" missed="0" covered="0"/></class><sourcefile name="OrderService.java"/></package></report>""",
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

            assessment = assess_coverage(git, SurefireEvidence(1, (), total_tests=1), load_jacoco_evidence(root))
            contract = assessment_to_contract(assessment)

            self.assertIsNone(contract["changed_class_coverage"][0]["branch_coverage_percent"])
            self.assertFalse(any("branch coverage" in x for x in contract["policy_violations"]))

    def test_output_schema_requires_branch_policy_field(self) -> None:
        contract = build_partial_contract()
        self.assertIn("minimum_branch_coverage_for_changed_classes", contract["policy"])
        self.assertFalse(validate_contract(contract))

    def test_markdown_includes_branch_policy_and_branch_column(self) -> None:
        contract = build_partial_contract()
        markdown = render_markdown(contract)
        self.assertIn("minimum_branch_coverage_for_changed_classes", markdown)
        self.assertIn("Branch %", markdown)

    def test_markdown_includes_test_execution_failures_section(self) -> None:
        contract = build_partial_contract()
        contract["test_execution_failures"] = ["orders-service"]
        markdown = render_markdown(contract)
        self.assertIn("## Test execution failures", markdown)
        self.assertIn("## Failed test suites", markdown)
        self.assertIn("orders-service", markdown)

    def test_output_schema_validates_test_execution_failures(self) -> None:
        contract = build_partial_contract()
        contract["test_execution_failures"] = [""]
        errors = validate_contract(contract)
        self.assertTrue(any("test_execution_failures" in e for e in errors))

    def test_output_schema_validates_failed_test_suites(self) -> None:
        contract = build_partial_contract()
        contract["failed_test_suites"] = [{"file": "x", "tests": 1, "failures": 1, "errors": 0, "skipped": 0}]
        errors = validate_contract(contract)
        self.assertFalse(errors)


    def test_related_test_candidate_generation(self) -> None:
        evidence = build_related_test_evidence(
            ["orders-service/src/main/java/com/example/OrderRiskClassifier.java"],
            [],
        )
        expected = set(evidence[0].expected_test_files)
        self.assertIn("orders-service/src/test/java/com/example/OrderRiskClassifierTest.java", expected)
        self.assertIn("orders-service/src/test/java/com/example/OrderRiskClassifierTests.java", expected)
        self.assertIn("orders-service/src/test/java/com/example/OrderRiskClassifierIT.java", expected)
        self.assertIn("orders-service/src/test/java/com/example/OrderRiskClassifierIntegrationTest.java", expected)

    def test_related_test_evidence_missing_and_matched(self) -> None:
        matched = build_related_test_evidence(
            ["orders-service/src/main/java/com/example/OrderRiskClassifier.java"],
            ["orders-service/src/test/java/com/example/OrderRiskClassifierTest.java"],
        )[0]
        self.assertEqual("matched", matched.status)
        self.assertIn("orders-service/src/test/java/com/example/OrderRiskClassifierTest.java", matched.matched_test_files)

        missing = build_related_test_evidence(
            ["orders-service/src/main/java/com/example/OrderRiskClassifier.java"],
            ["orders-service/src/test/java/com/example/UnrelatedTest.java"],
        )[0]
        self.assertEqual("missing", missing.status)

    def test_related_test_filename_match_in_different_package(self) -> None:
        evidence = build_related_test_evidence(
            ["orders-service/src/main/java/com/example/OrderRiskClassifier.java"],
            ["orders-service/src/test/java/com/example/feature/OrderRiskClassifierTest.java"],
        )[0]
        self.assertEqual("matched", evidence.status)

    def test_policy_loader_reads_related_test_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write(root / "coverage-policy.yml", "require_related_test_change_when_production_code_changes: true\n")
            policy = load_policy(root)
            self.assertTrue(policy.require_related_test_change_when_production_code_changes)

    def test_schema_rejects_invalid_related_test_status(self) -> None:
        contract = build_partial_contract()
        contract["related_test_evidence"][0]["status"] = "bad_status"
        errors = validate_contract(contract)
        self.assertTrue(any("related_test_evidence[0].status" in error for error in errors))

    def test_markdown_contains_related_test_section(self) -> None:
        contract = build_partial_contract()
        markdown = render_markdown(contract)
        self.assertIn("Related test evidence", markdown)
        self.assertIn("OrderService", markdown)

if __name__ == "__main__":
    unittest.main()
