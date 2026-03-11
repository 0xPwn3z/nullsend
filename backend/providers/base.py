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
