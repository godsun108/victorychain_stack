"""Conformance harness for standardized PQ provider adapters.

Vectors are data, not code. This harness consumes normalized vectors derived
from authoritative validation sources and checks provider behavior.
"""
from __future__ import annotations

from dataclasses import dataclass

from .pq_provider import PQProvider, require_parameter_set


@dataclass(frozen=True)
class MLDSAVerifyVector:
    parameter_set: str
    public_key: bytes
    message: bytes
    signature: bytes
    expected: bool


@dataclass(frozen=True)
class MLKEMDecapVector:
    parameter_set: str
    secret_key: bytes
    ciphertext: bytes
    expected_shared_secret: bytes


def check_ml_dsa_verify(provider: PQProvider, vector: MLDSAVerifyVector) -> None:
    require_parameter_set("ML-DSA", vector.parameter_set)
    actual = provider.ml_dsa_verify(
        vector.parameter_set,
        vector.public_key,
        vector.message,
        vector.signature,
    )
    if actual is not vector.expected:
        raise AssertionError("ML-DSA verification vector mismatch")


def check_ml_kem_decap(provider: PQProvider, vector: MLKEMDecapVector) -> None:
    require_parameter_set("ML-KEM", vector.parameter_set)
    actual = provider.ml_kem_decapsulate(
        vector.parameter_set,
        vector.secret_key,
        vector.ciphertext,
    )
    if actual != vector.expected_shared_secret:
        raise AssertionError("ML-KEM decapsulation vector mismatch")
