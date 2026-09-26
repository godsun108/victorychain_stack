"""Victory hybrid authorization verification boundary.

Both classical and post-quantum signatures cover the exact same canonical
authorization bytes. This module composes verifier results; it does not invent
or implement cryptographic primitives.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .identity import AuthorizationChallenge, ReplayGuard
from .key_registry import KeyRegistry
from .pq_provider import PQProvider
from .quantum_security import SignedEnvelope, authorize_suite


class ClassicalVerifier(Protocol):
    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool: ...


@dataclass(frozen=True)
class HybridPublicKeys:
    classical_public_key: bytes
    pq_public_key: bytes
    pq_parameter_set: str = "ML-DSA-65"
    classical_key_id: str | None = None
    pq_key_id: str | None = None


@dataclass(frozen=True)
class HybridAuthorization:
    challenge: AuthorizationChallenge
    envelope: SignedEnvelope

    def verify_and_consume(
        self,
        *,
        keys: HybridPublicKeys,
        classical_verifier: ClassicalVerifier,
        pq_provider: PQProvider,
        replay_guard: ReplayGuard,
        now: datetime,
        key_registry: KeyRegistry | None = None,
    ) -> None:
        self.challenge.validate(now=now)
        self.envelope.validate_structure()
        authorize_suite(self.challenge.suite_id)

        if self.challenge.suite_id != self.envelope.suite_id:
            raise ValueError("suite mismatch")
        if self.envelope.payload_digest != self.challenge.digest():
            raise ValueError("authorization payload digest mismatch")

        if key_registry is not None:
            if not keys.classical_key_id or not keys.pq_key_id:
                raise ValueError("registered key ids required")
            classical_record = key_registry.require_active(
                keys.classical_key_id, actor=self.challenge.actor, purpose="authorization-classical"
            )
            pq_record = key_registry.require_active(
                keys.pq_key_id, actor=self.challenge.actor, purpose="authorization-pq"
            )
            if classical_record.public_key != keys.classical_public_key:
                raise ValueError("classical key material mismatch")
            if pq_record.public_key != keys.pq_public_key:
                raise ValueError("post-quantum key material mismatch")

        message = self.challenge.canonical_bytes()
        try:
            classical_signature = bytes.fromhex(self.envelope.classical_signature or "")
            pq_signature = bytes.fromhex(self.envelope.pq_signature or "")
        except ValueError as exc:
            raise ValueError("signatures must be hex encoded") from exc

        if not classical_verifier.verify(
            keys.classical_public_key, message, classical_signature
        ):
            raise ValueError("classical signature verification failed")
        if not pq_provider.ml_dsa_verify(
            keys.pq_parameter_set, keys.pq_public_key, message, pq_signature
        ):
            raise ValueError("post-quantum signature verification failed")

        # Consume only after all checks succeed. Production storage must make
        # this atomic with authorization execution.
        replay_guard.consume(self.challenge, now=now)
