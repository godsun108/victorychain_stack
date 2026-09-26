import pytest

from src.victory_impact.quantum_security import (
    DEFAULT_SUITE,
    SecurityClass,
    SignedEnvelope,
    authorize_suite,
    security_manifest,
)


def test_default_is_hybrid():
    suite = authorize_suite(DEFAULT_SUITE)
    assert suite.security_class is SecurityClass.HYBRID
    assert "ML-DSA" in suite.signature
    assert "ML-KEM" in suite.key_establishment


def test_classical_only_downgrade_rejected_by_default():
    with pytest.raises(ValueError):
        authorize_suite("victory-classical-v1")


def test_unknown_suite_rejected():
    with pytest.raises(ValueError):
        authorize_suite("victory-magic-v99")


def test_hybrid_envelope_requires_both_signatures():
    with pytest.raises(ValueError):
        SignedEnvelope(
            version=1,
            suite_id="victory-hybrid-v1",
            payload_digest="a" * 64,
            classical_signature="classical",
            pq_signature=None,
        ).validate_structure()


def test_hybrid_envelope_structure_accepts_two_signature_slots():
    SignedEnvelope(
        version=1,
        suite_id="victory-hybrid-v1",
        payload_digest="a" * 64,
        classical_signature="classical-test-vector",
        pq_signature="pq-test-vector",
    ).validate_structure()


def test_soul_key_has_no_authority():
    manifest = security_manifest()
    assert manifest["soul_key_authority"] == "none"
    assert manifest["funds_authority"].startswith("disabled")
