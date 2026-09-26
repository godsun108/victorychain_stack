"""Research adapter for Open Quantum Safe's liboqs Python wrapper.

This adapter is optional. It does not make Victory, liboqs, or a deployment
NIST-validated. Production promotion requires pinned versions, authoritative
validation evidence, threat modeling, and independent review.
"""
from __future__ import annotations

from ..pq_provider import Encapsulation, KeyPair, require_parameter_set


class LibOQSProvider:
    provider_id = "open-quantum-safe/liboqs-python"

    def __init__(self):
        try:
            import oqs
        except ImportError as exc:
            raise RuntimeError(
                "optional PQ provider unavailable; install requirements-pq.txt"
            ) from exc
        self._oqs = oqs
        self.provider_version = getattr(oqs, "__version__", "unknown")

    @staticmethod
    def _kem_name(parameter_set: str) -> str:
        require_parameter_set("ML-KEM", parameter_set)
        return parameter_set

    @staticmethod
    def _dsa_name(parameter_set: str) -> str:
        require_parameter_set("ML-DSA", parameter_set)
        return parameter_set

    def ml_kem_keygen(self, parameter_set: str) -> KeyPair:
        name = self._kem_name(parameter_set)
        with self._oqs.KeyEncapsulation(name) as kem:
            public_key = kem.generate_keypair()
            secret_key = kem.export_secret_key()
        return KeyPair(public_key, secret_key)

    def ml_kem_encapsulate(self, parameter_set: str, public_key: bytes) -> Encapsulation:
        name = self._kem_name(parameter_set)
        with self._oqs.KeyEncapsulation(name) as kem:
            ciphertext, shared_secret = kem.encap_secret(public_key)
        return Encapsulation(ciphertext, shared_secret)

    def ml_kem_decapsulate(
        self, parameter_set: str, secret_key: bytes, ciphertext: bytes
    ) -> bytes:
        name = self._kem_name(parameter_set)
        with self._oqs.KeyEncapsulation(name, secret_key) as kem:
            return kem.decap_secret(ciphertext)

    def ml_dsa_keygen(self, parameter_set: str) -> KeyPair:
        name = self._dsa_name(parameter_set)
        with self._oqs.Signature(name) as signer:
            public_key = signer.generate_keypair()
            secret_key = signer.export_secret_key()
        return KeyPair(public_key, secret_key)

    def ml_dsa_sign(
        self, parameter_set: str, secret_key: bytes, message: bytes
    ) -> bytes:
        name = self._dsa_name(parameter_set)
        with self._oqs.Signature(name, secret_key) as signer:
            return signer.sign(message)

    def ml_dsa_verify(
        self,
        parameter_set: str,
        public_key: bytes,
        message: bytes,
        signature: bytes,
    ) -> bool:
        name = self._dsa_name(parameter_set)
        with self._oqs.Signature(name) as verifier:
            return bool(verifier.verify(message, signature, public_key))
