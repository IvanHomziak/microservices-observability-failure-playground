from __future__ import annotations

import argparse
import json
from pathlib import Path

from .assessment import assess_coverage
from .git_diff import load_changed_files
from .jacoco_loader import load_jacoco_evidence
from .output_schema import assessment_to_contract, render_contract_json
from .patch_proposal import build_patch_proposal, patch_proposal_to_dict, render_patch_proposal_markdown
from .providers import get_provider
from .renderer import render_markdown
from .surefire_loader import load_surefire_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate unit test coverage evidence and optional LangChain reasoning report.")
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--base-ref", required=True, help="Base git ref, for example origin/main")
    parser.add_argument("--head-ref", required=True, help="Head git ref, for example HEAD")
    parser.add_argument("--provider", default="deterministic", help="Reasoning provider: deterministic or langchain-openai")
    parser.add_argument("--output", required=True, type=Path, help="Markdown report output path")
    parser.add_argument("--json-output", required=True, type=Path, help="Validated JSON report output path")
    parser.add_argument("--prompt-output", type=Path, default=None, help="Optional bounded prompt artifact output path")
    parser.add_argument("--patch-proposal-output", type=Path, default=None, help="Optional markdown patch proposal artifact output path")
    parser.add_argument("--patch-proposal-json-output", type=Path, default=None, help="Optional JSON patch proposal artifact output path")
    args = parser.parse_args()

    git = load_changed_files(args.repository_root, args.base_ref, args.head_ref)
    surefire = load_surefire_evidence(args.repository_root)
    jacoco = load_jacoco_evidence(args.repository_root)
    assessment = assess_coverage(git, surefire, jacoco)
    deterministic_contract = assessment_to_contract(assessment)

    if args.prompt_output is not None:
        from .prompt_builder import build_coverage_reasoning_prompt

        args.prompt_output.parent.mkdir(parents=True, exist_ok=True)
        args.prompt_output.write_text(build_coverage_reasoning_prompt(deterministic_contract) + "\n", encoding="utf-8")
        print(f"Wrote coverage reasoning prompt to {args.prompt_output}")

    provider = get_provider(args.provider)
    provider_result = provider.refine(deterministic_contract)
    contract = provider_result.contract

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)

    args.output.write_text(render_markdown(contract) + "\n", encoding="utf-8")
    args.json_output.write_text(render_contract_json(contract) + "\n", encoding="utf-8")

    patch_proposal = build_patch_proposal(contract)
    patch_proposal_dict = patch_proposal_to_dict(patch_proposal)

    if args.patch_proposal_output is not None:
        args.patch_proposal_output.parent.mkdir(parents=True, exist_ok=True)
        args.patch_proposal_output.write_text(render_patch_proposal_markdown(patch_proposal) + "\n", encoding="utf-8")
        print(f"Wrote patch proposal markdown artifact to {args.patch_proposal_output}")

    if args.patch_proposal_json_output is not None:
        args.patch_proposal_json_output.parent.mkdir(parents=True, exist_ok=True)
        args.patch_proposal_json_output.write_text(json.dumps(patch_proposal_dict, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote patch proposal JSON artifact to {args.patch_proposal_json_output}")

    print(f"Wrote coverage markdown report to {args.output}")
    print(f"Wrote coverage JSON report to {args.json_output}")
    print(f"Provider: {provider_result.provider_name}")
    print(f"External call used: {provider_result.used_external_call}")
    print(f"Model: {provider_result.model or 'none'}")
    print(f"Coverage status: {contract['coverage_status']}")
    print(f"Merge recommendation: {contract['merge_recommendation']}")
    print(f"Patch proposal status: {patch_proposal.proposal_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
