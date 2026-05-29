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
            "Do not invent files, classes, methods, tests, coverage percentages, validation results, services, commands, or workflow behavior.",
            "If coverage evidence is missing or unknown, preserve that uncertainty explicitly.",
            "Pass/fail authority belongs only to deterministic policy evaluation in the input contract.",
            "Do not change coverage_status, merge_recommendation, policy_violations, or policy_warnings; they are deterministic and authoritative.",
            "Limit any refinements to advisory explanation fields: missing_test_scenarios, recommended_tests, blocking_reasons, and confidence.",
            "Do not recommend deleting tests or weakening verification.",
            "Do not propose code mutation, commits, PR creation, deployment, secrets access, or workflow permission escalation.",
            "Return JSON only. Do not wrap the response in markdown. Do not add prose outside JSON.",
            "Return the complete original JSON object with all required fields preserved.",
            "Do not summarize the JSON. Do not omit unchanged fields.",
            "If no advisory improvement is needed, return the input JSON unchanged.",
            "The JSON must preserve schema_version=1.0 and all required fields from the input contract.",
            "The safety_boundary must continue to say this report does not authorize code mutation, test deletion, PR creation, deployment, secrets access, workflow permission escalation, or automatic remediation.",
            "# Deterministic coverage evidence JSON",
            evidence_json,
        ]
    )
