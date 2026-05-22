from __future__ import annotations

import argparse
from pathlib import Path

from .evidence_loader import load_evidence_pack
from .output_schema import contract_from_report, render_contract_json
from .prompt_builder import build_reasoning_prompt
from .providers import get_provider
from .reasoner import reason


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only CI failure reasoning report from a bounded evidence pack.")
    parser.add_argument("--evidence-dir", required=True, type=Path, help="Directory containing triage/raw, triage/logs, and triage/output evidence")
    parser.add_argument("--repository-root", required=True, type=Path, help="Repository root containing AGENTS.md")
    parser.add_argument("--output", required=True, type=Path, help="Markdown output file")
    parser.add_argument("--json-output", type=Path, default=None, help="Optional validated structured JSON output file")
    parser.add_argument("--prompt-output", type=Path, default=None, help="Optional path for the generated bounded reasoning prompt artifact")
    parser.add_argument("--provider", default="deterministic", help="Reasoning provider name. Only 'deterministic' is enabled in this scaffold.")
    args = parser.parse_args()

    evidence = load_evidence_pack(args.evidence_dir, args.repository_root)
    deterministic_report = reason(evidence)
    contract = contract_from_report(deterministic_report)
    prompt = build_reasoning_prompt(evidence)
    provider = get_provider(args.provider)
    provider_result = provider.generate(prompt=prompt, deterministic_report=deterministic_report)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(provider_result.content + "\n", encoding="utf-8")

    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(render_contract_json(contract) + "\n", encoding="utf-8")
        print(f"Wrote validated structured JSON report to {args.json_output}")

    if args.prompt_output is not None:
        args.prompt_output.parent.mkdir(parents=True, exist_ok=True)
        args.prompt_output.write_text(prompt + "\n", encoding="utf-8")
        print(f"Wrote bounded reasoning prompt to {args.prompt_output}")

    print(f"Wrote agent diagnostic report to {args.output}")
    print(f"Provider: {provider_result.provider_name}")
    print(f"External call used: {provider_result.used_external_call}")
    print(f"Confidence: {deterministic_report.confidence}")
    print(f"JSON schema version: {contract['schema_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
