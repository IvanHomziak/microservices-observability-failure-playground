from __future__ import annotations

from .output_schema import render_contract_json

MAX_EVIDENCE_CHARS = 24_000


def build_coverage_reasoning_prompt(contract: dict) -> str:
    evidence_json = render_contract_json(contract)
    if len(evidence_json) > MAX_EVIDENCE_CHARS:
        evidence_json = evidence_json[-MAX_EVIDENCE_CHARS:]
        evidence_json = f"<truncated to latest {MAX_EVIDENCE_CHARS} chars>\n{evidence_json}"

    return "\n\n".join(
        [
            "# Unit Test Coverage Reasoning Task",
            "You are a read-only unit test coverage review agent.",
            "Reason only from the deterministic coverage evidence below.",
            "Do not invent files, classes, methods, tests, coverage percentages, or validation results.",
            "If coverage evidence is missing or unknown, preserve that uncertainty explicitly.",
            "Do not recommend deleting tests or weakening verification.",
            "Do not propose code mutation, commits, PR creation, deployment, secrets access, or workflow permission escalation.",
            "Return only JSON. Do not wrap the response in markdown. Do not add prose outside JSON.",
            "The JSON must preserve schema_version=1.0 and all required fields from the input contract.",
            "You may improve missing_test_scenarios, recommended_tests, blocking_reasons, confidence, and merge_recommendation only when supported by the evidence.",
            "The safety_boundary must continue to prohibit code mutation, test deletion, PR creation, deployment, secrets access, workflow permission escalation, and automatic remediation.",
            "# Deterministic coverage evidence JSON",
            evidence_json,
        ]
    )
