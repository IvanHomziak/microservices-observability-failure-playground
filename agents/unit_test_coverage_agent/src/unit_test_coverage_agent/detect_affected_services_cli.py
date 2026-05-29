from __future__ import annotations

import argparse
from pathlib import Path

from .affected_services import detect_affected_services
from .git_diff import load_changed_files


def _write_lines(path: Path, values: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(values) + ("\n" if values else ""), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect changed files and affected services for coverage workflows.")
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--base-ref", required=True, help="Base git ref, for example origin/main")
    parser.add_argument("--head-ref", required=True, help="Head git ref, for example HEAD")
    parser.add_argument("--changed-files-output", required=True, type=Path)
    parser.add_argument("--affected-services-output", required=True, type=Path)
    args = parser.parse_args()

    git = load_changed_files(args.repository_root, args.base_ref, args.head_ref)
    affected = detect_affected_services(git)

    _write_lines(args.changed_files_output, git.raw_changed_files)
    _write_lines(args.affected_services_output, affected)

    print(f"Detected changed files: {len(git.raw_changed_files)}")
    print(f"Detected affected services: {', '.join(affected) if affected else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
