"""Provider package – factory function for building LLM providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from providers.base import AsyncLLMProvider, LLMResponse, PENTEST_SYSTEM_PROMPT  # noqa: F401
from providers.openai_compat import OpenAICompatProvider
from providers.anthropic import AnthropicProvider

if TYPE_CHECKING:
    from config import Settings


def build_provider(settings: "Settings") -> AsyncLLMProvider:
    """Instantiate the correct provider based on application settings."""
    name = settings.provider.name.lower()
    model = settings.provider.model
    api_key = settings.api_key

    if name == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model)

    return OpenAICompatProvider(
        provider_name=name,
        api_key=api_key,
        model=model,
        base_url=settings.provider.base_url,
    )
