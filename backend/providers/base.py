"""LLM provider abstract base and shared types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from pydantic import BaseModel


PENTEST_SYSTEM_PROMPT = """\
You are an expert penetration tester providing technical guidance.
All identifying details in the prompt have been replaced with tokens
in the format [XXXX_XXXXXXXX] (e.g. [IPADDR_1b2c3d4e]).
Treat tokens as opaque identifiers — never guess their real values.
When referencing entities in your response, always use the exact token
format provided so that automatic de-tokenization can be applied.
Never modify, translate, split, or remove tokens.
Tokens are case-sensitive. Reproduce them character-for-character
including brackets.
Provide specific, actionable technical guidance based on the structure
of the request."""

# FIX: configurable system prompt — preset resolution
AVAILABLE_SYSTEM_PROMPTS: dict[str, str] = {
    "pentest": PENTEST_SYSTEM_PROMPT,
    "report": """\
You are an expert penetration testing report writer.
Produce concise, professional, structured findings and recommendations.
Do not invent vulnerabilities or evidence; only use details present in the prompt.
If information is missing, state assumptions and required validation steps explicitly.""",
    "recon": """\
You are an expert reconnaissance and OSINT analyst for security assessments.
Enumerate discovered signals, correlate related indicators, and prioritize likely attack paths.
Suggest clear next investigative steps and validation checks.
Do not speculate beyond the provided data; flag uncertainty explicitly.""",
    "default": PENTEST_SYSTEM_PROMPT,
}


def resolve_system_prompt(override: str | None) -> str:
    """Resolve a system prompt from a named preset or a raw override string."""
    if override is None:
        return PENTEST_SYSTEM_PROMPT

    preset = AVAILABLE_SYSTEM_PROMPTS.get(override)
    if preset is not None:
        return preset

    if len(override) > 2000:
        raise ValueError("system_prompt override exceeds 2000 characters")

    return override


class LLMResponse(BaseModel):
    """Structured response from an LLM provider."""

    content: str
    input_tokens: int
    output_tokens: int
    provider: str
    model: str


class AsyncLLMProvider(ABC):
    """Abstract base class for asynchronous LLM providers."""

    @abstractmethod
    async def send(self, prompt: str, system: str | None = None) -> LLMResponse:
        """Send a prompt and return the complete response."""
        ...

    @abstractmethod
    async def stream(self, prompt: str, system: str | None = None) -> AsyncIterator[str]:
        """Stream response chunks as they arrive from the provider."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable."""
        ...
