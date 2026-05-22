from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import EvidencePack

MAX_TEXT_CHARS = 80_000
MAX_LOG_CHARS = 120_000
MAX_INSTRUCTIONS_CHARS = 30_000


def _read_text(path: Path, *, max_chars: int) -> tuple[str, bool]:
    if not path.exists():
        return "", False
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[-max_chars:], True
    return text, False


def _read_json(path: Path) -> tuple[dict[str, Any], bool]:
    if not path.exists():
        return {}, False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_parse_error": f"Invalid JSON: {path}"}, True
    if isinstance(payload, dict):
        return payload, True
    return {"_parse_error": f"Expected object JSON: {path}"}, True


def load_evidence_pack(evidence_dir: Path, repository_root: Path) -> EvidencePack:
    missing: list[str] = []
    truncation_notes: list[str] = []

    run_json = evidence_dir / "raw" / "run.json"
    jobs_json = evidence_dir / "raw" / "jobs.json"
    diagnostics_report = evidence_dir / "output" / "ci-failure-diagnostics-report.md"
    agent_fix_plan = evidence_dir / "output" / "agent-fix-plan.md"
    workflow_log = evidence_dir / "logs" / "workflow-run.log"
    agents_md = repository_root / "AGENTS.md"

    run, run_exists = _read_json(run_json)
    jobs, jobs_exists = _read_json(jobs_json)
    diagnostics_text, diagnostics_truncated = _read_text(diagnostics_report, max_chars=MAX_TEXT_CHARS)
    fix_plan_text, fix_plan_truncated = _read_text(agent_fix_plan, max_chars=MAX_TEXT_CHARS)
    workflow_log_text, workflow_log_truncated = _read_text(workflow_log, max_chars=MAX_LOG_CHARS)
    agents_text, agents_truncated = _read_text(agents_md, max_chars=MAX_INSTRUCTIONS_CHARS)

    for path, exists in (
        (run_json, run_exists),
        (jobs_json, jobs_exists),
        (diagnostics_report, bool(diagnostics_text)),
        (agent_fix_plan, bool(fix_plan_text)),
        (workflow_log, bool(workflow_log_text)),
        (agents_md, bool(agents_text)),
    ):
        if not exists:
            missing.append(str(path))

    if diagnostics_truncated:
        truncation_notes.append("diagnostics report was truncated")
    if fix_plan_truncated:
        truncation_notes.append("agent fix plan was truncated")
    if workflow_log_truncated:
        truncation_notes.append("workflow log was truncated to latest content")
    if agents_truncated:
        truncation_notes.append("AGENTS.md was truncated")

    if truncation_notes:
        missing.extend(truncation_notes)

    return EvidencePack(
        evidence_dir=str(evidence_dir),
        run=run,
        jobs=jobs,
        diagnostics_report=diagnostics_text,
        agent_fix_plan=fix_plan_text,
        workflow_log_excerpt=workflow_log_text,
        agents_instructions_excerpt=agents_text,
        missing_files=tuple(missing),
    )
