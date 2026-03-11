"""Analyze router – NER entity detection (pre-HITL)."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["analyze"])


class AnalyzeRequest(BaseModel):
    """Request body for text analysis."""
    text: str
    session_id: str


class EntityResult(BaseModel):
    """A single detected entity."""
    original: str
    entity_type: str
    start: int
    end: int
    confidence: float


class AnalyzeResponse(BaseModel):
    """Response body for text analysis."""
    session_id: str
    original_text: str
    entities: list[EntityResult]


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(body: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    """Run NER on the provided text and return detected entities.

    This endpoint does NOT anonymize — it only detects entities.
    The analyst reviews them (HITL) before the /send endpoint
    performs actual anonymization.
    """
    ner = request.app.state.ner
    entities = ner.analyze(body.text)

    return AnalyzeResponse(
        session_id=body.session_id,
        original_text=body.text,
        entities=[
            EntityResult(
                original=e.original,
                entity_type=e.entity_type,
                start=e.start,
                end=e.end,
                confidence=e.confidence,
            )
            for e in entities
        ],
    )
