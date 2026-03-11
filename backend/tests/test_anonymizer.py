"""Tests for the anonymizer (build_safe_text / restore_text)."""

import re
import sqlite3

import pytest

from pipeline.anonymizer import build_safe_text, restore_text, _TOKEN_PATTERN
from pipeline.ner import RecognizedEntity
from pipeline.vault import Vault


@pytest.fixture()
def vault() -> Vault:
    """In-memory vault for testing."""
    v = object.__new__(Vault)
    v._conn = sqlite3.connect(":memory:")
    v._conn.execute("""
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
    v._conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tokens_original_session
        ON tokens (original, session_id)
    """)
    v._conn.commit()
    return v


def _entity(original: str, entity_type: str, start: int, end: int, confidence: float = 0.9) -> RecognizedEntity:
    return RecognizedEntity(
        original=original,
        entity_type=entity_type,
        start=start,
        end=end,
        confidence=confidence,
    )


class TestBuildSafeText:
    """Tests for build_safe_text."""

    def test_replaces_all_entities(self, vault: Vault) -> None:
        text = "Scan 10.0.1.50 on port 443"
        entities = [
            _entity("10.0.1.50", "IP_ADDRESS", 5, 14),
            _entity("443", "PORT", 23, 26),
        ]
        safe, mappings = build_safe_text(text, entities, vault, "sess1")
        assert "10.0.1.50" not in safe
        assert "443" not in safe
        assert len(mappings) == 2

    def test_empty_entities(self, vault: Vault) -> None:
        text = "No sensitive data here."
        safe, mappings = build_safe_text(text, [], vault, "sess1")
        assert safe == text
        assert mappings == []


class TestRestoreText:
    """Tests for restore_text."""

    def test_restores_all_originals(self, vault: Vault) -> None:
        text = "Scan 10.0.1.50 on port 443"
        entities = [
            _entity("10.0.1.50", "IP_ADDRESS", 5, 14),
            _entity("443", "PORT", 23, 26),
        ]
        safe, _ = build_safe_text(text, entities, vault, "sess1")
        restored = restore_text(safe, vault, "sess1")
        assert "10.0.1.50" in restored
        assert "443" in restored


class TestRoundTrip:
    """Full anonymize → restore round-trip."""

    def test_round_trip(self, vault: Vault) -> None:
        text = "Check host 10.0.1.50 subnet 10.0.0.0/24 with creds admin:hunter2"
        entities = [
            _entity("10.0.1.50", "IP_ADDRESS", 11, 20),
            _entity("10.0.0.0/24", "NETWORK_RANGE", 28, 39),
            _entity("admin:hunter2", "CREDENTIAL", 51, 64),
        ]
        safe, mappings = build_safe_text(text, entities, vault, "sess1")

        # Look up mappings by original value (order depends on sort)
        by_original = {m.original: m for m in mappings}
        ip_token = by_original["10.0.1.50"].token_id
        net_token = by_original["10.0.0.0/24"].token_id

        # Simulate LLM echoing tokens back
        llm_response = f"Target [{ip_token}] is on [{net_token}]"
        restored = restore_text(llm_response, vault, "sess1")
        assert "10.0.1.50" in restored
        assert "10.0.0.0/24" in restored

    def test_longest_match_first(self, vault: Vault) -> None:
        """Ensure longer matches are replaced before shorter substrings."""
        text = "Found 10.0.1.50 and 10.0.1.5 on the network."
        entities = [
            _entity("10.0.1.50", "IP_ADDRESS", 6, 15),
            _entity("10.0.1.5", "IP_ADDRESS", 20, 28),
        ]
        safe, mappings = build_safe_text(text, entities, vault, "sess1")
        # Both should be independently tokenized
        assert "10.0.1.50" not in safe
        assert "10.0.1.5" not in safe
        assert len(mappings) == 2


# All entity_types from ner_config.yaml + any multi-word types
_ALL_ENTITY_TYPES = [
    "IP_ADDRESS",
    "NETWORK_RANGE",
    "CREDENTIAL",
    "PORT",
    "FILE_PATH",
    "PERSON",
    "ORG_NAME",
    "HOSTNAME",
    "INTERNAL_CODE",
]

# Representative sample values per entity type
_SAMPLE_VALUES: dict[str, str] = {
    "IP_ADDRESS": "192.168.1.100",
    "NETWORK_RANGE": "10.0.0.0/24",
    "CREDENTIAL": "admin:hunter2",
    "PORT": "8443",
    "FILE_PATH": "/etc/shadow",
    "PERSON": "Alice Smith",
    "ORG_NAME": "Acme Corp",
    "HOSTNAME": "dc01.internal.local",
    "INTERNAL_CODE": "PROJ-X-4492",
}


class TestTokenFormatPerEntityType:
    """Verify every entity type produces a token matched by the regex."""

    @pytest.mark.parametrize("entity_type", _ALL_ENTITY_TYPES)
    def test_token_matches_regex(self, vault: Vault, entity_type: str) -> None:
        value = _SAMPLE_VALUES[entity_type]
        token_id = vault.store(value, entity_type, "sess_fmt")
        bracketed = f"[{token_id}]"
        assert _TOKEN_PATTERN.fullmatch(bracketed) or _TOKEN_PATTERN.search(bracketed), (
            f"Token '{bracketed}' for entity_type '{entity_type}' not matched by _TOKEN_PATTERN"
        )

    @pytest.mark.parametrize("entity_type", _ALL_ENTITY_TYPES)
    def test_no_double_underscore(self, vault: Vault, entity_type: str) -> None:
        value = _SAMPLE_VALUES[entity_type]
        token_id = vault.store(value, entity_type, "sess_dbl")
        assert "__" not in token_id, (
            f"Token '{token_id}' for entity_type '{entity_type}' contains double underscore"
        )


class TestRoundTripAllEntityTypes:
    """Full store → wrap → restore round-trip for every entity type."""

    @pytest.mark.parametrize("entity_type", _ALL_ENTITY_TYPES)
    def test_round_trip_per_type(self, vault: Vault, entity_type: str) -> None:
        original_value = _SAMPLE_VALUES[entity_type]
        session_id = f"sess_rt_{entity_type}"

        # 1. Store in vault
        token_id = vault.store(original_value, entity_type, session_id)

        # 2. Wrap in brackets (simulating build_safe_text output)
        safe_text = f"prefix [{token_id}] suffix"

        # 3. Restore
        restored = restore_text(safe_text, vault, session_id)

        # 4. Assert original value recovered
        assert original_value in restored, (
            f"Round-trip failed for {entity_type}: "
            f"token_id='{token_id}', safe='{safe_text}', restored='{restored}'"
        )
        assert f"[{token_id}]" not in restored

    def test_round_trip_all_types_in_one_text(self, vault: Vault) -> None:
        """All entity types in a single text survive anonymize → restore."""
        session_id = "sess_all"
        parts: list[str] = []
        originals: list[str] = []

        for entity_type in _ALL_ENTITY_TYPES:
            value = _SAMPLE_VALUES[entity_type]
            token_id = vault.store(value, entity_type, session_id)
            parts.append(f"[{token_id}]")
            originals.append(value)

        safe_text = " | ".join(parts)
        restored = restore_text(safe_text, vault, session_id)

        for value in originals:
            assert value in restored, f"'{value}' not found in restored text"
