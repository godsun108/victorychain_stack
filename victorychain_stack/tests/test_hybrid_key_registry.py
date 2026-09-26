from datetime import datetime, timezone

import pytest

from src.victory_impact.classical_crypto import (
    ECDSAP256Verifier,
    generate_research_p256_keypair,
    sign_research_p256,
)
from src.victory_impact.hybrid_authorization import HybridAuthorization, HybridPublicKeys
from src.victory_impact.identity import AuthorizationChallenge, ReplayGuard
from src.victory_impact.key_registry import KeyRegistry, PublicKeyRecord
from src.victory_impact.quantum_security import SignedEnvelope


NOW = datetime(2026, 9, 26, 20, 0, tzinfo=timezone.utc)


class FakePQ:
    provider_id = "test-only"

    @staticmethod
    def sign(key, message):
        import hashlib
        return hashlib.sha512(key + message).digest()

    def ml_dsa_verify(self, parameter_set, public_key, message, signature):
        return (
            parameter_set == "ML-DSA-65"
            and signature == self.sign(public_key, message)
        )


def fixture():
    actor = "did:victory:alice"
    classical_public, classical_private = generate_research_p256_keypair()
    pq_public = b"pq-public-1"
    registry = KeyRegistry()
    registry.register(PublicKeyRecord(
        "c1", actor, "authorization-classical", "ECDSA-P256-SHA256",
        classical_public, "2026-09-26T19:00:00Z",
    ))
    registry.register(PublicKeyRecord(
        "p1", actor, "authorization-pq", "ML-DSA-65",
        pq_public, "2026-09-26T19:00:00Z",
    ))
    challenge = AuthorizationChallenge(
        1, "challenge-1", actor, "attestation:create", "victory:record:1",
        "nonce-1", "2026-09-26T19:59:00Z", "2026-09-26T20:05:00Z",
    )
    message = challenge.canonical_bytes()
    pq = FakePQ()
    auth = HybridAuthorization(challenge, SignedEnvelope(
        version=1,
        suite_id=challenge.suite_id,
        payload_digest=challenge.digest(),
        classical_signature=sign_research_p256(classical_private, message).hex(),
        pq_signature=pq.sign(pq_public, message).hex(),
    ))
    keys = HybridPublicKeys(
        classical_public, pq_public, "ML-DSA-65", "c1", "p1"
    )
    return auth, keys, registry, pq


def verify(auth, keys, registry, pq):
    auth.verify_and_consume(
        keys=keys,
        classical_verifier=ECDSAP256Verifier(),
        pq_provider=pq,
        replay_guard=ReplayGuard(),
        now=NOW,
        key_registry=registry,
    )


def test_registered_active_keys_authorize():
    verify(*fixture())


def test_revoked_pq_key_fails_before_authorization():
    auth, keys, registry, pq = fixture()
    registry.revoke("p1", at=NOW)
    with pytest.raises(ValueError, match="not active"):
        verify(auth, keys, registry, pq)


def test_rotated_classical_key_rejects_old_authorization():
    auth, keys, registry, pq = fixture()
    new_public, _ = generate_research_p256_keypair()
    registry.rotate("c1", PublicKeyRecord(
        "c2", auth.challenge.actor, "authorization-classical",
        "ECDSA-P256-SHA256", new_public, "2026-09-26T20:00:00Z",
    ), at=NOW)
    with pytest.raises(ValueError, match="not active"):
        verify(auth, keys, registry, pq)


def test_registered_key_material_substitution_fails():
    auth, keys, registry, pq = fixture()
    substituted, _ = generate_research_p256_keypair()
    bad_keys = HybridPublicKeys(
        substituted, keys.pq_public_key, keys.pq_parameter_set,
        keys.classical_key_id, keys.pq_key_id,
    )
    with pytest.raises(ValueError, match="material mismatch"):
        verify(auth, bad_keys, registry, pq)


def test_wrong_actor_cannot_use_registered_keys():
    auth, keys, registry, pq = fixture()
    altered = AuthorizationChallenge(
        **{**auth.challenge.__dict__, "actor": "did:victory:bob"}
    )
    forged = HybridAuthorization(altered, SignedEnvelope(
        version=1,
        suite_id=altered.suite_id,
        payload_digest=altered.digest(),
        classical_signature=auth.envelope.classical_signature,
        pq_signature=auth.envelope.pq_signature,
    ))
    with pytest.raises(ValueError, match="not bound"):
        verify(forged, keys, registry, pq)
