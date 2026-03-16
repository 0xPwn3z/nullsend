"""Send router – anonymize, stream LLM response via SSE, de-anonymize."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator

from pipeline.anonymizer import _RESIDUAL_TOKEN_PATTERN, build_safe_text, restore_text
from pipeline.ner import RecognizedEntity
from providers.base import resolve_system_prompt

logger = logging.getLogger(__name__)

router = APIRouter(tags=["send"])


class ApprovedEntity(BaseModel):
    """Entity approved by the analyst during HITL review."""
    original: str
    entity_type: str
    confidence: float


class SendRequest(BaseModel):
    """Request body for the send endpoint."""
    session_id: str
    original_text: str
    approved_entities: list[ApprovedEntity]
    # FIX: configurable system prompt — preset resolution
    system_prompt: str | None = None

    @field_validator("system_prompt", mode="before")
    @classmethod
    def normalize_system_prompt(cls, value: str | None) -> str | None:
        """Normalize optional system prompt input from clients."""
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


def _sse_event(event: str, data: dict | str) -> str:
    """Format a server-sent event."""
    payload = json.dumps(data) if isinstance(data, dict) else data
    return f"event: {event}\ndata: {payload}\n\n"


async def _stream_response(request: Request, body: SendRequest) -> AsyncIterator[str]:
    """Core SSE generator: anonymize → stream LLM → de-anonymize → audit."""
    vault = request.app.state.vault
    provider = request.app.state.provider
    settings = request.app.state.settings
    audit = request.app.state.audit

    # Convert approved entities to RecognizedEntity instances
    entities = [
        RecognizedEntity(
            original=e.original,
            entity_type=e.entity_type,
            start=0,
            end=len(e.original),
            confidence=e.confidence,
        )
        for e in body.approved_entities
    ]

    # Anonymize
    safe_text, mappings = build_safe_text(
        body.original_text, entities, vault, body.session_id,
    )

    prompt_hash = hashlib.sha256(safe_text.encode()).hexdigest()

    # Stream from provider
    full_response = ""
    input_tokens = 0
    output_tokens = 0

    try:
        # FIX: configurable system prompt — preset resolution
        system = resolve_system_prompt(body.system_prompt)
        async for chunk in provider.stream(safe_text, system=system):
            full_response += chunk
            yield _sse_event("token", {"chunk": chunk})

        # FIX: safety — no silent fallback on restore failure
        # De-anonymize the full response
        try:
            restored = restore_text(full_response, vault, body.session_id)
        except Exception as exc:
            logger.exception("restore_text failed, aborting done event for safety")
            yield _sse_event("error", {
                "message": "Unable to safely restore anonymized response; response withheld.",
                "safety": True,
            })
            return

        unresolved_tokens = _RESIDUAL_TOKEN_PATTERN.findall(restored)
        if unresolved_tokens:
            logger.warning(
                "restore_text completed with unresolved tokens: session=%s count=%s",
                body.session_id,
                len(unresolved_tokens),
            )
            yield _sse_event("warning", {
                "message": "Response contains unresolved anonymization tokens; verify vault/session mappings.",
                "unresolved_tokens": unresolved_tokens,
            })

        # Estimate token counts from the full (non-streaming) response
        # For accurate counts, we'd need the provider to report them;
        # streaming APIs don't always include usage. Rough estimate:
        input_tokens = len(safe_text.split())
        output_tokens = len(full_response.split())

        yield _sse_event("done", {
            "restored_response": restored,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "safe_text": safe_text,
        })

        # Audit log
        detected_count = len(body.approved_entities)
        entity_types = list({e.entity_type for e in body.approved_entities})
        hitl_added = sum(1 for e in body.approved_entities if e.confidence >= 1.0)
        hitl_removed = 0  # Removals happen client-side before this endpoint

        audit.log_query(
            session_id=body.session_id,
            entity_count=detected_count,
            entity_types=entity_types,
            provider=settings.provider.name,
            model=settings.provider.model,
            hitl_entities_added=hitl_added,
            hitl_entities_removed=hitl_removed,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            prompt_hash=prompt_hash,
        )

    except Exception as exc:
        logger.exception("Error during LLM streaming")
        yield _sse_event("error", {"message": str(exc)})


@router.post("/send")
async def send_prompt(body: SendRequest, request: Request) -> StreamingResponse:
    """Anonymize prompt, stream LLM response via SSE, and de-anonymize.

    SSE events:
    - ``token``: ``{"chunk": "..."}`` — a text chunk from the LLM
    - ``done``: ``{"restored_response": "...", ...}`` — final de-anonymized response
    - ``error``: ``{"message": "..."}`` — error description
    """
    return StreamingResponse(
        _stream_response(request, body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
