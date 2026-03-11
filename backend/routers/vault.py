"""Vault inspection router."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["vault"])


class VaultTokenOut(BaseModel):
    """A single vault token."""
    token_id: str
    entity_type: str
    original_value: str
    created_at: str


class VaultResponse(BaseModel):
    """Response with all tokens for a session."""
    tokens: list[VaultTokenOut]


@router.get("/vault/{session_id}", response_model=VaultResponse)
async def get_vault_tokens(session_id: str, request: Request) -> VaultResponse:
    """Return all active vault tokens for the given session."""
    vault = request.app.state.vault
    rows = vault.get_session_tokens(session_id)
    return VaultResponse(
        tokens=[
            VaultTokenOut(
                token_id=r["token_id"],
                entity_type=r["entity_type"],
                original_value=r["original_value"],
                created_at=r["created_at"],
            )
            for r in rows
        ],
    )
