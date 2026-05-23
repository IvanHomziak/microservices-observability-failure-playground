from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SAFETY_BOUNDARY = (
    "Advisory artifact only. This proposal does not authorize code mutation, test deletion, "
    "commit creation, PR creation, deployment, secrets access, workflow permission escalation, "
    "or automatic remediation."
)


@dataclass(frozen=True)
class ProposedTestScenario:
    production_class: str
    source_file: str
    suggested_test_file: str
    suggested_test_class: str
    suggested_test_methods: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class PatchProposal:
    schema_version: str
    proposal_status: str
    merge_recommendation: str
    proposed_test_scenarios: tuple[ProposedTestScenario, ...]
    validation_commands: tuple[str, ...]
    notes: tuple[str, ...]
    safety_boundary: str


def _service_from_source_file(source_file: str) -> str | None:
    parts = source_file.split("/")
    if parts:
        return parts[0]
    return None


def _test_file_for_source(source_file: str, expected_class_name: str) -> str:
    if "/src/main/java/" in source_file:
        return source_file.replace("/src/main/java/", "/src/test/java/").replace(".java", "Test.java")
    service = _service_from_source_file(source_file)
    simple_name = expected_class_name.split(".")[-1]
    if service:
        package_path = "/".join(expected_class_name.split(".")[:-1])
        return f"{service}/src/test/java/{package_path}/{simple_name}Test.java"
    return f"src/test/java/{expected_class_name.replace('.', '/') }Test.java"


def _test_class_name(expected_class_name: str) -> str:
    return f"{expected_class_name}Test"


def _method_name_from_jvm_signature(signature: str) -> str:
    return signature.split("(", 1)[0] if "(" in signature else signature


def _suggested_methods(class_coverage: dict[str, Any]) -> tuple[str, ...]:
    status = class_coverage.get("status")
    uncovered_methods = class_coverage.get("uncovered_methods") or []
    expected_class_name = str(class_coverage.get("expected_class_name", "ChangedClass"))
    simple_name = expected_class_name.split(".")[-1]

    methods: list[str] = []
    for uncovered in uncovered_methods:
        method = _method_name_from_jvm_signature(str(uncovered))
        if method and method not in {"<init>", "<clinit>"}:
            methods.append(f"shouldCover{method[:1].upper()}{method[1:]}")

    if methods:
        return tuple(methods)

    if status == "uncovered":
        return (
            f"shouldCreate{simple_name}ForValidInput",
            f"shouldRejectInvalidInputFor{simple_name}",
            f"shouldHandleFailurePathFor{simple_name}",
        )

    if status == "unknown":
        return (
            f"shouldVerifyCoreBehaviorOf{simple_name}",
            f"shouldCoverErrorPathOf{simple_name}",
        )

    return (f"shouldImproveCoverageFor{simple_name}",)


def _rationale(class_coverage: dict[str, Any]) -> str:
    status = class_coverage.get("status")
    expected_class_name = class_coverage.get("expected_class_name", "unknown class")
    if status == "unknown":
        return f"Coverage for `{expected_class_name}` is unknown because no matching JaCoCo class entry was found."
    if status == "uncovered":
        return f"`{expected_class_name}` appears uncovered according to JaCoCo evidence."
    if status == "partial":
        return f"`{expected_class_name}` is only partially covered; missing line/method/branch coverage should be reviewed."
    return f"`{expected_class_name}` has coverage, but the report still recommends reviewing changed behavior."


def build_patch_proposal(contract: dict[str, Any]) -> PatchProposal:
    scenarios: list[ProposedTestScenario] = []
    changed_class_coverage = contract.get("changed_class_coverage", [])
    if isinstance(changed_class_coverage, list):
        for item in changed_class_coverage:
            if not isinstance(item, dict):
                continue
            status = item.get("status")
            if status not in {"unknown", "uncovered", "partial"}:
                continue
            source_file = str(item.get("source_file", ""))
            expected_class_name = str(item.get("expected_class_name", ""))
            if not source_file or not expected_class_name:
                continue
            scenarios.append(
                ProposedTestScenario(
                    production_class=expected_class_name,
                    source_file=source_file,
                    suggested_test_file=_test_file_for_source(source_file, expected_class_name),
                    suggested_test_class=_test_class_name(expected_class_name),
                    suggested_test_methods=_suggested_methods(item),
                    rationale=_rationale(item),
                )
            )

    services = contract.get("changed_services", [])
    validation_commands: list[str] = []
    if isinstance(services, list) and services:
        for service in services:
            if isinstance(service, str) and service.strip():
                validation_commands.append(f"cd {service} && mvn -B -ntp verify")
    else:
        validation_commands.append("mvn -B -ntp verify")

    notes: list[str] = []
    notes.append("This artifact proposes test coverage work only; it does not apply patches.")
    notes.append("Review proposed test names and scenarios manually before implementation.")
    if contract.get("jacoco_reports_found", 0) == 0:
        notes.append("JaCoCo evidence is missing; run tests with JaCoCo before treating this proposal as complete.")
    if contract.get("surefire_reports_found", 0) == 0:
        notes.append("Surefire evidence is missing; run Maven tests before treating this proposal as complete.")

    proposal_status = "no_action_needed" if not scenarios else "proposal_available"
    return PatchProposal(
        schema_version="1.0",
        proposal_status=proposal_status,
        merge_recommendation=str(contract.get("merge_recommendation", "manual_review")),
        proposed_test_scenarios=tuple(scenarios),
        validation_commands=tuple(validation_commands),
        notes=tuple(notes),
        safety_boundary=SAFETY_BOUNDARY,
    )


def patch_proposal_to_dict(proposal: PatchProposal) -> dict[str, Any]:
    return {
        "schema_version": proposal.schema_version,
        "proposal_status": proposal.proposal_status,
        "merge_recommendation": proposal.merge_recommendation,
        "proposed_test_scenarios": [
            {
                "production_class": scenario.production_class,
                "source_file": scenario.source_file,
                "suggested_test_file": scenario.suggested_test_file,
                "suggested_test_class": scenario.suggested_test_class,
                "suggested_test_methods": list(scenario.suggested_test_methods),
                "rationale": scenario.rationale,
            }
            for scenario in proposal.proposed_test_scenarios
        ],
        "validation_commands": list(proposal.validation_commands),
        "notes": list(proposal.notes),
        "safety_boundary": proposal.safety_boundary,
    }


def render_patch_proposal_markdown(proposal: PatchProposal) -> str:
    lines: list[str] = []
    lines.append("# Unit Test Coverage Patch Proposal")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Proposal status: `{proposal.proposal_status}`")
    lines.append(f"- Merge recommendation from coverage report: `{proposal.merge_recommendation}`")
    lines.append("")

    lines.append("## Proposed test scenarios")
    lines.append("")
    if not proposal.proposed_test_scenarios:
        lines.append("No test proposal was generated from the current coverage evidence.")
        lines.append("")
    else:
        for scenario in proposal.proposed_test_scenarios:
            lines.append(f"### `{scenario.production_class}`")
            lines.append("")
            lines.append(f"- Production file: `{scenario.source_file}`")
            lines.append(f"- Suggested test file: `{scenario.suggested_test_file}`")
            lines.append(f"- Suggested test class: `{scenario.suggested_test_class}`")
            lines.append(f"- Rationale: {scenario.rationale}")
            lines.append("- Suggested test methods:")
            for method in scenario.suggested_test_methods:
                lines.append(f"  - `{method}`")
            lines.append("")

    lines.append("## Validation commands")
    lines.append("")
    for command in proposal.validation_commands:
        lines.append(f"- `{command}`")
    lines.append("")

    lines.append("## Notes")
    lines.append("")
    for note in proposal.notes:
        lines.append(f"- {note}")
    lines.append("")

    lines.append("## Safety boundary")
    lines.append("")
    lines.append(proposal.safety_boundary)
    lines.append("")
    return "\n".join(lines)
