"""Audit log export router."""

from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import Response

router = APIRouter(tags=["audit"])


@router.get("/audit/{session_id}/export")
async def export_audit(session_id: str, request: Request) -> Response:
    """Export audit log entries for a session as a JSONL file attachment."""
    audit = request.app.state.audit
    entries = audit.export_session(session_id)
    content = "\n".join(json.dumps(e, ensure_ascii=False) for e in entries)
    if content:
        content += "\n"
    return Response(
        content=content,
        media_type="application/jsonl",
        headers={
            "Content-Disposition": f'attachment; filename="audit_{session_id}.jsonl"',
        },
    )
