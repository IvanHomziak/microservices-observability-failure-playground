from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from .output_schema import contract_from_report, render_contract_json, validate_contract
from .renderer import render_markdown
from .schemas import ReasoningReport

OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


@dataclass(frozen=True)
class ProviderResult:
    provider_name: str
    content: str
    json_content: str | None = None
    model: str | None = None
    used_external_call: bool = False


class ReasoningProvider(Protocol):
    name: str

    def generate(self, *, prompt: str, deterministic_report: ReasoningReport) -> ProviderResult:
        """Generate a reasoning response from a bounded prompt and deterministic report."""


class DeterministicReasoningProvider:
    """Default provider that performs no external call.

    It returns the deterministic report rendered by the local reasoning engine.
    """

    name = "deterministic"

    def generate(self, *, prompt: str, deterministic_report: ReasoningReport) -> ProviderResult:
        del prompt
        contract = contract_from_report(deterministic_report)
        return ProviderResult(
            provider_name=self.name,
            model=None,
            used_external_call=False,
            content=render_markdown(deterministic_report),
            json_content=render_contract_json(contract),
        )


class OpenAIReasoningProvider:
    """Optional OpenAI provider over bounded evidence.

    This provider is manual-only by workflow design. It performs no repository
    mutation and requires OPENAI_API_KEY to be explicitly available in the runtime
    environment. Its JSON output must validate against the local contract before
    it is trusted.
    """

    name = "openai"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    def generate(self, *, prompt: str, deterministic_report: ReasoningReport) -> ProviderResult:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required when provider=openai")

        deterministic_contract = contract_from_report(deterministic_report)
        request_prompt = _build_json_only_prompt(prompt, deterministic_contract)
        response_payload = _call_openai_responses_api(api_key=api_key, model=self.model, prompt=request_prompt)
        output_text = _extract_output_text(response_payload)
        contract = _parse_contract(output_text)
        errors = validate_contract(contract)
        if errors:
            raise RuntimeError("OpenAI provider returned invalid reasoning contract: " + "; ".join(errors))

        return ProviderResult(
            provider_name=self.name,
            model=self.model,
            used_external_call=True,
            content=output_text,
            json_content=render_contract_json(contract),
        )


def _build_json_only_prompt(prompt: str, deterministic_contract: dict[str, Any]) -> str:
    schema_keys = sorted(deterministic_contract.keys())
    return "\n\n".join(
        [
            prompt,
            "# Output contract",
            "Return only valid JSON. Do not wrap it in markdown. Do not include prose outside JSON.",
            "The JSON object must use exactly this schema version: 1.0.",
            "Required top-level keys:",
            "\n".join(f"- {key}" for key in schema_keys),
            "Allowed confidence values: low, medium, high.",
            "All list fields must be non-empty arrays of strings.",
            "The safety_boundary must state that the output is read-only and does not authorize code mutation, PR creation, deployment, secrets access, permission escalation, or automatic remediation.",
            "Use this deterministic contract as a safe baseline. You may improve wording only when supported by evidence:",
            json.dumps(deterministic_contract, indent=2, sort_keys=True, ensure_ascii=False),
        ]
    )


def _call_openai_responses_api(*, api_key: str, model: str, prompt: str) -> dict[str, Any]:
    request_body = json.dumps(
        {
            "model": model,
            "input": prompt,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        OPENAI_RESPONSES_ENDPOINT,
        data=request_body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API request failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI API request failed: {exc}") from exc

    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI API returned non-JSON response") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("OpenAI API returned unexpected response shape")
    return parsed


def _extract_output_text(response_payload: dict[str, Any]) -> str:
    output_text = response_payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    fragments: list[str] = []
    output = response_payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str):
                    fragments.append(text)
    joined = "\n".join(fragments).strip()
    if not joined:
        raise RuntimeError("OpenAI API response did not contain output_text")
    return joined


def _parse_contract(output_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("OpenAI provider returned non-JSON content") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("OpenAI provider returned JSON that is not an object")
    return payload


def get_provider(name: str) -> ReasoningProvider:
    normalized = name.strip().lower()
    if normalized == "deterministic":
        return DeterministicReasoningProvider()
    if normalized == "openai":
        return OpenAIReasoningProvider()
    if normalized in {"external", "llm"}:
        raise RuntimeError("Provider alias is disabled. Use provider=openai explicitly after environment review.")
    raise ValueError(f"Unsupported provider: {name}")
