"""Session management router."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel, field_validator

from providers.base import resolve_system_prompt

router = APIRouter(tags=["session"])


class NewSessionRequest(BaseModel):
    """Request body for creating a new session."""
    name: str
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


class NewSessionResponse(BaseModel):
    """Response body for a newly created session."""
    session_id: str
    created_at: str
    provider: str
    model: str
    # FIX: configurable system prompt — preset resolution
    system_prompt: str | None


class DeleteSessionResponse(BaseModel):
    """Response body for session deletion."""
    expired_tokens: int


@router.post("/session/new", response_model=NewSessionResponse)
async def create_session(body: NewSessionRequest, request: Request) -> NewSessionResponse:
    """Create a new analysis session."""
    settings = request.app.state.settings
    session_id = uuid.uuid4().hex[:16]
    created_at = datetime.now(timezone.utc).isoformat()

    # FIX: configurable system prompt — preset resolution
    resolve_system_prompt(body.system_prompt)

    return NewSessionResponse(
        session_id=session_id,
        created_at=created_at,
        provider=settings.provider.name,
        model=settings.provider.model,
        system_prompt=body.system_prompt,
    )


@router.delete("/session/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str, request: Request) -> DeleteSessionResponse:
    """Delete a session and expire all its vault tokens."""
    vault = request.app.state.vault
    expired = vault.expire_session(session_id)
    return DeleteSessionResponse(expired_tokens=expired)
