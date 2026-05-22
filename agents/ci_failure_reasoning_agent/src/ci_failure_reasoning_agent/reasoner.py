from __future__ import annotations

import re
from typing import Any

from .schemas import EvidencePack, ReasoningReport

CATEGORY_FIX_HINTS = {
    "workflow-safety-policy-failure": "Unsafe workflow behavior was detected. Inspect workflow triggers, permissions, secret usage, deployment commands, and policy gates.",
    "shell-script-syntax-or-permission": "Shell script syntax or executable permission issue was detected. Fix scripts without disabling validation.",
    "docker-compose-contract-failure": "Docker Compose contract failure was detected. Fix Compose base/override/profile contract before runtime validation.",
    "maven-build-or-test-failure": "Java build or test failure was detected. Inspect affected Maven service and Surefire reports if available.",
    "maven-dependency-resolution": "Maven dependency resolution issue was detected. Confirm whether this is transient before changing dependencies.",
    "service-startup-or-port-health-issue": "Service startup, health endpoint, or port alignment issue was detected. Inspect service logs and runtime port contract.",
    "health-timeout": "Health timeout was detected. Confirm whether startup is broken or CI readiness wait strategy is insufficient.",
    "runtime-verifier-evidence-failure": "Runtime verifier expected evidence but did not find it. Align verifier, scenario docs, and actual runtime behavior.",
    "workflow-timeout-or-hang": "Workflow timeout or hang was detected. Check whether this workflow should be manual-only or has missing cleanup/readiness logic.",
}


def _value(payload: dict[str, Any], key: str, default: str = "unknown") -> str:
    value = payload.get(key)
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _extract_categories(text: str) -> list[str]:
    categories: list[str] = []
    for category in CATEGORY_FIX_HINTS:
        if f"`{category}`" in text or category in text:
            categories.append(category)
    return categories


def _extract_failed_job_lines(text: str) -> tuple[str, ...]:
    lines: list[str] = []
    capture = False
    for line in text.splitlines():
        if line.strip() == "## Failed jobs and steps":
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip().startswith("|") and "---" not in line and "Job" not in line:
            lines.append(line.strip())
    return tuple(lines)


def _extract_likely_files(fix_plan: str) -> tuple[str, ...]:
    files: list[str] = []
    capture = False
    for line in fix_plan.splitlines():
        if line.strip() == "## Files likely involved":
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip().startswith("-"):
            files.append(line.strip()[1:].strip().strip("`"))
    return tuple(files)


def _extract_do_not_change(fix_plan: str) -> tuple[str, ...]:
    items: list[str] = []
    capture = False
    for line in fix_plan.splitlines():
        if line.strip() == "## Files or behavior that must not be changed casually":
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip().startswith("-"):
            items.append(line.strip()[1:].strip())
    return tuple(items)


def _extract_validation(fix_plan: str) -> tuple[str, ...]:
    items: list[str] = []
    capture = False
    for line in fix_plan.splitlines():
        if line.strip() == "## Validation commands":
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.strip().startswith("-"):
            items.append(line.strip()[1:].strip().strip("`"))
    return tuple(items)


def _infer_confidence(categories: list[str], missing: tuple[str, ...]) -> str:
    if missing:
        return "low"
    if categories and categories[0] in {"workflow-safety-policy-failure", "shell-script-syntax-or-permission", "docker-compose-contract-failure", "maven-build-or-test-failure"}:
        return "medium"
    if categories:
        return "medium"
    return "low"


def _extract_symptoms(evidence: EvidencePack, categories: list[str]) -> tuple[str, ...]:
    symptoms: list[str] = []
    for category in categories:
        symptoms.append(CATEGORY_FIX_HINTS[category])

    log_markers = [
        "connection reset by peer",
        "empty reply from server",
        "BUILD FAILURE",
        "[FAIL]",
        "timed out",
        "No such file or directory",
        "Permission denied",
    ]
    lower_log = evidence.workflow_log_excerpt.lower()
    for marker in log_markers:
        if marker.lower() in lower_log:
            symptoms.append(f"Workflow log contains marker: `{marker}`")
    return tuple(dict.fromkeys(symptoms))


def reason(evidence: EvidencePack) -> ReasoningReport:
    combined = "\n".join([evidence.diagnostics_report, evidence.agent_fix_plan])
    categories = _extract_categories(combined)
    primary = categories[0] if categories else None
    failed_jobs = _extract_failed_job_lines(evidence.diagnostics_report)
    likely_files = _extract_likely_files(evidence.agent_fix_plan)
    do_not_change = _extract_do_not_change(evidence.agent_fix_plan)
    validation = _extract_validation(evidence.agent_fix_plan)
    confidence = _infer_confidence(categories, evidence.missing_files)
    symptoms = _extract_symptoms(evidence, categories)

    workflow = (
        f"{_value(evidence.run, 'name')} / {_value(evidence.run, 'displayTitle')} "
        f"on `{_value(evidence.run, 'headBranch')}` at `{_value(evidence.run, 'headSha')}` "
        f"status=`{_value(evidence.run, 'status')}` conclusion=`{_value(evidence.run, 'conclusion')}`"
    )

    if primary:
        hypotheses = (CATEGORY_FIX_HINTS[primary],)
        summary = f"Primary deterministic failure category is `{primary}`. Review evidence before making code changes."
    else:
        hypotheses = ("Unknown / not confirmed from deterministic evidence. Inspect raw logs and metadata before implementing a fix.",)
        summary = "No reliable deterministic failure category was found. Manual evidence review is required."

    missing_evidence = tuple(evidence.missing_files) if evidence.missing_files else (
        "No missing required evidence files were detected by the loader. Still verify raw logs before final root-cause claims.",
    )

    recommended_fix = tuple(CATEGORY_FIX_HINTS[c] for c in categories) if categories else (
        "Inspect raw logs and extend deterministic rules if the failure pattern is repeatable.",
    )

    return ReasoningReport(
        executive_summary=summary,
        evidence_inspected=(
            "triage/raw/run.json",
            "triage/raw/jobs.json",
            "triage/output/ci-failure-diagnostics-report.md",
            "triage/output/agent-fix-plan.md",
            "triage/logs/workflow-run.log",
            "AGENTS.md",
        ),
        failed_workflow=workflow,
        failed_jobs_and_steps=failed_jobs or ("No failed job table was available in diagnostics report.",),
        symptoms=symptoms or ("No known symptom marker was detected. Inspect raw logs.",),
        root_cause_hypotheses=hypotheses,
        confidence=confidence,
        missing_evidence=missing_evidence,
        recommended_fix=recommended_fix,
        files_likely_affected=likely_files or ("Unknown / not confirmed from deterministic evidence",),
        files_not_to_change_casually=do_not_change or ("Do not weaken CI checks or verifier assertions to make the run green.",),
        validation_plan=validation or ("Run the affected workflow again after a targeted fix.",),
        risk_assessment="Advisory report only. Human review is required before implementation.",
    )
