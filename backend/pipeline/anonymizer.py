"""Text anonymization and de-anonymization using vault tokens."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from pipeline.ner import RecognizedEntity
from pipeline.vault import Vault

logger = logging.getLogger(__name__)


@dataclass
class EntityMapping:
    """Mapping between an original value and its vault token."""

    original: str
    token_id: str
    entity_type: str
    confidence: float


def build_safe_text(
    original_text: str,
    entities: list[RecognizedEntity],
    vault: Vault,
    session_id: str,
) -> tuple[str, list[EntityMapping]]:
    """Replace all recognized entities with vault tokens.

    Entities are sorted by span length descending so that the longest
    match is replaced first, preventing partial-replacement bugs.

    Returns:
        A tuple of (safe_text, mapping_list).
    """
    if not entities:
        return original_text, []

    # Sort by span length descending, then by start position descending
    # (so replacements from right-to-left don't shift earlier offsets)
    sorted_entities = sorted(
        entities,
        key=lambda e: (-(e.end - e.start), -e.start),
    )

    # Deduplicate by original text (keep first = longest/highest conf)
    seen_originals: set[str] = set()
    unique_entities: list[RecognizedEntity] = []
    for ent in sorted_entities:
        if ent.original not in seen_originals:
            seen_originals.add(ent.original)
            unique_entities.append(ent)

    mappings: list[EntityMapping] = []
    safe = original_text

    # Replace right-to-left by start position to preserve offsets
    for ent in sorted(unique_entities, key=lambda e: -e.start):
        token_id = vault.store(ent.original, ent.entity_type, session_id)
        token_placeholder = f"[{token_id}]"
        # Replace all occurrences of this original value
        safe = safe.replace(ent.original, token_placeholder)
        mappings.append(EntityMapping(
            original=ent.original,
            token_id=token_id,
            entity_type=ent.entity_type,
            confidence=ent.confidence,
        ))

    return safe, mappings


# FIX: safety — no silent fallback on restore failure
# Regex to find token placeholders: [TYPE_XXXXXXXX]
# TYPE is an uppercase prefix (new format: no underscores, e.g. IPADDR, ORGNAM)
# followed by _ and 8 hex chars.
# Also matches legacy prefixes that may contain underscores (e.g. IP_A, ORG_).
_RESIDUAL_TOKEN_PATTERN = re.compile(r"\[([A-Z][A-Z_]{0,9}_[0-9a-f]{8})\]")
_TOKEN_PATTERN = _RESIDUAL_TOKEN_PATTERN


def restore_text(
    anonymized_response: str,
    vault: Vault,
    session_id: str,
) -> str:
    """Replace all vault token placeholders with their original values.

    Tokens that cannot be resolved (expired or missing) are left as-is.
    """
    matches = _TOKEN_PATTERN.findall(anonymized_response)
    logger.debug(
        "restore_text: session=%s, tokens_found=%s, response_preview=%.200s",
        session_id, matches, anonymized_response,
    )

    def _replacer(match: re.Match[str]) -> str:
        token_id = match.group(1)
        original = vault.resolve(token_id, session_id)
        if original is None:
            logger.warning(
                "restore_text: token '%s' not found for session '%s'",
                token_id, session_id,
            )
            return match.group(0)
        logger.debug("restore_text: resolved '%s' → '%.40s'", token_id, original)
        return original

    return _TOKEN_PATTERN.sub(_replacer, anonymized_response)
