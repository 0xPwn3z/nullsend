"""Tests for the SQLCipher vault."""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from pipeline.vault import Vault


def _make_vault(tmp_path: Path) -> Vault:
    """Create a Vault backed by a plain SQLite database (no SQLCipher) for tests."""
    # For tests we use a simple SQLite wrapper that ignores PRAGMA key.
    db_path = tmp_path / "test_vault.db"
    return Vault.__new__(Vault), db_path


class _TestVault:
    """In-memory SQLite vault for testing (avoids SQLCipher dependency)."""

    def __init__(self) -> None:
        self._conn = sqlite3.connect(":memory:")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                token_id     TEXT NOT NULL,
                original     TEXT NOT NULL,
                entity_type  TEXT NOT NULL,
                session_id   TEXT NOT NULL,
                created_at   TEXT NOT NULL,
                expired      INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY  (token_id, session_id)
            )
        """)
        self._conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_tokens_original_session
            ON tokens (original, session_id)
        """)
        self._conn.commit()

    # Delegate to the real Vault methods by patching _conn
    def _patch(self) -> "Vault":
        """Return a Vault-like object backed by in-memory SQLite."""
        v = object.__new__(Vault)
        v._conn = self._conn  # type: ignore[attr-defined]
        return v


@pytest.fixture()
def vault() -> Vault:
    """In-memory vault for testing."""
    return _TestVault()._patch()


class TestStoreResolve:
    """Store and resolve round-trip."""

    def test_round_trip(self, vault: Vault) -> None:
        token = vault.store("10.0.1.50", "IP_ADDRESS", "sess1")
        assert token.startswith("IPADDR")
        resolved = vault.resolve(token, "sess1")
        assert resolved == "10.0.1.50"

    def test_idempotency(self, vault: Vault) -> None:
        t1 = vault.store("admin:hunter2", "CREDENTIAL", "sess1")
        t2 = vault.store("admin:hunter2", "CREDENTIAL", "sess1")
        assert t1 == t2

    def test_session_scoping(self, vault: Vault) -> None:
        t1 = vault.store("10.0.1.50", "IP_ADDRESS", "sess1")
        t2 = vault.store("10.0.1.50", "IP_ADDRESS", "sess2")
        # Different sessions get different tokens
        assert t1 != t2

    def test_resolve_wrong_session(self, vault: Vault) -> None:
        token = vault.store("10.0.1.50", "IP_ADDRESS", "sess1")
        assert vault.resolve(token, "sess2") is None


class TestExpire:
    """Session expiration."""

    def test_expire_session(self, vault: Vault) -> None:
        vault.store("10.0.1.50", "IP_ADDRESS", "sess1")
        vault.store("admin:password", "CREDENTIAL", "sess1")
        expired = vault.expire_session("sess1")
        assert expired == 2

    def test_resolve_after_expire(self, vault: Vault) -> None:
        token = vault.store("10.0.1.50", "IP_ADDRESS", "sess1")
        vault.expire_session("sess1")
        assert vault.resolve(token, "sess1") is None

    def test_get_session_tokens(self, vault: Vault) -> None:
        vault.store("10.0.1.50", "IP_ADDRESS", "sess1")
        vault.store("admin:password", "CREDENTIAL", "sess1")
        tokens = vault.get_session_tokens("sess1")
        assert len(tokens) == 2
