import hashlib
from datetime import datetime, timezone

import pytest

from src.victory_impact.hybrid_authorization import (
    HybridAuthorization,
    HybridPublicKeys,
)
from src.victory_impact.identity import AuthorizationChallenge, ReplayGuard
from src.victory_impact.quantum_security import SignedEnvelope


NOW = datetime(2026, 9, 26, 19, 0, tzinfo=timezone.utc)


class FakeClassical:
    def sign(self, key, message):
        return hashlib.sha256(key + message).digest()

    def verify(self, public_key, message, signature):
        return signature == self.sign(public_key, message)


class FakePQ:
    provider_id = "test-only"

    def sign(self, key, message):
        return hashlib.sha512(key + message).digest()

    def ml_dsa_verify(self, parameter_set, public_key, message, signature):
        return parameter_set == "ML-DSA-65" and signature == self.sign(public_key, message)


CLASSICAL_KEY = b"classical-public-test-key"
PQ_KEY = b"pq-public-test-key"
CLASSICAL = FakeClassical()
PQ = FakePQ()


def challenge(**overrides):
    values = dict(
        version=1,
        challenge_id="challenge-001",
        actor="did:victory:alice",
        action="attestation:create",
        resource="victory:record:123",
        nonce="unique-nonce",
        issued_at="2026-09-26T18:59:00Z",
        expires_at="2026-09-26T19:05:00Z",
        suite_id="victory-hybrid-v1",
    )
    values.update(overrides)
    return AuthorizationChallenge(**values)


def authorization(item=None, *, pq=True, classical=True):
    item = item or challenge()
    message = item.canonical_bytes()
    return HybridAuthorization(
        item,
        SignedEnvelope(
            version=1,
            suite_id=item.suite_id,
            payload_digest=item.digest(),
            classical_signature=CLASSICAL.sign(CLASSICAL_KEY, message).hex() if classical else None,
            pq_signature=PQ.sign(PQ_KEY, message).hex() if pq else None,
        ),
    )


def verify(auth, guard=None):
    auth.verify_and_consume(
        keys=HybridPublicKeys(CLASSICAL_KEY, PQ_KEY),
        classical_verifier=CLASSICAL,
        pq_provider=PQ,
        replay_guard=guard or ReplayGuard(),
        now=NOW,
    )


def test_valid_hybrid_authorization_passes():
    verify(authorization())


@pytest.mark.parametrize("missing", ["pq", "classical"])
def test_signature_stripping_fails_closed(missing):
    with pytest.raises(ValueError):
        verify(authorization(pq=missing != "pq", classical=missing != "classical"))


def test_payload_substitution_fails():
    auth = authorization()
    altered = HybridAuthorization(challenge(resource="victory:record:999"), auth.envelope)
    with pytest.raises(ValueError, match="digest mismatch"):
        verify(altered)


def test_classical_downgrade_fails():
    item = challenge(suite_id="victory-classical-v1")
    env = SignedEnvelope(
        version=1,
        suite_id="victory-classical-v1",
        payload_digest=item.digest(),
        classical_signature=CLASSICAL.sign(CLASSICAL_KEY, item.canonical_bytes()).hex(),
    )
    with pytest.raises(ValueError):
        verify(HybridAuthorization(item, env))


def test_suite_substitution_fails():
    auth = authorization()
    env = SignedEnvelope(
        version=1,
        suite_id="victory-pq-v1",
        payload_digest=auth.envelope.payload_digest,
        pq_signature=auth.envelope.pq_signature,
    )
    with pytest.raises(ValueError, match="suite mismatch"):
        verify(HybridAuthorization(auth.challenge, env))


def test_bad_pq_signature_fails():
    auth = authorization()
    env = SignedEnvelope(
        version=1,
        suite_id=auth.envelope.suite_id,
        payload_digest=auth.envelope.payload_digest,
        classical_signature=auth.envelope.classical_signature,
        pq_signature=b"forged".hex(),
    )
    with pytest.raises(ValueError, match="post-quantum"):
        verify(HybridAuthorization(auth.challenge, env))


def test_replay_fails():
    guard = ReplayGuard()
    auth = authorization()
    verify(auth, guard)
    with pytest.raises(ValueError, match="already consumed"):
        verify(auth, guard)
