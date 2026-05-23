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


def classify_file(path: str) -> ChangedFile:
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

    return ChangedFile(path=path, category=category, service=service)


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
    output = _run_git(["diff", "--name-only", diff_range], repository_root)
    raw_files = tuple(line.strip() for line in output.splitlines() if line.strip())
    changed_files = tuple(classify_file(path) for path in raw_files)
    return GitDiffEvidence(
        base_ref=base_ref,
        head_ref=head_ref,
        changed_files=changed_files,
        raw_changed_files=raw_files,
    )
