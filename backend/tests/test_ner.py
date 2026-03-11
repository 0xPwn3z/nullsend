"""Tests for the hybrid Regex + GLiNER NER pipeline."""

from __future__ import annotations

import pytest

from pipeline.ner import (
    GLiNEREngine,
    MergeEngine,
    PentestNER,
    RecognizedEntity,
    RegexEngine,
    load_config,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def config() -> dict:
    """Shared NER config loaded from ner_config.yaml."""
    return load_config()


@pytest.fixture(scope="module")
def regex_engine(config: dict) -> RegexEngine:
    return RegexEngine(config)


@pytest.fixture(scope="module")
def merge_engine(config: dict) -> MergeEngine:
    return MergeEngine(config)


@pytest.fixture(scope="module")
def ner() -> PentestNER:
    """Full pipeline instance (GLiNER may or may not be available)."""
    n = PentestNER()
    n.load()
    return n


# ===================================================================
# RegexEngine tests
# ===================================================================

class TestRegexIPv4:
    """IPv4 address detection."""

    def test_ipv4_detection(self, regex_engine: RegexEngine) -> None:
        text = "target is 192.168.1.1 on the internal network"
        entities = regex_engine.analyze(text)
        ips = [e for e in entities if e.entity_type == "IP_ADDRESS"]
        assert any(e.original == "192.168.1.1" for e in ips)

    def test_ipv4_deny_list(self, regex_engine: RegexEngine) -> None:
        text = "listening on 0.0.0.0 and broadcast 255.255.255.255"
        entities = regex_engine.analyze(text)
        ips = [e for e in entities if e.entity_type == "IP_ADDRESS"]
        originals = {e.original for e in ips}
        assert "0.0.0.0" not in originals
        assert "255.255.255.255" not in originals

    def test_ipv4_no_false_positive_on_version_string(
        self, regex_engine: RegexEngine
    ) -> None:
        # Version strings like "3.11.0" should not have 4 octets → no match
        text = "Python 3.11.0 is installed"
        entities = regex_engine.analyze(text)
        ips = [e for e in entities if e.entity_type == "IP_ADDRESS"]
        assert not ips


class TestRegexIPv6:
    """IPv6 address detection."""

    def test_ipv6_detection(self, regex_engine: RegexEngine) -> None:
        text = "addr is 2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        entities = regex_engine.analyze(text)
        ips = [e for e in entities if e.entity_type == "IP_ADDRESS"]
        assert len(ips) >= 1

    def test_ipv6_abbreviated(self, regex_engine: RegexEngine) -> None:
        text = "addr is ::1234:5678"
        entities = regex_engine.analyze(text)
        ips = [e for e in entities if e.entity_type == "IP_ADDRESS"]
        assert len(ips) >= 1


class TestRegexCIDR:
    """CIDR / network range detection."""

    def test_cidr_detection(self, regex_engine: RegexEngine) -> None:
        text = "subnet 10.0.0.0/24 is in scope"
        entities = regex_engine.analyze(text)
        ranges = [e for e in entities if e.entity_type == "NETWORK_RANGE"]
        assert any("10.0.0.0/24" in e.original for e in ranges)


class TestRegexCredential:
    """Credential detection."""

    def test_credential_kv(self, regex_engine: RegexEngine) -> None:
        text = "Found password=Meri2024!Admin# in the config"
        entities = regex_engine.analyze(text)
        creds = [e for e in entities if e.entity_type == "CREDENTIAL"]
        assert len(creds) >= 1

    def test_credential_userpass(self, regex_engine: RegexEngine) -> None:
        text = "try auth admin:Passw0rd on the portal"
        entities = regex_engine.analyze(text)
        creds = [e for e in entities if e.entity_type == "CREDENTIAL"]
        assert len(creds) >= 1

    def test_jwt_detection(self, regex_engine: RegexEngine) -> None:
        text = (
            "token eyJhbGciOiJIUzI1NiJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkw."
            "SflKxwRJSMeKKF2QT4fwpM"
        )
        entities = regex_engine.analyze(text)
        creds = [e for e in entities if e.entity_type == "CREDENTIAL"]
        assert len(creds) >= 1

    def test_ssh_key_header(self, regex_engine: RegexEngine) -> None:
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIICXAIBAAJB"
        entities = regex_engine.analyze(text)
        creds = [e for e in entities if e.entity_type == "CREDENTIAL"]
        assert len(creds) >= 1

    def test_no_false_positive_url(self, regex_engine: RegexEngine) -> None:
        text = "visit https://example.com for docs"
        entities = regex_engine.analyze(text)
        creds = [e for e in entities if e.entity_type == "CREDENTIAL"]
        # URL should NOT match as a credential
        assert not any("https://example.com" in e.original for e in creds)


class TestRegexPort:
    """Port detection."""

    def test_port_with_context(self, regex_engine: RegexEngine) -> None:
        text = "port 443 open on target"
        entities = regex_engine.analyze(text)
        ports = [e for e in entities if e.entity_type == "PORT"]
        assert len(ports) >= 1

    def test_port_colon_notation(self, regex_engine: RegexEngine) -> None:
        text = "service on :8080/tcp is running"
        entities = regex_engine.analyze(text)
        ports = [e for e in entities if e.entity_type == "PORT"]
        assert len(ports) >= 1

    def test_port_validation(self, regex_engine: RegexEngine) -> None:
        text = "port 99999 unreachable"
        entities = regex_engine.analyze(text)
        ports = [e for e in entities if e.entity_type == "PORT"]
        assert not ports


class TestRegexFilePath:
    """File path detection."""

    def test_filepath_unix(self, regex_engine: RegexEngine) -> None:
        text = "check the config at /etc/passwd for users"
        entities = regex_engine.analyze(text)
        paths = [e for e in entities if e.entity_type == "FILE_PATH"]
        assert any("/etc/passwd" in e.original for e in paths)

    def test_filepath_windows(self, regex_engine: RegexEngine) -> None:
        text = r"the log is at C:\Users\admin\file.txt on the target"
        entities = regex_engine.analyze(text)
        paths = [e for e in entities if e.entity_type == "FILE_PATH"]
        assert len(paths) >= 1

    def test_filepath_must_be_deep(self, regex_engine: RegexEngine) -> None:
        # The non-system pattern requires at least 3 levels
        text = "check /randomdir alone"
        entities = regex_engine.analyze(text)
        paths = [e for e in entities if e.entity_type == "FILE_PATH"]
        assert not any(e.original.strip() == "/randomdir" for e in paths)


class TestRegexHash:
    """Hash detection."""

    def test_hash_md5(self, regex_engine: RegexEngine) -> None:
        text = "hash: 5d41402abc4b2a76b9719d911017c592"
        entities = regex_engine.analyze(text)
        hashes = [e for e in entities if e.entity_type == "HASH"]
        assert len(hashes) >= 1

    def test_hash_sha256(self, regex_engine: RegexEngine) -> None:
        text = (
            "sha256 digest "
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )
        entities = regex_engine.analyze(text)
        hashes = [e for e in entities if e.entity_type == "HASH"]
        assert len(hashes) >= 1


class TestRegexInternalCode:
    """Internal code / ticket detection."""

    def test_internal_code_cve(self, regex_engine: RegexEngine) -> None:
        text = "exploiting CVE-2024-1234 on the target"
        entities = regex_engine.analyze(text)
        codes = [e for e in entities if e.entity_type == "INTERNAL_CODE"]
        assert any("CVE-2024-1234" in e.original for e in codes)

    def test_internal_code_ticket(self, regex_engine: RegexEngine) -> None:
        text = "reference ticket INC-4892 for this finding"
        entities = regex_engine.analyze(text)
        codes = [e for e in entities if e.entity_type == "INTERNAL_CODE"]
        assert any("INC-4892" in e.original for e in codes)


class TestRegexContextBoost:
    """Context-based score boosting."""

    def test_context_boost_applied(self, regex_engine: RegexEngine) -> None:
        text_with_ctx = "the server hash is 5d41402abc4b2a76b9719d911017c592"
        text_no_ctx = "value 5d41402abc4b2a76b9719d911017c592 here"
        ents_with = regex_engine.analyze(text_with_ctx)
        ents_no = regex_engine.analyze(text_no_ctx)
        hashes_with = [e for e in ents_with if e.entity_type == "HASH"]
        hashes_no = [e for e in ents_no if e.entity_type == "HASH"]
        assert hashes_with and hashes_no
        # With context word "hash" → score should be boosted
        assert hashes_with[0].confidence >= hashes_no[0].confidence


class TestRegexOverlap:
    """Regex overlapping same type produces entries for merge."""

    def test_overlapping_same_type(self, regex_engine: RegexEngine) -> None:
        # A CIDR like 10.0.0.0/24 may also match as IP_ADDRESS (the prefix)
        text = "scan 10.0.0.0/24"
        entities = regex_engine.analyze(text)
        # Should have at least NETWORK_RANGE for the full CIDR
        ranges = [e for e in entities if e.entity_type == "NETWORK_RANGE"]
        assert len(ranges) >= 1


# ===================================================================
# GLiNER Engine tests (skipped if model not available)
# ===================================================================

class TestGLiNER:
    """GLiNER inference tests — skipped if model not loaded."""

    def test_gliner_person_italian(self, ner: PentestNER) -> None:
        if not ner.gliner_available:
            pytest.skip("GLiNER model not loaded in test environment")
        text = "Contattare Mario Rossi per i dettagli"
        entities = ner.analyze(text)
        persons = [e for e in entities if e.entity_type == "PERSON"]
        assert any("Mario" in e.original for e in persons)

    def test_gliner_org_italian(self, ner: PentestNER) -> None:
        if not ner.gliner_available:
            pytest.skip("GLiNER model not loaded in test environment")
        text = "Il pentest per Meridian Logistics S.r.l. è confermato"
        entities = ner.analyze(text)
        orgs = [e for e in entities if e.entity_type == "ORG_NAME"]
        assert any("Meridian" in e.original for e in orgs)

    def test_gliner_hostname(self, ner: PentestNER) -> None:
        if not ner.gliner_available:
            pytest.skip("GLiNER model not loaded in test environment")
        text = "access admin.internal.corp via SSH"
        entities = ner.analyze(text)
        hosts = [e for e in entities if e.entity_type == "HOSTNAME"]
        assert any("admin.internal.corp" in e.original for e in hosts)

    def test_gliner_degraded_mode(self, config: dict) -> None:
        engine = GLiNEREngine(config)
        # Not calling load() → model stays None
        assert not engine.available
        assert engine.analyze("Mario Rossi works at Acme") == []


# ===================================================================
# MergeEngine tests
# ===================================================================

class TestMergeEngine:
    """Merge engine: overlap resolution, dedup, sorting."""

    def test_regex_priority_over_gliner(
        self, merge_engine: MergeEngine
    ) -> None:
        regex_ent = RecognizedEntity(
            original="192.168.1.1",
            entity_type="IP_ADDRESS",
            start=10, end=21,
            confidence=0.95,
        )
        gliner_ent = RecognizedEntity(
            original="192.168.1.1",
            entity_type="HOSTNAME",
            start=10, end=21,
            confidence=0.98,
        )
        result = merge_engine.merge([regex_ent], [gliner_ent])
        # Regex IP_ADDRESS should win due to regex_priority_types
        assert len(result) == 1
        assert result[0].entity_type == "IP_ADDRESS"

    def test_overlap_keep_highest(self, merge_engine: MergeEngine) -> None:
        low = RecognizedEntity(
            original="admin",
            entity_type="PERSON",
            start=0, end=5,
            confidence=0.5,
        )
        high = RecognizedEntity(
            original="admin",
            entity_type="PERSON",
            start=0, end=5,
            confidence=0.9,
        )
        result = merge_engine.merge([], [low, high])
        assert len(result) == 1
        assert result[0].confidence == 0.9

    def test_no_duplicates(self, merge_engine: MergeEngine) -> None:
        ent = RecognizedEntity(
            original="10.0.0.1",
            entity_type="IP_ADDRESS",
            start=5, end=13,
            confidence=0.95,
        )
        result = merge_engine.merge([ent], [ent])
        assert len(result) == 1

    def test_sort_by_start(self, merge_engine: MergeEngine) -> None:
        e1 = RecognizedEntity(
            original="foo", entity_type="PERSON",
            start=20, end=23, confidence=0.8,
        )
        e2 = RecognizedEntity(
            original="bar", entity_type="ORG_NAME",
            start=5, end=8, confidence=0.7,
        )
        result = merge_engine.merge([], [e1, e2])
        assert result[0].start < result[1].start


# ===================================================================
# PentestNER integration tests
# ===================================================================

class TestPentestNER:
    """Full pipeline integration tests."""

    def test_full_pipeline_pentest_text(self, ner: PentestNER) -> None:
        text = (
            "Target host 10.0.1.50 has port 22 open. "
            "Found password=S3cretP@ss in /etc/shadow. "
            "Reference CVE-2024-1234."
        )
        entities = ner.analyze(text)
        types = {e.entity_type for e in entities}
        assert "IP_ADDRESS" in types
        assert "CREDENTIAL" in types

    def test_degraded_mode_regex_only(self) -> None:
        ner = PentestNER()
        # Force degraded mode: mark loaded without calling gliner.load()
        ner._gliner._model = None
        ner._loaded = True
        text = "scan 192.168.1.1 port 80"
        entities = ner.analyze(text)
        ips = [e for e in entities if e.entity_type == "IP_ADDRESS"]
        assert len(ips) >= 1

    def test_health_returns_mode(self, ner: PentestNER) -> None:
        h = ner.health()
        assert "regex" in h
        assert "gliner" in h
        assert "mode" in h
        assert h["regex"] == "ok"
        assert h["mode"] in ("regex+gliner", "regex-only")

    def test_analyze_never_raises(self, ner: PentestNER) -> None:
        # Garbage / edge-case inputs must not raise
        for inp in ["", " ", "\x00\x01\x02", "a" * 10000, None.__class__.__name__]:
            result = ner.analyze(inp)
            assert isinstance(result, list)
