from __future__ import annotations

import argparse
from pathlib import Path

from .assessment import assess_coverage
from .git_diff import load_changed_files
from .jacoco_loader import load_jacoco_evidence
from .output_schema import assessment_to_contract, render_contract_json
from .renderer import render_markdown
from .surefire_loader import load_surefire_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic unit test coverage evidence report.")
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--base-ref", required=True, help="Base git ref, for example origin/main")
    parser.add_argument("--head-ref", required=True, help="Head git ref, for example HEAD")
    parser.add_argument("--output", required=True, type=Path, help="Markdown report output path")
    parser.add_argument("--json-output", required=True, type=Path, help="Validated JSON report output path")
    args = parser.parse_args()

    git = load_changed_files(args.repository_root, args.base_ref, args.head_ref)
    surefire = load_surefire_evidence(args.repository_root)
    jacoco = load_jacoco_evidence(args.repository_root)
    assessment = assess_coverage(git, surefire, jacoco)
    contract = assessment_to_contract(assessment)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)

    args.output.write_text(render_markdown(contract) + "\n", encoding="utf-8")
    args.json_output.write_text(render_contract_json(contract) + "\n", encoding="utf-8")

    print(f"Wrote coverage markdown report to {args.output}")
    print(f"Wrote coverage JSON report to {args.json_output}")
    print(f"Coverage status: {contract['coverage_status']}")
    print(f"Merge recommendation: {contract['merge_recommendation']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
