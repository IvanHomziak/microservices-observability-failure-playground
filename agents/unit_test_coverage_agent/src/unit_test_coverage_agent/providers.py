from __future__ import annotations

import json
import os
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Protocol

from .output_schema import validate_contract
from .prompt_builder import build_coverage_reasoning_prompt

DEFAULT_MODEL = "gpt-4.1-mini"

AUTHORITATIVE_FIELDS = (
    "coverage_status",
    "merge_recommendation",
    "policy_violations",
    "policy_warnings",
)

ADVISORY_FIELDS = (
    "missing_test_scenarios",
    "recommended_tests",
    "blocking_reasons",
    "confidence",
)

LLM_FALLBACK_WARNING = "LLM advisory refinement unavailable; deterministic coverage contract was used."
MAX_WARNING_DETAIL_CHARS = 600


@dataclass(frozen=True)
class ProviderResult:
    provider_name: str
    contract: dict
    model: str | None
    used_external_call: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)


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

    def __init__(self, model: str | None = None, fallback_on_invalid_response: bool = False) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
        self.fallback_on_invalid_response = fallback_on_invalid_response

    def refine(self, contract: dict) -> ProviderResult:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for provider=langchain-openai")

        deterministic_errors = validate_contract(contract)
        if deterministic_errors:
            raise ValueError("Invalid deterministic coverage contract: " + "; ".join(deterministic_errors))

        prompt = build_coverage_reasoning_prompt(contract)
        try:
            output_text = self._invoke(prompt)
            advisory_contract = self._parse_json_contract(output_text)
            errors = validate_contract(advisory_contract)
            if errors:
                return self._handle_invalid_response(contract, "LangChain provider returned invalid coverage contract: " + "; ".join(errors))

            authority_errors = self._validate_authoritative_fields(contract, advisory_contract)
            if authority_errors:
                return self._handle_invalid_response(
                    contract,
                    "LangChain provider attempted to modify deterministic policy fields: " + "; ".join(authority_errors),
                )

            refined_contract = self._merge_advisory_fields(contract, advisory_contract)
            errors = validate_contract(refined_contract)
            if errors:
                return self._handle_invalid_response(contract, "Merged LangChain coverage contract is invalid: " + "; ".join(errors))

            return ProviderResult(
                provider_name=self.name,
                contract=refined_contract,
                model=self.model,
                used_external_call=True,
            )
        except Exception as exc:
            return self._handle_invalid_response(contract, f"{type(exc).__name__}: {exc}")

    def _handle_invalid_response(self, deterministic_contract: dict, reason: str) -> ProviderResult:
        if self.fallback_on_invalid_response:
            return self._fallback_result(deterministic_contract, reason)
        raise RuntimeError(reason)

    def _fallback_result(self, deterministic_contract: dict, reason: str) -> ProviderResult:
        return ProviderResult(
            provider_name=self.name,
            contract=deepcopy(deterministic_contract),
            model=self.model,
            used_external_call=True,
            warnings=(LLM_FALLBACK_WARNING, self._truncate_warning_detail(reason)),
        )

    @staticmethod
    def _truncate_warning_detail(reason: str) -> str:
        normalized = " ".join(reason.split())
        if len(normalized) <= MAX_WARNING_DETAIL_CHARS:
            return normalized
        return normalized[:MAX_WARNING_DETAIL_CHARS].rstrip() + "..."

    @staticmethod
    def _validate_authoritative_fields(deterministic_contract: dict, advisory_contract: dict) -> list[str]:
        errors: list[str] = []
        for field in AUTHORITATIVE_FIELDS:
            if advisory_contract.get(field) != deterministic_contract.get(field):
                errors.append(f"{field} must remain deterministic")
        return errors

    @staticmethod
    def _merge_advisory_fields(deterministic_contract: dict, advisory_contract: dict) -> dict:
        refined_contract = deepcopy(deterministic_contract)
        for field in ADVISORY_FIELDS:
            if field in advisory_contract:
                refined_contract[field] = advisory_contract[field]
        return refined_contract

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
        return LangChainOpenAICoverageProvider(fallback_on_invalid_response=True)
    raise ValueError(f"Unsupported coverage reasoning provider: {name}")
