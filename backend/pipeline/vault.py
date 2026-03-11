"""SQLCipher-backed token vault for sensitive entity storage."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sqlcipher3  # type: ignore[import-untyped]


class Vault:
    """Encrypted vault mapping sensitive strings to opaque tokens.

    Each token is scoped to a session. The underlying database is
    encrypted using SQLCipher with the provided password.
    """

    def __init__(self, db_path: Path, password: str) -> None:
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlcipher3.connect(str(db_path))
        cur = self._conn.cursor()
        safe_password = password.replace("'", "''")
        cur.execute(f"PRAGMA key = '{safe_password}'")
        cur.execute("PRAGMA kdf_iter = 600000")
        cur.execute("PRAGMA cipher_page_size = 4096")
        self._create_tables()

    # ── schema ───────────────────────────────────────────────────

    def _create_tables(self) -> None:
        """Ensure the tokens table exists."""
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
            CREATE INDEX IF NOT EXISTS idx_tokens_session
            ON tokens (session_id)
        """)
        self._conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_tokens_original_session
            ON tokens (original, session_id)
        """)
        self._conn.commit()

    # ── public API ───────────────────────────────────────────────

    def store(self, original: str, entity_type: str, session_id: str) -> str:
        """Store a sensitive value and return its opaque token.

        Idempotent: the same (original, session_id) pair always returns the
        same token ID.
        """
        row = self._conn.execute(
            "SELECT token_id FROM tokens WHERE original = ? AND session_id = ? AND expired = 0",
            (original, session_id),
        ).fetchone()
        if row:
            return row[0]

        prefix = entity_type.replace("_", "")[:6].upper()
        token_id = f"{prefix}_{secrets.token_hex(4)}"
        now = datetime.now(timezone.utc).isoformat()

        self._conn.execute(
            "INSERT INTO tokens (token_id, original, entity_type, session_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (token_id, original, entity_type, session_id, now),
        )
        self._conn.commit()
        return token_id

    def resolve(self, token_id: str, session_id: str) -> str | None:
        """Resolve a token back to its original value, or None if expired/missing."""
        row = self._conn.execute(
            "SELECT original FROM tokens WHERE token_id = ? AND session_id = ? AND expired = 0",
            (token_id, session_id),
        ).fetchone()
        return row[0] if row else None

    def get_session_tokens(self, session_id: str) -> list[dict[str, Any]]:
        """Return all active tokens for a session."""
        rows = self._conn.execute(
            "SELECT token_id, entity_type, original, created_at FROM tokens WHERE session_id = ? AND expired = 0",
            (session_id,),
        ).fetchall()
        return [
            {
                "token_id": r[0],
                "entity_type": r[1],
                "original_value": r[2],
                "created_at": r[3],
            }
            for r in rows
        ]

    def expire_session(self, session_id: str) -> int:
        """Mark all tokens for a session as expired. Returns count of expired tokens."""
        cur = self._conn.execute(
            "UPDATE tokens SET expired = 1 WHERE session_id = ? AND expired = 0",
            (session_id,),
        )
        self._conn.commit()
        return cur.rowcount

    def close(self) -> None:
        """Close the database connection."""
        self._conn.close()
