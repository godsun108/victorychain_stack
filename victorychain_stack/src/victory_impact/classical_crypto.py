"""Classical signature adapter for Victory hybrid authorization.

Uses the cryptography project's ECDSA P-256 implementation. This is a software
research/integration adapter, not a replacement for hardware-backed passkeys.
"""
from __future__ import annotations

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


class ECDSAP256Verifier:
    algorithm = "ECDSA-P256-SHA256"

    def verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        try:
            key = serialization.load_pem_public_key(public_key)
            if not isinstance(key, ec.EllipticCurvePublicKey):
                return False
            if not isinstance(key.curve, ec.SECP256R1):
                return False
            key.verify(signature, message, ec.ECDSA(hashes.SHA256()))
            return True
        except (ValueError, TypeError):
            return False
        except Exception as exc:
            # cryptography raises InvalidSignature for forged signatures; avoid
            # coupling business logic to provider-specific exception classes.
            if exc.__class__.__name__ == "InvalidSignature":
                return False
            raise


def generate_research_p256_keypair() -> tuple[bytes, object]:
    """Generate ephemeral CI/research keys; never persists private material."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return public_pem, private_key


def sign_research_p256(private_key: object, message: bytes) -> bytes:
    return private_key.sign(message, ec.ECDSA(hashes.SHA256()))
