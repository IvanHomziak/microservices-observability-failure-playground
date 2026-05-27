from __future__ import annotations

from .git_diff import SERVICE_ROOTS
from .models import GitDiffEvidence

RELEVANT_SERVICE_CATEGORIES = {"production-java", "test-java", "build-config", "service-other"}
GLOBAL_TRIGGER_PATH_PREFIXES = (
    ".github/workflows/",
    "agents/unit_test_coverage_agent/",
)
GLOBAL_TRIGGER_PATHS = {
    "coverage-policy.yml",
    "coverage-policy-pr.yml",
}


def detect_affected_services(git: GitDiffEvidence) -> tuple[str, ...]:
    changed_paths = git.raw_changed_files
    if any(path in GLOBAL_TRIGGER_PATHS for path in changed_paths) or any(
        path.startswith(prefix) for path in changed_paths for prefix in GLOBAL_TRIGGER_PATH_PREFIXES
    ):
        return tuple(sorted(SERVICE_ROOTS))

    services = {
        item.service
        for item in git.changed_files
        if item.service is not None and item.category in RELEVANT_SERVICE_CATEGORIES
    }
    return tuple(sorted(services))
