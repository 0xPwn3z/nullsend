"""
SecureRelay NER Pipeline — Hybrid Regex + GLiNER engine.

Architecture:
  1. RegexEngine  — deterministic, structured entities
  2. GLiNEREngine — zero-shot NER, linguistic entities, Italian-native
  3. MergeEngine  — overlap resolution, deduplication, sorting
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entity dataclass (unchanged public contract)
# ---------------------------------------------------------------------------

@dataclass
class RecognizedEntity:
    """A single recognized sensitive entity in text."""

    original:    str
    entity_type: str
    start:       int
    end:         int
    confidence:  float

    def overlaps(self, other: RecognizedEntity) -> bool:
        return self.start < other.end and other.start < self.end

    def contains(self, other: RecognizedEntity) -> bool:
        return self.start <= other.start and self.end >= other.end

    def span_length(self) -> int:
        return self.end - self.start


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

DEFAULT_CONFIG_PATH = Path(__file__).parent / "ner_config.yaml"


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load NER configuration from YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def _validate_ipv4(value: str) -> bool:
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(p) <= 255 for p in parts)
    except ValueError:
        return False


def _validate_port(value: str) -> bool:
    digits = re.search(r"\d+", value)
    if not digits:
        return False
    return 1 <= int(digits.group()) <= 65535


VALIDATORS: dict[str, Any] = {
    "ipv4": _validate_ipv4,
    "port": _validate_port,
}


# ---------------------------------------------------------------------------
# Regex Engine
# ---------------------------------------------------------------------------

class RegexEngine:
    """
    Deterministic regex-based entity detector.
    Reads pattern config from ner_config.yaml at init time.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._cfg: dict[str, Any] = config["regex"]
        self._global_threshold: float = self._cfg.get("global_threshold", 0.75)
        self._context_window: int = self._cfg.get("context_window", 60)
        self._compiled: list[dict[str, Any]] = []
        self._build_patterns()

    def _build_patterns(self) -> None:
        for p_cfg in self._cfg.get("patterns", []):
            compiled_patterns: list[re.Pattern[str]] = []
            for raw in p_cfg.get("patterns", []):
                # Remove inline comments and whitespace in pattern strings
                clean = re.sub(r"#[^\n]*", "", raw)
                clean = re.sub(r"\s+", "", clean)
                try:
                    compiled_patterns.append(re.compile(clean))
                except re.error as e:
                    logger.warning(
                        "RegexEngine: failed to compile pattern "
                        "for %s: %s", p_cfg["entity_type"], e,
                    )
            self._compiled.append({
                **p_cfg,
                "_compiled_patterns": compiled_patterns,
            })

    def analyze(self, text: str) -> list[RecognizedEntity]:
        """Run all regex patterns against text and return matches."""
        results: list[RecognizedEntity] = []

        for p_cfg in self._compiled:
            entity_type: str = p_cfg["entity_type"]
            base_score = float(p_cfg.get("score", self._global_threshold))
            validate_key: str | None = p_cfg.get("validate")
            deny_list: set[str] = set(p_cfg.get("deny_list", []))
            deny_regexes = [
                re.compile(r) for r in p_cfg.get("deny_list_regex", [])
            ]
            context_cfg: dict[str, Any] = p_cfg.get("context_boost", {})
            context_words = [
                w.lower() for w in context_cfg.get("words", [])
            ]
            context_boost = float(context_cfg.get("boost", 0.0))

            for pattern in p_cfg["_compiled_patterns"]:
                for m in pattern.finditer(text):
                    full_match = m.group(0)
                    start, end = m.start(), m.end()

                    # Use first capturing group if present, else full match
                    value = m.group(1) if m.lastindex else full_match

                    # deny_list check
                    if value in deny_list or full_match in deny_list:
                        continue

                    # deny_list_regex check
                    if any(dr.search(full_match) for dr in deny_regexes):
                        continue

                    # validator check
                    if validate_key:
                        validator = VALIDATORS.get(validate_key)
                        if validator and not validator(value):
                            continue

                    # context boost
                    score = base_score
                    if context_words:
                        ctx_start = max(0, start - self._context_window)
                        ctx_end = min(len(text), end + self._context_window)
                        context = text[ctx_start:ctx_end].lower()
                        if any(w in context for w in context_words):
                            score = min(1.0, score + context_boost)

                    results.append(RecognizedEntity(
                        original=full_match,
                        entity_type=entity_type,
                        start=start,
                        end=end,
                        confidence=round(score, 4),
                    ))

        return results


# ---------------------------------------------------------------------------
# GLiNER Engine
# ---------------------------------------------------------------------------

class GLiNEREngine:
    """
    Zero-shot NER using GLiNER multi-language PII model.
    Loads the model once at startup. Supports ONNX for CPU inference.
    Fully offline after Dockerfile build.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._cfg: dict[str, Any] = config["gliner"]
        self._model: Any = None  # GLiNER model instance (typed as Any — external lib)
        self._labels: list[str] = [
            item["label"] for item in self._cfg.get("labels", [])
        ]
        self._label_to_type: dict[str, str] = {
            item["label"]: item["entity_type"]
            for item in self._cfg.get("labels", [])
        }
        self._threshold: float = float(self._cfg.get("threshold", 0.4))
        self._max_length: int = int(self._cfg.get("max_length", 512))
        self._batch_size: int = int(self._cfg.get("batch_size", 8))
        self._use_onnx: bool = bool(self._cfg.get("use_onnx", False))
        self._model_id: str = self._cfg["model_id"]
        self._cache_dir: Path = Path(
            self._cfg.get("model_cache_dir", "/app/models")
        )

    def load(self) -> None:
        """
        Load GLiNER model. Called once in FastAPI lifespan startup.
        Sets HF_HOME to cache dir and local_files_only=True to
        guarantee offline operation after Dockerfile build.
        """
        from gliner import GLiNER  # type: ignore[import-untyped]

        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_DATASETS_OFFLINE"] = "1"

        cache_str = str(self._cache_dir)
        os.environ.setdefault("HF_HOME", cache_str)
        os.environ.setdefault("HUGGINGFACE_HUB_CACHE", cache_str)

        t0 = time.perf_counter()
        try:
            self._model = GLiNER.from_pretrained(
                self._model_id,
                cache_dir=cache_str,
                local_files_only=True,
            )
            elapsed = time.perf_counter() - t0
            logger.info(
                "GLiNEREngine: loaded '%s' (ONNX=%s) in %.2fs",
                self._model_id, self._use_onnx, elapsed,
            )
        except Exception:
            logger.exception(
                "GLiNEREngine: failed to load model. "
                "NER will run regex-only."
            )
            self._model = None

    @property
    def available(self) -> bool:
        """Return True if the GLiNER model loaded successfully."""
        return self._model is not None

    def analyze(self, text: str) -> list[RecognizedEntity]:
        """Run GLiNER inference on text and return recognized entities."""
        if not self.available or not self._labels:
            return []

        chunks = self._chunk_text(text)
        results: list[RecognizedEntity] = []

        for chunk, chunk_start in chunks:
            try:
                raw = self._model.predict_entities(
                    chunk,
                    self._labels,
                    threshold=self._threshold,
                    batch_size=self._batch_size,
                )
            except Exception:
                logger.warning(
                    "GLiNEREngine: inference error on chunk",
                    exc_info=True,
                )
                continue

            for ent in raw:
                entity_type = self._label_to_type.get(
                    ent["label"], ent["label"].upper().replace(" ", "_")
                )
                start = chunk_start + ent["start"]
                end = chunk_start + ent["end"]
                original = text[start:end]

                if len(original.strip()) < 2:
                    continue

                results.append(RecognizedEntity(
                    original=original,
                    entity_type=entity_type,
                    start=start,
                    end=end,
                    confidence=round(float(ent["score"]), 4),
                ))

        return results

    def _chunk_text(self, text: str) -> list[tuple[str, int]]:
        """
        Split text into chunks of approximately max_length characters,
        breaking at sentence/newline boundaries.
        Returns list of (chunk_text, start_offset_in_original).
        """
        max_chars = self._max_length * 4  # rough char estimate
        if len(text) <= max_chars:
            return [(text, 0)]

        chunks: list[tuple[str, int]] = []
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            if end < len(text):
                for sep in ["\n", ". ", "! ", "? "]:
                    idx = text.rfind(sep, start, end)
                    if idx > start:
                        end = idx + len(sep)
                        break
            chunks.append((text[start:end], start))
            start = end

        return chunks


# ---------------------------------------------------------------------------
# Merge Engine
# ---------------------------------------------------------------------------

class MergeEngine:
    """
    Merges results from RegexEngine and GLiNEREngine.
    Resolves overlaps, removes duplicates, sorts by start.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._cfg: dict[str, Any] = config.get("merge", {})
        self._overlap_strategy: str = self._cfg.get(
            "overlap_strategy", "highest_confidence"
        )
        self._min_span_length: int = int(
            self._cfg.get("min_span_length", 2)
        )
        self._regex_priority_types: set[str] = set(
            self._cfg.get("regex_priority_types", [])
        )

    def merge(
        self,
        regex_entities: list[RecognizedEntity],
        gliner_entities: list[RecognizedEntity],
    ) -> list[RecognizedEntity]:
        """Merge regex and GLiNER results with overlap resolution."""

        # Tag source for priority logic
        combined: list[tuple[RecognizedEntity, str]] = (
            [(e, "regex") for e in regex_entities]
            + [(e, "gliner") for e in gliner_entities]
        )

        # Remove spans that are too short
        combined = [
            (e, s) for e, s in combined
            if e.span_length() >= self._min_span_length
        ]

        # Sort: regex-priority types first, then by confidence desc
        combined.sort(
            key=lambda x: (
                0 if (
                    x[1] == "regex"
                    and x[0].entity_type in self._regex_priority_types
                ) else 1,
                -x[0].confidence,
                x[0].start,
            )
        )

        resolved: list[RecognizedEntity] = []

        for entity, source in combined:
            overlapping = [
                r for r in resolved if entity.overlaps(r)
            ]

            if not overlapping:
                resolved.append(entity)
                continue

            if self._overlap_strategy == "highest_confidence":
                max_existing = max(r.confidence for r in overlapping)

                # Regex priority: always keep regex for its entity types
                if (
                    source == "regex"
                    and entity.entity_type in self._regex_priority_types
                ):
                    for r in overlapping:
                        if r in resolved:
                            resolved.remove(r)
                    resolved.append(entity)
                elif entity.confidence > max_existing:
                    for r in overlapping:
                        if r in resolved:
                            resolved.remove(r)
                    resolved.append(entity)
                # else: keep existing, discard new

        # Final sort by start position
        resolved.sort(key=lambda e: e.start)

        # Deduplication: same start+end+type → keep highest confidence
        seen: dict[tuple[int, int, str], RecognizedEntity] = {}
        for e in resolved:
            key = (e.start, e.end, e.entity_type)
            if key not in seen or e.confidence > seen[key].confidence:
                seen[key] = e

        return list(seen.values())


# ---------------------------------------------------------------------------
# PentestNER — public interface (unchanged)
# ---------------------------------------------------------------------------

class PentestNER:
    """
    Main NER interface. Instantiate once at application startup.
    Thread-safe for concurrent analyze() calls after load().
    """

    def __init__(
        self,
        config_path: Path = DEFAULT_CONFIG_PATH,
    ) -> None:
        self._config = load_config(config_path)
        self._regex = RegexEngine(self._config)
        self._gliner = GLiNEREngine(self._config)
        self._merge = MergeEngine(self._config)
        self._loaded = False

    def load(self) -> None:
        """
        Load GLiNER model. Must be called once before analyze().
        Called from FastAPI lifespan startup handler.
        Logs degraded mode if GLiNER fails to load.
        """
        self._gliner.load()
        self._loaded = True
        mode = "Regex+GLiNER" if self._gliner.available else "Regex-only"
        logger.info("PentestNER initialized in %s mode", mode)

    def analyze(self, text: str) -> list[RecognizedEntity]:
        """
        Analyze text and return recognized entities.
        If GLiNER failed to load, runs regex-only (degraded mode).
        Never raises — returns empty list on unexpected error.
        """
        if not self._loaded:
            logger.warning(
                "PentestNER.analyze() called before load(). "
                "Calling load() now."
            )
            self.load()

        try:
            t0 = time.perf_counter()

            regex_results = self._regex.analyze(text)

            gliner_results = (
                self._gliner.analyze(text)
                if self._gliner.available else []
            )

            merged = self._merge.merge(regex_results, gliner_results)

            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.debug(
                "PentestNER.analyze(): %d entities "
                "(regex=%d, gliner=%d) in %.1fms",
                len(merged), len(regex_results),
                len(gliner_results), elapsed_ms,
            )

            return merged

        except Exception:
            logger.exception("PentestNER.analyze() unexpected error")
            return []

    @property
    def gliner_available(self) -> bool:
        """Return True if GLiNER model is loaded and available."""
        return self._gliner.available

    def health(self) -> dict[str, str]:
        """Return health status dict for the NER pipeline."""
        return {
            "regex": "ok",
            "gliner": "ok" if self._gliner.available else "degraded",
            "mode": (
                "regex+gliner" if self._gliner.available
                else "regex-only"
            ),
        }
