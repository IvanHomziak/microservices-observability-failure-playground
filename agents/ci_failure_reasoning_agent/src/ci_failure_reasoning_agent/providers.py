from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .renderer import render_markdown
from .schemas import ReasoningReport


@dataclass(frozen=True)
class ProviderResult:
    provider_name: str
    content: str
    model: str | None = None
    used_external_call: bool = False


class ReasoningProvider(Protocol):
    name: str

    def generate(self, *, prompt: str, deterministic_report: ReasoningReport) -> ProviderResult:
        """Generate a reasoning response from a bounded prompt and deterministic report."""


class DeterministicReasoningProvider:
    """Default provider that performs no external call.

    It returns the deterministic report rendered by the local reasoning engine.
    This is the only enabled provider in the current scaffold.
    """

    name = "deterministic"

    def generate(self, *, prompt: str, deterministic_report: ReasoningReport) -> ProviderResult:
        del prompt
        return ProviderResult(
            provider_name=self.name,
            model=None,
            used_external_call=False,
            content=render_markdown(deterministic_report),
        )


class DisabledExternalProvider:
    """Placeholder for future LLM providers.

    This class intentionally fails closed. A real external provider must be added
    in a separate PR with explicit security review, environment protection,
    structured output validation, and no PR write permissions.
    """

    name = "disabled-external"

    def generate(self, *, prompt: str, deterministic_report: ReasoningReport) -> ProviderResult:
        del prompt, deterministic_report
        raise RuntimeError(
            "External provider is disabled in this scaffold. Add a reviewed provider implementation in a separate PR."
        )


def get_provider(name: str) -> ReasoningProvider:
    normalized = name.strip().lower()
    if normalized == "deterministic":
        return DeterministicReasoningProvider()
    if normalized in {"external", "llm", "openai"}:
        return DisabledExternalProvider()
    raise ValueError(f"Unsupported provider: {name}")
