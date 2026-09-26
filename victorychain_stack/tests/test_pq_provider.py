import pytest

from src.victory_impact.pq_conformance import (
    MLDSAVerifyVector,
    MLKEMDecapVector,
    check_ml_dsa_verify,
    check_ml_kem_decap,
)
from src.victory_impact.pq_provider import (
    Encapsulation,
    KeyPair,
    PQProvider,
    require_parameter_set,
)


class FakeProvider:
    provider_id = "fake-test-only"

    def ml_kem_keygen(self, parameter_set):
        return KeyPair(b"pk", b"sk")

    def ml_kem_encapsulate(self, parameter_set, public_key):
        return Encapsulation(b"ct", b"shared")

    def ml_kem_decapsulate(self, parameter_set, secret_key, ciphertext):
        return b"shared"

    def ml_dsa_keygen(self, parameter_set):
        return KeyPair(b"pk", b"sk")

    def ml_dsa_sign(self, parameter_set, secret_key, message):
        return b"sig"

    def ml_dsa_verify(self, parameter_set, public_key, message, signature):
        return signature == b"sig"


def test_provider_protocol_and_parameter_sets():
    provider = FakeProvider()
    assert isinstance(provider, PQProvider)
    require_parameter_set("ML-KEM", "ML-KEM-768")
    require_parameter_set("ML-DSA", "ML-DSA-65")
    with pytest.raises(ValueError):
        require_parameter_set("ML-KEM", "magic")


def test_normalized_conformance_harness():
    provider = FakeProvider()
    check_ml_dsa_verify(
        provider,
        MLDSAVerifyVector("ML-DSA-65", b"pk", b"msg", b"sig", True),
    )
    check_ml_kem_decap(
        provider,
        MLKEMDecapVector("ML-KEM-768", b"sk", b"ct", b"shared"),
    )


def test_conformance_failure_is_loud():
    provider = FakeProvider()
    with pytest.raises(AssertionError):
        check_ml_kem_decap(
            provider,
            MLKEMDecapVector("ML-KEM-768", b"sk", b"ct", b"wrong"),
        )
