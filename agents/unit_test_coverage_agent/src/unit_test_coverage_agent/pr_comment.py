from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .output_schema import render_contract_json, validate_contract
from .providers import DEFAULT_MODEL
from .pr_summary_comment import COMMENT_MARKER, render_pr_summary_comment

MAX_LLM_MARKDOWN_CHARS = 8_000
MAX_LLM_RESPONSE_CHARS = 12_000
LLM_SUMMARY_UNAVAILABLE_NOTE = "LLM summary unavailable due to invalid response."
ALLOWED_RISK_ASSESSMENTS = {"low", "medium", "high"}


class MissingOpenAIAPIKeyError(RuntimeError):
    """Raised when optional PR-comment LLM enhancement is requested without a key."""


class InvalidLLMCommentSummaryError(RuntimeError):
    """Raised when the optional PR-comment LLM response cannot be safely rendered."""


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


def _truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars].rstrip() + "\n\n<truncated>"


def build_pr_comment_llm_prompt(
    coverage_contract: dict[str, Any],
    patch_proposal: dict[str, Any],
    coverage_markdown: str | None = None,
) -> str:
    """Build a bounded prompt for optional advisory PR-comment summary text."""

    prompt_parts = [
        "# OpenAI-enhanced Unit Test Coverage PR Comment Task",
        "You are improving the explanation in a GitHub PR comment from validated deterministic artifacts.",
        "Reason only from the evidence provided in this prompt.",
        "Do not invent files, classes, methods, tests, services, coverage percentages, Maven status, commands, or workflow behavior.",
        "Do not claim tests exist unless the evidence says they exist.",
        "Do not recommend deleting tests or weakening verification.",
        "You must not change pass/fail or policy facts. Deterministic policy facts remain authoritative.",
        "You must not change coverage_status, merge_recommendation, policy_violations, policy_warnings, changed files, coverage percentages, affected services, test failure counts, or Maven failure status.",
        "Return JSON only. Do not wrap the response in markdown. Do not add prose outside JSON.",
        "The JSON object must contain exactly these fields:",
        '{"executive_summary":"...","reviewer_guidance":["..."],"developer_next_steps":["..."],"risk_assessment":"low|medium|high","limitations":["..."]}',
        "Keep each string concise and evidence-based.",
        "# Validated coverage JSON",
        render_contract_json(coverage_contract),
        "# Validated patch proposal JSON",
        json.dumps(patch_proposal, indent=2, sort_keys=True, ensure_ascii=False),
    ]
    if coverage_markdown:
        prompt_parts.extend(["# Trimmed deterministic Markdown report", _truncate(coverage_markdown, MAX_LLM_MARKDOWN_CHARS)])
    return "\n\n".join(prompt_parts)


def _invoke_openai_summary(prompt: str, model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingOpenAIAPIKeyError("OPENAI_API_KEY repository secret is required when use_llm_summary=true")

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": "You are a read-only coverage comment assistant. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"OpenAI PR comment summary request failed with HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError("OpenAI PR comment summary request failed") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI PR comment summary response was not valid JSON") from exc

    try:
        content = response_payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("OpenAI PR comment summary response did not include message content") from exc
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("OpenAI PR comment summary response was empty")
    return content.strip()


def parse_and_validate_llm_summary(output_text: str) -> dict[str, Any]:
    if len(output_text) > MAX_LLM_RESPONSE_CHARS:
        raise InvalidLLMCommentSummaryError("LLM summary response exceeded the allowed size")
    try:
        payload = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise InvalidLLMCommentSummaryError("LLM summary response was not valid JSON") from exc
    return validate_llm_summary(payload)


def validate_llm_summary(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise InvalidLLMCommentSummaryError("LLM summary response must be a JSON object")

    expected_fields = {
        "executive_summary",
        "reviewer_guidance",
        "developer_next_steps",
        "risk_assessment",
        "limitations",
    }
    actual_fields = set(payload)
    if actual_fields != expected_fields:
        extra = sorted(actual_fields - expected_fields)
        missing = sorted(expected_fields - actual_fields)
        details = []
        if missing:
            details.append(f"missing fields: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected fields: {', '.join(extra)}")
        raise InvalidLLMCommentSummaryError("Invalid LLM summary fields: " + "; ".join(details))

    executive_summary = payload["executive_summary"]
    if not isinstance(executive_summary, str) or not executive_summary.strip():
        raise InvalidLLMCommentSummaryError("LLM executive_summary must be a non-empty string")

    risk_assessment = payload["risk_assessment"]
    if not isinstance(risk_assessment, str) or risk_assessment not in ALLOWED_RISK_ASSESSMENTS:
        raise InvalidLLMCommentSummaryError("LLM risk_assessment must be low, medium, or high")

    validated: dict[str, Any] = {
        "executive_summary": executive_summary.strip(),
        "risk_assessment": risk_assessment,
    }
    for field in ("reviewer_guidance", "developer_next_steps", "limitations"):
        values = payload[field]
        if not isinstance(values, list) or not values:
            raise InvalidLLMCommentSummaryError(f"LLM {field} must be a non-empty list")
        cleaned: list[str] = []
        for index, value in enumerate(values):
            if not isinstance(value, str) or not value.strip():
                raise InvalidLLMCommentSummaryError(f"LLM {field}[{index}] must be a non-empty string")
            cleaned.append(value.strip())
        validated[field] = cleaned
    return validated


def generate_llm_summary(
    coverage_contract: dict[str, Any],
    patch_proposal: dict[str, Any],
    coverage_markdown: str | None,
    model: str,
) -> dict[str, Any]:
    prompt = build_pr_comment_llm_prompt(coverage_contract, patch_proposal, coverage_markdown)
    return parse_and_validate_llm_summary(_invoke_openai_summary(prompt, model))


def render_pr_comment(
    coverage_contract: dict[str, Any],
    patch_proposal: dict[str, Any],
    *,
    llm_summary: dict[str, Any] | None = None,
    llm_note: str | None = None,
) -> str:
    errors = validate_contract(coverage_contract)
    if errors:
        raise ValueError("Invalid coverage contract: " + "; ".join(errors))
    return render_pr_summary_comment(coverage_contract, patch_proposal, llm_summary=llm_summary, llm_note=llm_note)


def _write_llm_summary_artifact(path: Path | None, payload: dict[str, Any] | None, note: str | None, model: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": model,
        "summary_available": payload is not None,
        "summary": payload,
        "note": note,
    }
    path.write_text(json.dumps(artifact, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a PR comment from validated unit test coverage agent artifacts.")
    parser.add_argument("--coverage-json", required=True, type=Path)
    parser.add_argument("--patch-proposal-json", required=True, type=Path)
    parser.add_argument("--coverage-md", type=Path)
    parser.add_argument("--patch-proposal-md", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--use-llm-summary", action="store_true")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--llm-summary-output", type=Path)
    args = parser.parse_args()

    coverage_contract = _load_json(args.coverage_json)
    patch_proposal = _load_json(args.patch_proposal_json)
    errors = validate_contract(coverage_contract)
    if errors:
        raise ValueError("Invalid coverage contract: " + "; ".join(errors))

    coverage_markdown = _load_text_if_exists(args.coverage_md)
    patch_proposal_markdown = _load_text_if_exists(args.patch_proposal_md)
    llm_summary: dict[str, Any] | None = None
    llm_note: str | None = None

    if args.use_llm_summary:
        try:
            llm_summary = generate_llm_summary(coverage_contract, patch_proposal, coverage_markdown, args.model)
        except MissingOpenAIAPIKeyError:
            raise
        except Exception as exc:
            llm_note = LLM_SUMMARY_UNAVAILABLE_NOTE
            print(f"{LLM_SUMMARY_UNAVAILABLE_NOTE} Reason: {exc}")
        _write_llm_summary_artifact(args.llm_summary_output, llm_summary, llm_note, args.model)

    comment = render_pr_summary_comment(
        coverage_contract,
        patch_proposal,
        coverage_markdown,
        patch_proposal_markdown,
        llm_summary=llm_summary,
        llm_note=llm_note,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(comment + "\n", encoding="utf-8")
    print(f"Wrote PR comment to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
