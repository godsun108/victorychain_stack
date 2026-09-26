from src.victory_impact.classical_crypto import (
    ECDSAP256Verifier,
    generate_research_p256_keypair,
    sign_research_p256,
)


def test_real_p256_signature_verifies_and_tamper_fails():
    public_key, private_key = generate_research_p256_keypair()
    message = b"victory canonical authorization"
    signature = sign_research_p256(private_key, message)
    verifier = ECDSAP256Verifier()
    assert verifier.verify(public_key, message, signature)
    assert not verifier.verify(public_key, message + b"!", signature)


def test_wrong_p256_key_fails():
    public_key, private_key = generate_research_p256_keypair()
    other_public_key, _ = generate_research_p256_keypair()
    signature = sign_research_p256(private_key, b"intent")
    assert not ECDSAP256Verifier().verify(other_public_key, b"intent", signature)
