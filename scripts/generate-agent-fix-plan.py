#!/usr/bin/env python3
"""Generate an agent-ready CI failure fix plan from deterministic diagnostics evidence.

This script does not call an LLM, does not mutate repository files, and does not
produce a patch. It turns collected CI diagnostics evidence into a structured
remediation plan that a human or agent can review before implementation.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import re
from collections import Counter
from typing import Any


@dataclasses.dataclass(frozen=True)
class RunSummary:
    name: str
    display_title: str
    event: str
    head_branch: str
    head_sha: str
    status: str
    conclusion: str
    url: str | None


@dataclasses.dataclass(frozen=True)
class FailedStep:
    name: str
    number: int | None
    conclusion: str
    status: str


@dataclasses.dataclass(frozen=True)
class FailedJob:
    name: str
    conclusion: str
    status: str
    url: str | None
    failed_steps: tuple[FailedStep, ...]


CATEGORY_FIX_MAP: dict[str, dict[str, Any]] = {
    "workflow-safety-policy-failure": {
        "confidence": "high",
        "likely_files": [".github/workflows/*.yml"],
        "must_not_change": ["Do not remove safety checks just to make CI green."],
        "recommended_fix": "Fix unsafe workflow behavior: forbidden trigger, secret usage, deployment command, or broad permissions.",
        "validation": ["Inspect changed workflow files", "Run PR Fast Feedback"],
        "risk": "High if ignored because unsafe PR workflows can expose secrets or mutate protected systems.",
    },
    "shell-script-syntax-or-permission": {
        "confidence": "high",
        "likely_files": ["scripts/*.sh"],
        "must_not_change": ["Do not skip script validation."],
        "recommended_fix": "Fix shell syntax, interpreter, missing file, or executable permission issue.",
        "validation": ["bash -n scripts/*.sh", "ls -l scripts/*.sh"],
        "risk": "Medium. Broken verifier scripts can invalidate scenario readiness checks.",
    },
    "docker-compose-contract-failure": {
        "confidence": "high",
        "likely_files": ["docker-compose.yml", "docker-compose*.yml", "*/Dockerfile", ".env.example"],
        "must_not_change": ["Do not delete scenario overrides to make Compose validation pass."],
        "recommended_fix": "Fix invalid Compose syntax, missing service references, invalid profile usage, or broken override contract.",
        "validation": ["docker compose config", "docker compose -f docker-compose.yml -f <override> config"],
        "risk": "High for runtime scenarios because invalid Compose contracts block deterministic verification.",
    },
    "maven-build-or-test-failure": {
        "confidence": "high",
        "likely_files": ["*/pom.xml", "*/src/main/**", "*/src/test/**"],
        "must_not_change": ["Do not delete tests without proving they are invalid."],
        "recommended_fix": "Inspect Surefire reports and fix the failing test, compilation error, or broken Maven module configuration.",
        "validation": ["cd <affected-service> && mvn test", "Check target/surefire-reports when available"],
        "risk": "Medium to high. Java test failures can indicate broken API behavior or invalid test fixtures.",
    },
    "maven-dependency-resolution": {
        "confidence": "medium",
        "likely_files": ["*/pom.xml"],
        "must_not_change": ["Do not change dependency versions unless coordinates are proven incorrect."],
        "recommended_fix": "Retry first if this looks transient. If repeatable, inspect dependency coordinates and repository configuration.",
        "validation": ["cd <affected-service> && mvn -B -ntp test"],
        "risk": "Medium. May be transient network/repository behavior rather than code failure.",
    },
    "service-startup-or-port-health-issue": {
        "confidence": "medium",
        "likely_files": ["docker-compose.yml", "*/src/main/resources/application.yml", "*/Dockerfile", "scripts/verify-*.sh"],
        "must_not_change": ["Do not increase timeouts blindly without checking startup logs and port alignment."],
        "recommended_fix": "Check SERVER_PORT, Compose port mapping, actuator health exposure, dependency startup order, and service logs.",
        "validation": ["docker compose config", "./scripts/verify-milestone-1.sh", "docker compose logs --no-color <service>"],
        "risk": "High for runtime-smoke and scenario workflows because unhealthy services invalidate downstream evidence.",
    },
    "health-timeout": {
        "confidence": "medium",
        "likely_files": ["scripts/verify-*.sh", "docker-compose.yml", "*/src/main/resources/application.yml"],
        "must_not_change": ["Do not classify timeout as root cause without inspecting logs."],
        "recommended_fix": "Inspect service logs and health endpoint behavior. Adjust readiness polling only after verifying startup behavior.",
        "validation": ["./scripts/verify-milestone-1.sh", "curl -v http://localhost:<port>/actuator/health"],
        "risk": "Medium. Could be real startup regression or insufficient CI wait strategy.",
    },
    "runtime-verifier-evidence-failure": {
        "confidence": "medium",
        "likely_files": ["scripts/verify-*.sh", "scripts/trigger-*.sh", "scenarios/*.md", "docker-compose*.yml", "*/src/main/**"],
        "must_not_change": ["Do not weaken verifier assertions to pass without preserving scenario evidence."],
        "recommended_fix": "Compare verifier expectations with scenario docs and actual runtime behavior. Align code, docs, and verifier together.",
        "validation": ["Run the affected verifier script", "Check scenario docs and expected evidence"],
        "risk": "High for AI diagnostics quality because missing evidence can make agent conclusions unreliable.",
    },
    "workflow-timeout-or-hang": {
        "confidence": "medium",
        "likely_files": [".github/workflows/*.yml", "scripts/verify-*.sh"],
        "must_not_change": ["Do not move heavy full-readiness checks into required PR checks without proof of stability."],
        "recommended_fix": "Determine whether the workflow is too heavy for PR execution, missing cleanup, or waiting on an unavailable dependency.",
        "validation": ["Inspect workflow duration", "Check artifacts and cleanup behavior", "Consider manual-only execution for full readiness"],
        "risk": "Medium. Long-running checks reduce CI reliability and can block agentic feedback loops.",
    },
}


def load_json(path: pathlib.Path | None) -> Any | None:
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def read_text(path: pathlib.Path | None) -> str:
    if path is None or not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def as_string(value: Any, default: str = "unknown") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def as_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_run_summary(run_json_path: pathlib.Path | None) -> RunSummary:
    payload = load_json(run_json_path) or {}
    if not isinstance(payload, dict):
        payload = {}
    return RunSummary(
        name=as_string(payload.get("name")),
        display_title=as_string(payload.get("displayTitle")),
        event=as_string(payload.get("event")),
        head_branch=as_string(payload.get("headBranch")),
        head_sha=as_string(payload.get("headSha")),
        status=as_string(payload.get("status")),
        conclusion=as_string(payload.get("conclusion")),
        url=as_optional_string(payload.get("url")),
    )


def parse_failed_jobs(jobs_json_path: pathlib.Path | None) -> list[FailedJob]:
    payload = load_json(jobs_json_path)
    if not isinstance(payload, dict):
        return []
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        return []

    failed_jobs: list[FailedJob] = []
    for raw_job in jobs:
        if not isinstance(raw_job, dict):
            continue
        conclusion = as_string(raw_job.get("conclusion")).lower()
        status = as_string(raw_job.get("status")).lower()
        if conclusion not in {"failure", "cancelled", "timed_out", "action_required", "startup_failure"} and status not in {
            "failure",
            "cancelled",
            "timed_out",
            "action_required",
            "startup_failure",
        }:
            continue

        raw_steps = raw_job.get("steps")
        steps = raw_steps if isinstance(raw_steps, list) else []
        failed_steps: list[FailedStep] = []
        for raw_step in steps:
            if not isinstance(raw_step, dict):
                continue
            step_conclusion = as_string(raw_step.get("conclusion")).lower()
            step_status = as_string(raw_step.get("status")).lower()
            if step_conclusion in {"failure", "cancelled", "timed_out", "action_required", "startup_failure"} or step_status in {
                "failure",
                "cancelled",
                "timed_out",
                "action_required",
                "startup_failure",
            }:
                failed_steps.append(
                    FailedStep(
                        name=as_string(raw_step.get("name")),
                        number=as_optional_int(raw_step.get("number")),
                        conclusion=step_conclusion,
                        status=step_status,
                    )
                )

        failed_jobs.append(
            FailedJob(
                name=as_string(raw_job.get("name")),
                conclusion=conclusion,
                status=status,
                url=as_optional_string(raw_job.get("url")),
                failed_steps=tuple(failed_steps),
            )
        )

    return failed_jobs


def extract_categories(report_text: str) -> Counter[str]:
    categories: Counter[str] = Counter()
    for match in re.finditer(r"`([a-z0-9-]+)`\s*\|\s*(\d+)\s*\|", report_text):
        category = match.group(1)
        count = int(match.group(2))
        if category in CATEGORY_FIX_MAP:
            categories[category] += count
    return categories


def infer_primary_category(categories: Counter[str], failed_jobs: list[FailedJob]) -> str | None:
    priority = [
        "workflow-safety-policy-failure",
        "shell-script-syntax-or-permission",
        "docker-compose-contract-failure",
        "maven-build-or-test-failure",
        "service-startup-or-port-health-issue",
        "health-timeout",
        "runtime-verifier-evidence-failure",
        "workflow-timeout-or-hang",
        "maven-dependency-resolution",
    ]
    for category in priority:
        if categories.get(category):
            return category

    job_names = " ".join(job.name.lower() for job in failed_jobs)
    if "maven" in job_names or "java" in job_names:
        return "maven-build-or-test-failure"
    if "runtime" in job_names or "smoke" in job_names:
        return "service-startup-or-port-health-issue"
    if "compose" in job_names:
        return "docker-compose-contract-failure"
    if "shell" in job_names or "script" in job_names:
        return "shell-script-syntax-or-permission"
    return None


def format_failed_steps(steps: tuple[FailedStep, ...]) -> str:
    if not steps:
        return "No failed step metadata available"
    values = []
    for step in steps:
        prefix = f"#{step.number} " if step.number is not None else ""
        values.append(f"{prefix}{step.name} ({step.conclusion or step.status})")
    return "; ".join(values)


def unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def render_plan(
    run: RunSummary,
    failed_jobs: list[FailedJob],
    categories: Counter[str],
    primary_category: str | None,
    diagnostics_report_path: pathlib.Path | None,
) -> str:
    plan = CATEGORY_FIX_MAP.get(primary_category or "", {})
    likely_files = unique_ordered(list(plan.get("likely_files", [])))
    must_not_change = unique_ordered(list(plan.get("must_not_change", [])))
    validation = unique_ordered(list(plan.get("validation", [])))

    lines: list[str] = []
    lines.append("# Agent Fix Plan")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append("This is a deterministic, evidence-based remediation plan for a failed CI run.")
    lines.append("It does not contain an automatic patch and does not authorize code mutation by itself.")
    lines.append("")

    lines.append("## Failed workflow")
    lines.append("")
    lines.append(f"- Name: `{run.name}`")
    lines.append(f"- Display title: `{run.display_title}`")
    lines.append(f"- Event: `{run.event}`")
    lines.append(f"- Head branch: `{run.head_branch}`")
    lines.append(f"- Head SHA: `{run.head_sha}`")
    lines.append(f"- Status: `{run.status}`")
    lines.append(f"- Conclusion: `{run.conclusion}`")
    if run.url:
        lines.append(f"- URL: {run.url}")
    lines.append("")

    lines.append("## Failed jobs and steps")
    lines.append("")
    if not failed_jobs:
        lines.append("No failed job metadata was found. Inspect raw logs before making changes.")
    else:
        lines.append("| Job | Conclusion | Status | Failed steps | URL |")
        lines.append("|---|---|---|---|---|")
        for job in failed_jobs:
            url = f"[open]({job.url})" if job.url else ""
            lines.append(f"| `{job.name}` | `{job.conclusion}` | `{job.status}` | {format_failed_steps(job.failed_steps)} | {url} |")
    lines.append("")

    lines.append("## Observed failure categories")
    lines.append("")
    if not categories:
        lines.append("No known deterministic failure category was detected from the diagnostics report.")
    else:
        lines.append("| Category | Count |")
        lines.append("|---|---:|")
        for category, count in categories.most_common():
            lines.append(f"| `{category}` | {count} |")
    lines.append("")

    lines.append("## Primary triage category")
    lines.append("")
    if primary_category:
        lines.append(f"`{primary_category}`")
    else:
        lines.append("Unknown / not confirmed from deterministic evidence.")
    lines.append("")

    lines.append("## Probable root cause")
    lines.append("")
    if primary_category:
        lines.append(plan.get("recommended_fix", "Inspect evidence and derive a targeted fix."))
    else:
        lines.append("Unknown. The current deterministic rules did not identify a reliable category. Inspect raw logs and update the rules if the pattern is repeatable.")
    lines.append("")

    lines.append("## Confidence")
    lines.append("")
    lines.append(f"`{plan.get('confidence', 'low') if primary_category else 'low'}`")
    lines.append("")

    lines.append("## Files likely involved")
    lines.append("")
    if likely_files:
        for item in likely_files:
            lines.append(f"- `{item}`")
    else:
        lines.append("- Unknown / not confirmed from deterministic evidence")
    lines.append("")

    lines.append("## Files or behavior that must not be changed casually")
    lines.append("")
    if must_not_change:
        for item in must_not_change:
            lines.append(f"- {item}")
    else:
        lines.append("- Do not weaken CI checks or verifier assertions just to make the workflow green.")
        lines.append("- Do not delete deterministic scenario evidence without updating docs and verifiers.")
    lines.append("")

    lines.append("## Recommended fix approach")
    lines.append("")
    if primary_category:
        lines.append(plan.get("recommended_fix", "Inspect evidence and make the smallest safe fix."))
    else:
        lines.append("Inspect raw logs, identify the failing layer, and add a deterministic analyzer rule before making broad code changes.")
    lines.append("")

    lines.append("## Validation commands")
    lines.append("")
    if validation:
        for item in validation:
            lines.append(f"- `{item}`")
    else:
        lines.append("- `bash -n scripts/*.sh`")
        lines.append("- `docker compose config`")
        lines.append("- run the affected workflow again")
    lines.append("")

    lines.append("## Risk assessment")
    lines.append("")
    lines.append(plan.get("risk", "Unknown. Inspect raw evidence before implementing changes."))
    lines.append("")

    lines.append("## Human approval required")
    lines.append("")
    lines.append("Yes. This plan is advisory and must be reviewed before implementation.")
    lines.append("")

    lines.append("## Evidence references")
    lines.append("")
    if diagnostics_report_path:
        lines.append(f"- Diagnostics report: `{diagnostics_report_path}`")
    lines.append("- Raw logs and metadata should be reviewed before making a patch.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic agent fix plan from CI diagnostics evidence.")
    parser.add_argument("--diagnostics-report", required=True, type=pathlib.Path)
    parser.add_argument("--run-json", required=True, type=pathlib.Path)
    parser.add_argument("--jobs-json", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()

    diagnostics_text = read_text(args.diagnostics_report)
    categories = extract_categories(diagnostics_text)
    failed_jobs = parse_failed_jobs(args.jobs_json)
    run_summary = parse_run_summary(args.run_json)
    primary_category = infer_primary_category(categories, failed_jobs)

    plan = render_plan(
        run=run_summary,
        failed_jobs=failed_jobs,
        categories=categories,
        primary_category=primary_category,
        diagnostics_report_path=args.diagnostics_report,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(plan + "\n", encoding="utf-8")
    print(f"Wrote agent fix plan to {args.output}")
    print(f"Primary category: {primary_category or 'unknown'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
