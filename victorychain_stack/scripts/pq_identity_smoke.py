"""Research-only end-to-end Victory Identity hybrid authorization smoke."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

from src.victory_impact.hybrid_authorization import HybridAuthorization, HybridPublicKeys
from src.victory_impact.identity import AuthorizationChallenge, ReplayGuard
from src.victory_impact.key_registry import KeyRegistry, PublicKeyRecord
from src.victory_impact.providers.liboqs_provider import LibOQSProvider
from src.victory_impact.quantum_security import SignedEnvelope


class ResearchClassicalVerifier:
    """Deterministic test verifier only; NOT production classical cryptography."""
    def sign(self, key: bytes, message: bytes) -> bytes:
        return hashlib.sha256(key + message).digest()

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        return signature == self.sign(public_key, message)


def main() -> None:
    provider = LibOQSProvider()
    pq_keys = provider.ml_dsa_keygen("ML-DSA-65")
    classical_key = b"research-only-classical-key"
    classical = ResearchClassicalVerifier()

    now = datetime.now(timezone.utc)
    challenge = AuthorizationChallenge(
        version=1,
        challenge_id="pq-identity-smoke",
        actor="did:victory:research-smoke",
        action="attestation:create",
        resource="victory:research:smoke",
        nonce=hashlib.sha256(pq_keys.public_key).hexdigest()[:32],
        issued_at=(now - timedelta(seconds=5)).isoformat(),
        expires_at=(now + timedelta(minutes=5)).isoformat(),
        suite_id="victory-hybrid-v1",
    )
    message = challenge.canonical_bytes()

    registry = KeyRegistry()
    registry.register(PublicKeyRecord(
        "classical-1", challenge.actor, "authorization-classical",
        "RESEARCH-TEST-ONLY", classical_key, challenge.issued_at,
    ))
    registry.register(PublicKeyRecord(
        "pq-1", challenge.actor, "authorization-pq",
        "ML-DSA-65", pq_keys.public_key, challenge.issued_at,
    ))

    envelope = SignedEnvelope(
        version=1,
        suite_id=challenge.suite_id,
        payload_digest=challenge.digest(),
        classical_signature=classical.sign(classical_key, message).hex(),
        pq_signature=provider.ml_dsa_sign("ML-DSA-65", pq_keys.secret_key, message).hex(),
    )
    authorization = HybridAuthorization(challenge, envelope)
    authorization.verify_and_consume(
        keys=HybridPublicKeys(
            classical_key, pq_keys.public_key, "ML-DSA-65", "classical-1", "pq-1"
        ),
        classical_verifier=classical,
        pq_provider=provider,
        replay_guard=ReplayGuard(),
        now=now,
        key_registry=registry,
    )
    print("VICTORY_PQ_IDENTITY_SMOKE=PASS")
    print("CLAIM=research-only; classical leg is deterministic test verifier")
    print(f"PQ_PROVIDER={provider.provider_id}")
    print("PQ_PARAMETER_SET=ML-DSA-65")
    print(f"CHALLENGE_DIGEST={challenge.digest()}")


if __name__ == "__main__":
    main()
