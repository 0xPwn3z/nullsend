"""Nullsend backend – FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Settings
from pipeline.ner import PentestNER
from pipeline.vault import Vault
from pipeline.audit import AuditLog
from providers import build_provider


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: initialize shared resources on startup, clean up on shutdown."""
    # FIX: session expiry — TTL enforcement + startup cleanup
    settings = Settings()

    ner = PentestNER()
    ner.load()
    vault = Vault(
        db_path=settings.vault_db_path,
        password=settings.vault_password,
        session_ttl_hours=settings.session_ttl_hours,
    )
    vault.cleanup_expired_sessions()
    audit = AuditLog(log_path=settings.audit_log_path)
    provider = build_provider(settings)

    app.state.settings = settings
    app.state.ner = ner
    app.state.vault = vault
    app.state.audit = audit
    app.state.provider = provider

    yield

    vault.close()


app = FastAPI(
    title="Nullsend",
    description="Privacy layer for LLM-assisted penetration testing",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS ------------------------------------------------------------------
_settings_for_cors = Settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings_for_cors.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers ---------------------------------------------------------------
from routers import session, analyze, send, vault, audit  # noqa: E402

app.include_router(session.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")
app.include_router(send.router, prefix="/api")
app.include_router(vault.router, prefix="/api")
app.include_router(audit.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    """Health-check endpoint reporting component status."""
    settings: Settings = app.state.settings
    vault_status = "ok"
    try:
        app.state.vault.get_session_tokens("__health__")
    except Exception:
        vault_status = "error"

    return {
        "status": "ok",
        "provider": settings.provider.name,
        "model": settings.provider.model,
        "vault": vault_status,
        "ner": app.state.ner.health()["mode"],
    }
