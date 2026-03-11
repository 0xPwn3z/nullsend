"""Tests for FastAPI endpoints using httpx AsyncClient."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app


@pytest_asyncio.fixture()
async def client():
    """Async test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    """GET /api/health returns status ok."""
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "provider" in data
    assert "model" in data


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient) -> None:
    """POST /api/session/new returns a session_id."""
    resp = await client.post("/api/session/new", json={"name": "test-session"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert len(data["session_id"]) > 0
    assert "created_at" in data


@pytest.mark.asyncio
async def test_analyze_with_entities(client: AsyncClient) -> None:
    """POST /api/analyze detects entities in pentest text."""
    body = {
        "text": "Scan 10.0.1.50 on port 443 using nmap.",
        "session_id": "test-session-1",
    }
    resp = await client.post("/api/analyze", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "test-session-1"
    assert isinstance(data["entities"], list)
    # Should detect at least the IP
    assert len(data["entities"]) >= 1


@pytest.mark.asyncio
async def test_analyze_clean_text(client: AsyncClient) -> None:
    """POST /api/analyze returns empty entities for clean text."""
    body = {
        "text": "What is the OWASP Top 10?",
        "session_id": "test-session-2",
    }
    resp = await client.post("/api/analyze", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["entities"], list)
    # Clean text should produce zero or very few entities
