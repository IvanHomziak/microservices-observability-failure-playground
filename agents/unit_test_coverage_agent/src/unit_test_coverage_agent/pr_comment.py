from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .output_schema import validate_contract
from .pr_summary_comment import COMMENT_MARKER, render_pr_summary_comment


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _load_text_if_exists(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def render_pr_comment(coverage_contract: dict[str, Any], patch_proposal: dict[str, Any]) -> str:
    errors = validate_contract(coverage_contract)
    if errors:
        raise ValueError("Invalid coverage contract: " + "; ".join(errors))
    return render_pr_summary_comment(coverage_contract, patch_proposal)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a PR comment from validated unit test coverage agent artifacts.")
    parser.add_argument("--coverage-json", required=True, type=Path)
    parser.add_argument("--patch-proposal-json", required=True, type=Path)
    parser.add_argument("--coverage-md", type=Path)
    parser.add_argument("--patch-proposal-md", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    coverage_contract = _load_json(args.coverage_json)
    patch_proposal = _load_json(args.patch_proposal_json)
    errors = validate_contract(coverage_contract)
    if errors:
        raise ValueError("Invalid coverage contract: " + "; ".join(errors))

    comment = render_pr_summary_comment(
        coverage_contract,
        patch_proposal,
        _load_text_if_exists(args.coverage_md),
        _load_text_if_exists(args.patch_proposal_md),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(comment + "\n", encoding="utf-8")
    print(f"Wrote PR comment to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
