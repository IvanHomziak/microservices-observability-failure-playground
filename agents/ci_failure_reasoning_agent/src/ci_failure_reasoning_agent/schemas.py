from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EvidencePack:
    evidence_dir: str
    run: dict[str, Any]
    jobs: dict[str, Any]
    diagnostics_report: str
    agent_fix_plan: str
    workflow_log_excerpt: str
    agents_instructions_excerpt: str
    missing_files: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ReasoningReport:
    executive_summary: str
    evidence_inspected: tuple[str, ...]
    failed_workflow: str
    failed_jobs_and_steps: tuple[str, ...]
    symptoms: tuple[str, ...]
    root_cause_hypotheses: tuple[str, ...]
    confidence: str
    missing_evidence: tuple[str, ...]
    recommended_fix: tuple[str, ...]
    files_likely_affected: tuple[str, ...]
    files_not_to_change_casually: tuple[str, ...]
    validation_plan: tuple[str, ...]
    risk_assessment: str
