"""Anthropic native SDK provider."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

import anthropic
from anthropic import APIStatusError

from providers.base import AsyncLLMProvider, LLMResponse, PENTEST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_RETRYABLE_CODES = {429, 503, 529}
_MAX_RETRIES = 3


class AnthropicProvider(AsyncLLMProvider):
    """LLM provider using the native Anthropic async streaming API.

    Supports both one-shot and streaming completions with automatic
    retry on 429/503/529.
    """

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022") -> None:
        self._model = model
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    # ── helpers ──────────────────────────────────────────────────

    async def _retry(self, coro_factory):  # type: ignore[no-untyped-def]
        """Retry with exponential backoff on retryable HTTP codes."""
        for attempt in range(_MAX_RETRIES):
            try:
                return await coro_factory()
            except APIStatusError as exc:
                if exc.status_code in _RETRYABLE_CODES and attempt < _MAX_RETRIES - 1:
                    wait = 2 ** attempt
                    logger.warning("Anthropic returned %s, retrying in %ss", exc.status_code, wait)
                    await asyncio.sleep(wait)
                else:
                    raise

    # ── public API ───────────────────────────────────────────────

    async def send(self, prompt: str, system: str | None = None) -> LLMResponse:
        """Send a prompt and return the full response."""
        sys_text = system or PENTEST_SYSTEM_PROMPT

        response = await self._retry(
            lambda: self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=sys_text,
                messages=[{"role": "user", "content": prompt}],
            )
        )

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return LLMResponse(
            content=content,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            provider="anthropic",
            model=self._model,
        )

    async def stream(self, prompt: str, system: str | None = None) -> AsyncIterator[str]:
        """Stream response chunks using the Anthropic streaming API."""
        sys_text = system or PENTEST_SYSTEM_PROMPT

        async with self._client.messages.stream(
            model=self._model,
            max_tokens=4096,
            system=sys_text,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def health_check(self) -> bool:
        """Check if the Anthropic API is reachable."""
        try:
            await self._client.messages.create(
                model=self._model,
                max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            return True
        except Exception:
            return False
