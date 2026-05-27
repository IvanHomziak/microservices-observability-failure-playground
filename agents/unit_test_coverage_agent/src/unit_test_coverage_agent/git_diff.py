from __future__ import annotations

import subprocess
from pathlib import Path

from .models import ChangedFile, GitDiffEvidence

SERVICE_ROOTS = {
    "api-gateway",
    "orders-service",
    "payments-service",
    "inventory-service",
    "notification-service",
    "audit-service",
}


def _normalize_change_status(raw_status: str) -> str:
    status = (raw_status or "").strip().upper()
    if status.startswith("A"):
        return "added"
    if status.startswith("M"):
        return "modified"
    if status.startswith("D"):
        return "deleted"
    if status.startswith("R"):
        return "renamed"
    if status.startswith("C"):
        return "copied"
    return "unknown"


def classify_file(path: str, change_status: str = "unknown") -> ChangedFile:
    parts = path.split("/")
    service = parts[0] if parts and parts[0] in SERVICE_ROOTS else None

    if path.endswith(".md") or path.startswith("docs/"):
        category = "docs"
    elif path.startswith(".github/workflows/"):
        category = "workflow"
    elif service and "/src/test/" in path and path.endswith(".java"):
        category = "test-java"
    elif service and "/src/main/" in path and path.endswith(".java"):
        category = "production-java"
    elif service and path.endswith("pom.xml"):
        category = "build-config"
    elif service:
        category = "service-other"
    else:
        category = "other"

    return ChangedFile(path=path, category=category, service=service, change_status=change_status)


def _run_git(args: list[str], repository_root: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repository_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout


def load_changed_files(repository_root: Path, base_ref: str, head_ref: str) -> GitDiffEvidence:
    diff_range = f"{base_ref}...{head_ref}"
    output = _run_git(["diff", "--name-status", "--find-renames", "--find-copies", diff_range], repository_root)
    raw_files: list[str] = []
    changed_files_list: list[ChangedFile] = []
    for line in output.splitlines():
        entry = line.strip()
        if not entry:
            continue
        parts = entry.split("\t")
        if len(parts) < 2:
            continue
        status = _normalize_change_status(parts[0])
        path = parts[-1].strip()
        if not path:
            continue
        raw_files.append(path)
        changed_files_list.append(classify_file(path, change_status=status))
    raw_files_tuple = tuple(raw_files)
    changed_files = tuple(changed_files_list)
    return GitDiffEvidence(
        base_ref=base_ref,
        head_ref=head_ref,
        changed_files=changed_files,
        raw_changed_files=raw_files_tuple,
    )
