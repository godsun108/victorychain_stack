"""Provider-neutral post-quantum cryptography boundary.

No primitive is implemented here. Providers must wrap a vetted implementation
of the named standardized algorithms and can be swapped without changing
Victory business logic.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class KeyPair:
    public_key: bytes
    secret_key: bytes


@dataclass(frozen=True)
class Encapsulation:
    ciphertext: bytes
    shared_secret: bytes


@runtime_checkable
class PQProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    def ml_kem_keygen(self, parameter_set: str) -> KeyPair: ...

    def ml_kem_encapsulate(
        self, parameter_set: str, public_key: bytes
    ) -> Encapsulation: ...

    def ml_kem_decapsulate(
        self, parameter_set: str, secret_key: bytes, ciphertext: bytes
    ) -> bytes: ...

    def ml_dsa_keygen(self, parameter_set: str) -> KeyPair: ...

    def ml_dsa_sign(
        self, parameter_set: str, secret_key: bytes, message: bytes
    ) -> bytes: ...

    def ml_dsa_verify(
        self,
        parameter_set: str,
        public_key: bytes,
        message: bytes,
        signature: bytes,
    ) -> bool: ...


ML_KEM_PARAMETER_SETS = frozenset({"ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"})
ML_DSA_PARAMETER_SETS = frozenset({"ML-DSA-44", "ML-DSA-65", "ML-DSA-87"})


def require_parameter_set(algorithm: str, parameter_set: str) -> None:
    allowed = {
        "ML-KEM": ML_KEM_PARAMETER_SETS,
        "ML-DSA": ML_DSA_PARAMETER_SETS,
    }
    if algorithm not in allowed or parameter_set not in allowed[algorithm]:
        raise ValueError("unsupported post-quantum parameter set")
