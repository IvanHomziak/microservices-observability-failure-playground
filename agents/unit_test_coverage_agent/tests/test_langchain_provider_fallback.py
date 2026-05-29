from __future__ import annotations

import json
import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from unit_test_coverage_agent.providers import (  # noqa: E402
    LLM_FALLBACK_WARNING,
    LangChainOpenAICoverageProvider,
)
from unit_test_coverage_agent.prompt_builder import build_coverage_reasoning_prompt  # noqa: E402


def build_contract() -> dict:
    return {
        "schema_version": "1.0",
        "coverage_status": "sufficient",
        "changed_production_files": ["orders-service/src/main/java/com/example/OrderService.java"],
        "deleted_production_files": [],
        "coverage_relevant_production_files": ["orders-service/src/main/java/com/example/OrderService.java"],
        "changed_test_files": ["orders-service/src/test/java/com/example/OrderServiceTest.java"],
        "changed_services": ["orders-service"],
        "surefire_reports_found": 1,
        "jacoco_reports_found": 1,
        "test_total_count": 1,
        "test_failure_count": 0,
        "test_error_count": 0,
        "test_skipped_count": 0,
        "failed_test_suites": [],
        "test_execution_failures": [],
        "changed_class_coverage": [
            {
                "source_file": "orders-service/src/main/java/com/example/OrderService.java",
                "expected_class_name": "com.example.OrderService",
                "matched_class_name": "com.example.OrderService",
                "service": "orders-service",
                "report_file": "orders-service/target/site/jacoco/jacoco.xml",
                "status": "covered",
                "lines_covered": 10,
                "lines_missed": 0,
                "line_coverage_percent": 100.0,
                "methods_covered": 2,
                "methods_missed": 0,
                "method_coverage_percent": 100.0,
                "branch_coverage_percent": None,
                "mapping_strategy": "exact_class_name",
                "mapping_confidence": "high",
                "mapping_candidates": ["com.example.OrderService"],
                "uncovered_methods": [],
            }
        ],
        "related_test_evidence": [
            {
                "production_file": "orders-service/src/main/java/com/example/OrderService.java",
                "expected_class_name": "OrderService",
                "expected_test_files": ["orders-service/src/test/java/com/example/OrderServiceTest.java"],
                "matched_test_files": ["orders-service/src/test/java/com/example/OrderServiceTest.java"],
                "status": "matched",
            }
        ],
        "covered_classes": ["com.example.OrderService"],
        "partially_covered_classes": [],
        "uncovered_classes": [],
        "unknown_coverage_files": [],
        "missing_related_test_files": [],
        "policy": {
            "minimum_line_coverage_for_changed_classes": 70.0,
            "minimum_method_coverage_for_changed_classes": 70.0,
            "minimum_branch_coverage_for_changed_classes": 60.0,
            "require_test_changes_when_production_code_changes": True,
            "require_related_test_change_when_production_code_changes": True,
            "fail_on_unknown_coverage": True,
            "fail_on_missing_surefire_evidence": True,
            "fail_on_missing_jacoco_evidence": True,
            "fail_on_maven_verification_failure": True,
            "fail_on_test_failures": True,
        },
        "policy_violations": [],
        "policy_warnings": [],
        "missing_test_scenarios": ["No deterministic missing-test scenario was detected."],
        "recommended_tests": ["No deterministic test recommendation was generated."],
        "confidence": "medium",
        "blocking_reasons": ["No deterministic blocking reason was detected."],
        "merge_recommendation": "approve",
        "safety_boundary": "Read-only advisory output. This report does not authorize code mutation, test deletion, PR creation, deployment, secrets access, workflow permission escalation, or automatic remediation.",
    }


class TestLangChainProviderFallback(unittest.TestCase):
    def test_missing_openai_key_still_fails_clearly(self) -> None:
        provider = LangChainOpenAICoverageProvider(model="gpt-4.1-mini")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "OPENAI_API_KEY is required"):
                provider.refine(build_contract())

    def test_non_json_llm_response_falls_back_to_deterministic_contract(self) -> None:
        provider = LangChainOpenAICoverageProvider(model="gpt-4.1-mini")
        contract = build_contract()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch.object(provider, "_invoke", return_value="not json"):
            result = provider.refine(contract)

        self.assertEqual(contract, result.contract)
        self.assertTrue(result.used_external_call)
        self.assertEqual("gpt-4.1-mini", result.model)
        self.assertIn(LLM_FALLBACK_WARNING, result.warnings)
        self.assertTrue(any("non-JSON" in warning for warning in result.warnings))

    def test_incomplete_llm_contract_falls_back_to_deterministic_contract(self) -> None:
        provider = LangChainOpenAICoverageProvider(model="gpt-4.1-mini")
        contract = build_contract()

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch.object(
            provider,
            "_invoke",
            return_value=json.dumps({"schema_version": "1.0"}),
        ):
            result = provider.refine(contract)

        self.assertEqual(contract, result.contract)
        self.assertIn(LLM_FALLBACK_WARNING, result.warnings)
        self.assertTrue(any("Missing required field" in warning for warning in result.warnings))

    def test_llm_attempt_to_modify_authoritative_fields_falls_back(self) -> None:
        provider = LangChainOpenAICoverageProvider(model="gpt-4.1-mini")
        contract = build_contract()
        modified = deepcopy(contract)
        modified["coverage_status"] = "policy_violation"

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch.object(provider, "_invoke", return_value=json.dumps(modified)):
            result = provider.refine(contract)

        self.assertEqual(contract, result.contract)
        self.assertIn(LLM_FALLBACK_WARNING, result.warnings)
        self.assertTrue(any("coverage_status must remain deterministic" in warning for warning in result.warnings))

    def test_valid_llm_contract_accepts_advisory_field_refinements(self) -> None:
        provider = LangChainOpenAICoverageProvider(model="gpt-4.1-mini")
        contract = build_contract()
        refined = deepcopy(contract)
        refined["recommended_tests"] = ["Keep the existing related test coverage for OrderService."]
        refined["confidence"] = "high"

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), patch.object(provider, "_invoke", return_value=json.dumps(refined)):
            result = provider.refine(contract)

        self.assertEqual(["Keep the existing related test coverage for OrderService."], result.contract["recommended_tests"])
        self.assertEqual("high", result.contract["confidence"])
        self.assertEqual(contract["coverage_status"], result.contract["coverage_status"])
        self.assertEqual((), result.warnings)

    def test_prompt_requires_complete_json_contract(self) -> None:
        prompt = build_coverage_reasoning_prompt(build_contract())

        self.assertIn("Return the complete original JSON object", prompt)
        self.assertIn("Do not omit unchanged fields", prompt)
        self.assertIn("return the input JSON unchanged", prompt)


if __name__ == "__main__":
    unittest.main()
