import pytest

from src.victory_impact.providers.liboqs_provider import LibOQSProvider


def test_provider_rejects_nonstandard_parameter_sets_without_loading_library():
    assert LibOQSProvider._kem_name("ML-KEM-768") == "ML-KEM-768"
    assert LibOQSProvider._dsa_name("ML-DSA-65") == "ML-DSA-65"
    with pytest.raises(ValueError):
        LibOQSProvider._kem_name("Kyber-Magic")
    with pytest.raises(ValueError):
        LibOQSProvider._dsa_name("Dilithium-Custom")
