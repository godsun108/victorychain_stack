"""Victory post-quantum security policy and crypto-agility boundary.

This module intentionally does NOT implement cryptographic primitives itself.
Production primitives must come from vetted implementations of standardized
algorithms. The purpose here is algorithm negotiation, policy, downgrade
resistance, and an auditable migration boundary.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class SecurityClass(str, Enum):
    CLASSICAL = "classical"
    POST_QUANTUM = "post_quantum"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class AlgorithmSuite:
    suite_id: str
    security_class: SecurityClass
    signature: tuple[str, ...]
    key_establishment: tuple[str, ...]
    experimental: bool = False


SUITES = {
    "victory-classical-v1": AlgorithmSuite(
        "victory-classical-v1", SecurityClass.CLASSICAL,
        ("ECDSA-P256",), ("ECDH-P256",),
    ),
    "victory-pq-v1": AlgorithmSuite(
        "victory-pq-v1", SecurityClass.POST_QUANTUM,
        ("ML-DSA",), ("ML-KEM",),
    ),
    "victory-hybrid-v1": AlgorithmSuite(
        "victory-hybrid-v1", SecurityClass.HYBRID,
        ("ECDSA-P256", "ML-DSA"), ("ECDH-P256", "ML-KEM"),
    ),
}

DEFAULT_SUITE = "victory-hybrid-v1"


def get_suite(suite_id: str) -> AlgorithmSuite:
    try:
        return SUITES[suite_id]
    except KeyError as exc:
        raise ValueError("unsupported cryptographic suite") from exc


def authorize_suite(
    suite_id: str,
    *,
    require_post_quantum: bool = True,
    allow_experimental: bool = False,
) -> AlgorithmSuite:
    suite = get_suite(suite_id)
    if suite.experimental and not allow_experimental:
        raise ValueError("experimental cryptography is forbidden")
    if require_post_quantum and suite.security_class is SecurityClass.CLASSICAL:
        raise ValueError("post-quantum-capable suite required")
    return suite


@dataclass(frozen=True)
class SignedEnvelope:
    version: int
    suite_id: str
    payload_digest: str
    classical_signature: str | None = None
    pq_signature: str | None = None

    def validate_structure(self) -> None:
        if self.version != 1:
            raise ValueError("unsupported envelope version")
        suite = authorize_suite(self.suite_id)
        if len(self.payload_digest) != 64:
            raise ValueError("expected SHA-256 payload digest")
        if suite.security_class is SecurityClass.HYBRID:
            if not self.classical_signature or not self.pq_signature:
                raise ValueError("hybrid envelope requires both signatures")
        elif suite.security_class is SecurityClass.POST_QUANTUM:
            if not self.pq_signature:
                raise ValueError("post-quantum signature required")


def security_manifest() -> dict:
    return {
        "default_suite": DEFAULT_SUITE,
        "policy": "crypto-agile-hybrid-migration",
        "funds_authority": "disabled_until_vetted_implementation_and_review",
        "soul_key_authority": "none",
        "suites": {
            key: {
                "security_class": value.security_class.value,
                "signature": list(value.signature),
                "key_establishment": list(value.key_establishment),
                "experimental": value.experimental,
            }
            for key, value in SUITES.items()
        },
    }
