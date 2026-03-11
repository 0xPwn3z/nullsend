"""Append-only JSONL audit log for anonymized LLM interactions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLog:
    """Thread-safe, append-only JSONL audit log.

    Each entry records metadata about an anonymized prompt/response
    exchange – including entity counts, HITL adjustments, token usage,
    and a SHA-256 hash of the anonymized prompt (never the original).
    """

    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_query(
        self,
        session_id: str,
        entity_count: int,
        entity_types: list[str],
        provider: str,
        model: str,
        hitl_entities_added: int,
        hitl_entities_removed: int,
        input_tokens: int,
        output_tokens: int,
        prompt_hash: str,
    ) -> None:
        """Append a single audit entry to the JSONL file."""
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "entity_count": entity_count,
            "entity_types": entity_types,
            "provider": provider,
            "model": model,
            "hitl_entities_added": hitl_entities_added,
            "hitl_entities_removed": hitl_entities_removed,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "prompt_hash": prompt_hash,
        }
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def export_session(self, session_id: str) -> list[dict[str, Any]]:
        """Return all audit entries for a given session."""
        entries: list[dict[str, Any]] = []
        if not self._log_path.exists():
            return entries
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if entry.get("session_id") == session_id:
                    entries.append(entry)
        return entries
