from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Protocol

from .output_schema import render_contract_json, validate_contract
from .prompt_builder import build_coverage_reasoning_prompt

DEFAULT_MODEL = "gpt-4.1-mini"


@dataclass(frozen=True)
class ProviderResult:
    provider_name: str
    contract: dict
    model: str | None
    used_external_call: bool


class CoverageReasoningProvider(Protocol):
    name: str

    def refine(self, contract: dict) -> ProviderResult:
        """Return a validated coverage assessment contract."""


class DeterministicCoverageProvider:
    name = "deterministic"

    def refine(self, contract: dict) -> ProviderResult:
        errors = validate_contract(contract)
        if errors:
            raise ValueError("Invalid deterministic coverage contract: " + "; ".join(errors))
        return ProviderResult(
            provider_name=self.name,
            contract=contract,
            model=None,
            used_external_call=False,
        )


class LangChainOpenAICoverageProvider:
    name = "langchain-openai"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    def refine(self, contract: dict) -> ProviderResult:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required when provider=langchain-openai")

        prompt = build_coverage_reasoning_prompt(contract)
        output_text = self._invoke(prompt)
        refined_contract = self._parse_json_contract(output_text)
        errors = validate_contract(refined_contract)
        if errors:
            raise RuntimeError("LangChain provider returned invalid coverage contract: " + "; ".join(errors))

        return ProviderResult(
            provider_name=self.name,
            contract=refined_contract,
            model=self.model,
            used_external_call=True,
        )

    def _invoke(self, prompt: str) -> str:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise RuntimeError(
                "LangChain dependencies are required for provider=langchain-openai. "
                "Install package dependencies before running this provider."
            ) from exc

        model = ChatOpenAI(model=self.model, temperature=0)
        response = model.invoke(
            [
                SystemMessage(content="You are a read-only coverage reasoning agent. Return only valid JSON."),
                HumanMessage(content=prompt),
            ]
        )
        content = getattr(response, "content", None)
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("LangChain provider returned an empty response")
        return content.strip()

    @staticmethod
    def _parse_json_contract(output_text: str) -> dict:
        try:
            payload = json.loads(output_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("LangChain provider returned non-JSON content") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("LangChain provider returned JSON that is not an object")
        return payload


def get_provider(name: str) -> CoverageReasoningProvider:
    normalized = name.strip().lower()
    if normalized == "deterministic":
        return DeterministicCoverageProvider()
    if normalized in {"langchain", "langchain-openai"}:
        return LangChainOpenAICoverageProvider()
    raise ValueError(f"Unsupported coverage reasoning provider: {name}")
