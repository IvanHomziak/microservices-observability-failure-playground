from __future__ import annotations

import argparse
from pathlib import Path

from .evidence_loader import load_evidence_pack
from .reasoner import reason
from .renderer import render_markdown


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a read-only CI failure reasoning report from a bounded evidence pack.")
    parser.add_argument("--evidence-dir", required=True, type=Path, help="Directory containing triage/raw, triage/logs, and triage/output evidence")
    parser.add_argument("--repository-root", required=True, type=Path, help="Repository root containing AGENTS.md")
    parser.add_argument("--output", required=True, type=Path, help="Markdown output file")
    args = parser.parse_args()

    evidence = load_evidence_pack(args.evidence_dir, args.repository_root)
    report = reason(evidence)
    rendered = render_markdown(report)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(f"Wrote agent diagnostic report to {args.output}")
    print(f"Confidence: {report.confidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
