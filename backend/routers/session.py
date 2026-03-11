"""Session management router."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["session"])


class NewSessionRequest(BaseModel):
    """Request body for creating a new session."""
    name: str


class NewSessionResponse(BaseModel):
    """Response body for a newly created session."""
    session_id: str
    created_at: str
    provider: str
    model: str


class DeleteSessionResponse(BaseModel):
    """Response body for session deletion."""
    expired_tokens: int


@router.post("/session/new", response_model=NewSessionResponse)
async def create_session(body: NewSessionRequest, request: Request) -> NewSessionResponse:
    """Create a new analysis session."""
    settings = request.app.state.settings
    session_id = uuid.uuid4().hex[:16]
    created_at = datetime.now(timezone.utc).isoformat()

    return NewSessionResponse(
        session_id=session_id,
        created_at=created_at,
        provider=settings.provider.name,
        model=settings.provider.model,
    )


@router.delete("/session/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str, request: Request) -> DeleteSessionResponse:
    """Delete a session and expire all its vault tokens."""
    vault = request.app.state.vault
    expired = vault.expire_session(session_id)
    return DeleteSessionResponse(expired_tokens=expired)
