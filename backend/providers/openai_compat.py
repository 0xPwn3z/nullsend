"""OpenAI-compatible LLM provider (Groq, OpenRouter, Ollama)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI, APIStatusError

from providers.base import AsyncLLMProvider, LLMResponse, PENTEST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

PROVIDER_CONFIGS: dict[str, dict[str, str]] = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.1-8b-instant",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "meta-llama/llama-3.1-8b-instruct:free",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "default_model": "qwen2.5:latest",
    },
}

_RETRYABLE_CODES = {429, 503}
_MAX_RETRIES = 3


class OpenAICompatProvider(AsyncLLMProvider):
    """LLM provider using the OpenAI-compatible API (Groq, OpenRouter, Ollama).

    Supports both one-shot and streaming completions with automatic
    retry on 429/503.
    """

    def __init__(self, provider_name: str, api_key: str, model: str | None = None, base_url: str | None = None) -> None:
        config = PROVIDER_CONFIGS.get(provider_name, {})
        self._provider_name = provider_name
        self._model = model or config.get("default_model", "")
        self._base_url = base_url or config.get("base_url", "")

        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=self._base_url,
        )

    # ── helpers ──────────────────────────────────────────────────

    def _build_messages(self, prompt: str, system: str | None) -> list[dict[str, str]]:
        """Build the messages array for chat completions."""
        messages: list[dict[str, str]] = []
        sys_text = system or PENTEST_SYSTEM_PROMPT
        messages.append({"role": "system", "content": sys_text})
        messages.append({"role": "user", "content": prompt})
        return messages

    async def _retry(self, coro_factory: Any) -> Any:
        """Retry coroutine on retryable HTTP status codes with exponential backoff."""
        for attempt in range(_MAX_RETRIES):
            try:
                return await coro_factory()
            except APIStatusError as exc:
                if exc.status_code in _RETRYABLE_CODES and attempt < _MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    logger.warning("Provider %s returned %s, retrying in %ss", self._provider_name, exc.status_code, wait)
                    await asyncio.sleep(wait)
                else:
                    raise

    # ── public API ───────────────────────────────────────────────

    async def send(self, prompt: str, system: str | None = None) -> LLMResponse:
        """Send a prompt and return the full response."""
        messages = self._build_messages(prompt, system)

        response = await self._retry(
            lambda: self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )
        )

        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            provider=self._provider_name,
            model=self._model,
        )

    async def stream(self, prompt: str, system: str | None = None) -> AsyncIterator[str]:
        """Stream response chunks using the OpenAI streaming API."""
        messages = self._build_messages(prompt, system)

        stream = await self._retry(
            lambda: self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                stream=True,
            )
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def health_check(self) -> bool:
        """Check provider reachability with a minimal request."""
        try:
            await self._client.models.list()
            return True
        except Exception:
            return False
