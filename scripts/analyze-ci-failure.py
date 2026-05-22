#!/usr/bin/env python3
"""Rule-based CI failure analyzer for GitHub Actions logs.

This script is intentionally deterministic and does not call an LLM.
It reads local text log files, optionally parses GitHub Actions jobs metadata,
and produces a markdown diagnostics report.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import re
from collections import Counter
from typing import Any, Iterable


@dataclasses.dataclass(frozen=True)
class Finding:
    category: str
    severity: str
    pattern: str
    evidence: str
    recommendation: str


@dataclasses.dataclass(frozen=True)
class StepFailure:
    name: str
    number: int | None
    status: str
    conclusion: str
    started_at: str | None
    completed_at: str | None


@dataclasses.dataclass(frozen=True)
class JobFailure:
    name: str
    database_id: int | None
    status: str
    conclusion: str
    started_at: str | None
    completed_at: str | None
    url: str | None
    failed_steps: tuple[StepFailure, ...]


RULES: list[tuple[str, str, re.Pattern[str], str]] = [
    (
        "service-startup-or-port-health-issue",
        "high",
        re.compile(r"connection reset by peer|empty reply from server|failed to connect|connection refused", re.IGNORECASE),
        "Check service startup logs, SERVER_PORT alignment, Docker Compose port mappings, actuator exposure, and dependency readiness.",
    ),
    (
        "health-timeout",
        "high",
        re.compile(r"timed out waiting for .*health|timeout.*actuator/health|health check.*failed", re.IGNORECASE),
        "Inspect the target service logs and container state. Verify the health endpoint path, exposed port, and startup dependencies.",
    ),
    (
        "docker-compose-contract-failure",
        "high",
        re.compile(
            r"services\..*Additional property|"
            r"yaml:|"
            r"invalid compose|"
            r"no such service|"
            r"service .* has neither an image nor a build context|"
            r"error while interpolating|"
            r"failed to solve|"
            r"failed to read .*docker-compose|"
            r"compose file .* is invalid|"
            r"unsupported config option",
            re.IGNORECASE,
        ),
        "Run the exact docker compose config command locally and fix the base or override Compose contract.",
    ),
    (
        "maven-build-or-test-failure",
        "high",
        re.compile(r"BUILD FAILURE|There are test failures|Failed tests:|Tests run: .* Failures: [1-9]|Compilation failure", re.IGNORECASE),
        "Open Surefire reports if available. Re-run the affected service with mvn test and fix the failing test or compilation error.",
    ),
    (
        "maven-dependency-resolution",
        "medium",
        re.compile(r"Could not resolve dependencies|Could not transfer artifact|Return code is: 403|Return code is: 5\d\d|Connection timed out", re.IGNORECASE),
        "Treat as possible transient repository/network issue first. Retry before changing code unless the dependency coordinates are incorrect.",
    ),
    (
        "shell-script-syntax-or-permission",
        "high",
        re.compile(r"syntax error near unexpected token|Permission denied|not executable|bad interpreter|No such file or directory", re.IGNORECASE),
        "Run bash -n scripts/*.sh and verify executable permissions for required verifier scripts.",
    ),
    (
        "workflow-safety-policy-failure",
        "high",
        re.compile(r"pull_request_target|Secrets usage detected|Forbidden deployment command|Forbidden .* trigger", re.IGNORECASE),
        "Inspect workflow safety rules. Do not bypass by deleting checks; fix the unsafe workflow trigger, secret usage, or deployment command.",
    ),
    (
        "runtime-verifier-evidence-failure",
        "high",
        re.compile(r"\[FAIL\]|expected .* but got|Missing:|Could not parse HTTP status|response missing", re.IGNORECASE),
        "Inspect the failing verifier and scenario contract. Confirm trigger output, expected HTTP behavior, logs, and cleanup behavior.",
    ),
    (
        "workflow-timeout-or-hang",
        "medium",
        re.compile(r"The operation was canceled|timed out|exceeded the maximum execution time|cancelled", re.IGNORECASE),
        "Check whether the workflow is too heavy for PR execution. Consider manual-only execution, path filters, better readiness waits, or diagnostics artifacts.",
    ),
]

FAILURE_CONCLUSIONS = {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}
FAILURE_STATUSES = {"failure", "cancelled", "timed_out", "action_required", "startup_failure"}


def iter_log_files(logs_dir: pathlib.Path) -> Iterable[pathlib.Path]:
    if logs_dir.is_file():
        yield logs_dir
        return

    for path in sorted(logs_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".txt", ".log", ""}:
            yield path


def safe_read(path: pathlib.Path, max_chars: int) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"<failed to read {path}: {exc}>"
    if len(text) > max_chars:
        return text[-max_chars:]
    return text


def compact_line(line: str, max_len: int = 300) -> str:
    normalized = re.sub(r"\s+", " ", line).strip()
    if len(normalized) > max_len:
        return normalized[: max_len - 3] + "..."
    return normalized


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


def load_json(path: pathlib.Path) -> Any | None:
    if not path or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"_parse_error": str(exc)}


def parse_failed_jobs(jobs_json_path: pathlib.Path | None) -> tuple[list[JobFailure], str | None]:
    if jobs_json_path is None:
        return [], "No jobs.json path was provided."

    payload = load_json(jobs_json_path)
    if payload is None:
        return [], f"jobs.json not found at {jobs_json_path}"

    if isinstance(payload, dict) and "_parse_error" in payload:
        return [], f"Could not parse jobs.json: {payload['_parse_error']}"

    raw_jobs = payload.get("jobs") if isinstance(payload, dict) else None
    if not isinstance(raw_jobs, list):
        return [], "jobs.json did not contain a top-level jobs array."

    failed_jobs: list[JobFailure] = []

    for raw_job in raw_jobs:
        if not isinstance(raw_job, dict):
            continue

        conclusion = as_string(raw_job.get("conclusion"), default="unknown").lower()
        status = as_string(raw_job.get("status"), default="unknown").lower()
        raw_steps = raw_job.get("steps")
        steps = raw_steps if isinstance(raw_steps, list) else []

        failed_steps: list[StepFailure] = []
        for raw_step in steps:
            if not isinstance(raw_step, dict):
                continue
            step_conclusion = as_string(raw_step.get("conclusion"), default="unknown").lower()
            step_status = as_string(raw_step.get("status"), default="unknown").lower()
            if step_conclusion in FAILURE_CONCLUSIONS or step_status in FAILURE_STATUSES:
                failed_steps.append(
                    StepFailure(
                        name=as_string(raw_step.get("name")),
                        number=as_optional_int(raw_step.get("number")),
                        status=step_status,
                        conclusion=step_conclusion,
                        started_at=as_optional_string(raw_step.get("startedAt")),
                        completed_at=as_optional_string(raw_step.get("completedAt")),
                    )
                )

        # Classify failed jobs only from job-level status/conclusion.
        # Failed step metadata can exist in successful jobs when a step uses continue-on-error;
        # those jobs must not be listed as failed because it would misdirect triage.
        if conclusion in FAILURE_CONCLUSIONS or status in FAILURE_STATUSES:
            failed_jobs.append(
                JobFailure(
                    name=as_string(raw_job.get("name")),
                    database_id=as_optional_int(raw_job.get("databaseId")),
                    status=status,
                    conclusion=conclusion,
                    started_at=as_optional_string(raw_job.get("startedAt")),
                    completed_at=as_optional_string(raw_job.get("completedAt")),
                    url=as_optional_string(raw_job.get("url")),
                    failed_steps=tuple(failed_steps),
                )
            )

    return failed_jobs, None


def analyze(logs_dir: pathlib.Path, max_chars_per_file: int) -> tuple[list[Finding], Counter[str], list[str]]:
    findings: list[Finding] = []
    scanned_files: list[str] = []
    category_counts: Counter[str] = Counter()

    for path in iter_log_files(logs_dir):
        scanned_files.append(str(path))
        content = safe_read(path, max_chars=max_chars_per_file)
        lines = content.splitlines()

        for category, severity, pattern, recommendation in RULES:
            for line in lines:
                if pattern.search(line):
                    evidence = f"{path}: {compact_line(line)}"
                    findings.append(
                        Finding(
                            category=category,
                            severity=severity,
                            pattern=pattern.pattern,
                            evidence=evidence,
                            recommendation=recommendation,
                        )
                    )
                    category_counts[category] += 1
                    break

    return findings, category_counts, scanned_files


def markdown_escape_cell(value: str | None) -> str:
    if value is None:
        return ""
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_failed_steps(steps: tuple[StepFailure, ...]) -> str:
    if not steps:
        return "No failed step metadata available"
    fragments: list[str] = []
    for step in steps:
        number = f"#{step.number} " if step.number is not None else ""
        fragments.append(f"{number}{step.name} ({step.conclusion or step.status})")
    return "; ".join(fragments)


def render_markdown(
    findings: list[Finding],
    category_counts: Counter[str],
    scanned_files: list[str],
    failed_jobs: list[JobFailure],
    jobs_parse_warning: str | None,
    run_id: str | None,
    repository: str | None,
) -> str:
    lines: list[str] = []
    lines.append("# CI Failure Diagnostics Report")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append(f"- Repository: `{repository or 'unknown'}`")
    lines.append(f"- Workflow run ID: `{run_id or 'unknown'}`")
    lines.append(f"- Files scanned: `{len(scanned_files)}`")
    lines.append(f"- Findings: `{len(findings)}`")
    lines.append(f"- Failed jobs from metadata: `{len(failed_jobs)}`")
    lines.append("")

    lines.append("## Important limitation")
    lines.append("")
    lines.append("This report is deterministic and rule-based. It does not call an LLM and does not prove root cause by itself.")
    lines.append("Use it as an evidence index and triage aid. Confirm conclusions against workflow logs, artifacts, repository code, and verifier scripts.")
    lines.append("")

    if jobs_parse_warning:
        lines.append("## Jobs metadata warning")
        lines.append("")
        lines.append(f"- {jobs_parse_warning}")
        lines.append("")

    lines.append("## Failed jobs and steps")
    lines.append("")
    if not failed_jobs:
        lines.append("No failed job metadata was found in `jobs.json`.")
        lines.append("")
    else:
        lines.append("| Job | Conclusion | Status | Failed steps | Job URL |")
        lines.append("|---|---|---|---|---|")
        for job in failed_jobs:
            job_link = f"[open]({job.url})" if job.url else ""
            lines.append(
                "| "
                f"`{markdown_escape_cell(job.name)}` | "
                f"`{markdown_escape_cell(job.conclusion)}` | "
                f"`{markdown_escape_cell(job.status)}` | "
                f"{markdown_escape_cell(render_failed_steps(job.failed_steps))} | "
                f"{job_link} |"
            )
        lines.append("")

    if not scanned_files:
        lines.append("## Result")
        lines.append("")
        lines.append("No log files were found to analyze.")
        lines.append("")
        return "\n".join(lines)

    lines.append("## Scanned files")
    lines.append("")
    for item in scanned_files[:100]:
        lines.append(f"- `{item}`")
    if len(scanned_files) > 100:
        lines.append(f"- ... `{len(scanned_files) - 100}` more files omitted")
    lines.append("")

    if not findings:
        lines.append("## Result")
        lines.append("")
        lines.append("No known failure signatures were detected by the current rule set.")
        lines.append("")
        lines.append("Recommended next step: inspect the raw logs and extend `scripts/analyze-ci-failure.py` with a new deterministic rule if the failure pattern is repeatable.")
        lines.append("")
        return "\n".join(lines)

    lines.append("## Category summary")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---:|")
    for category, count in category_counts.most_common():
        lines.append(f"| `{category}` | {count} |")
    lines.append("")

    lines.append("## Findings")
    lines.append("")
    lines.append("| Severity | Category | Evidence | Recommendation |")
    lines.append("|---|---|---|---|")
    for finding in findings[:50]:
        evidence = markdown_escape_cell(finding.evidence)
        recommendation = markdown_escape_cell(finding.recommendation)
        lines.append(f"| `{finding.severity}` | `{finding.category}` | `{evidence}` | {recommendation} |")
    if len(findings) > 50:
        lines.append(f"| `info` | `truncated` | `{len(findings) - 50}` additional findings omitted | Inspect raw logs. |")
    lines.append("")

    lines.append("## Recommended triage order")
    lines.append("")
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
        if category_counts.get(category):
            lines.append(f"1. Investigate `{category}`")
    lines.append("")

    lines.append("## Next validation commands")
    lines.append("")
    lines.append("Use the smallest relevant validation first:")
    lines.append("")
    lines.append("```bash")
    lines.append("bash -n scripts/*.sh")
    lines.append("docker compose config")
    lines.append("./scripts/verify-milestone-1.sh")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze GitHub Actions logs with deterministic rules.")
    parser.add_argument("--logs-dir", required=True, type=pathlib.Path, help="Directory or file containing logs to scan")
    parser.add_argument("--output", required=True, type=pathlib.Path, help="Markdown output path")
    parser.add_argument("--jobs-json", type=pathlib.Path, default=None, help="Optional GitHub Actions jobs metadata JSON")
    parser.add_argument("--run-id", default=None, help="GitHub Actions workflow run ID")
    parser.add_argument("--repository", default=None, help="Repository full name")
    parser.add_argument("--max-chars-per-file", type=int, default=250_000, help="Maximum characters read from each log file")
    args = parser.parse_args()

    findings, category_counts, scanned_files = analyze(args.logs_dir, args.max_chars_per_file)
    failed_jobs, jobs_parse_warning = parse_failed_jobs(args.jobs_json)
    report = render_markdown(
        findings=findings,
        category_counts=category_counts,
        scanned_files=scanned_files,
        failed_jobs=failed_jobs,
        jobs_parse_warning=jobs_parse_warning,
        run_id=args.run_id,
        repository=args.repository,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report + "\n", encoding="utf-8")
    print(f"Wrote diagnostics report to {args.output}")
    print(f"Findings: {len(findings)}")
    print(f"Failed jobs from metadata: {len(failed_jobs)}")
    if jobs_parse_warning:
        print(f"Jobs metadata warning: {jobs_parse_warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
