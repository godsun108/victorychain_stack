"""Credential-free PQ research smoke test.

Exit non-zero if the optional provider cannot complete ML-KEM and ML-DSA
round trips. Passing this is implementation smoke evidence, not certification.
"""
from src.victory_impact.providers.liboqs_provider import LibOQSProvider
from src.victory_impact.pq_conformance import kem_round_trip


def main() -> None:
    provider = LibOQSProvider()

    if not kem_round_trip(provider, "ML-KEM-768"):
        raise SystemExit("ML-KEM-768 round trip failed")

    keys = provider.ml_dsa_keygen("ML-DSA-65")
    message = b"victory-pq-smoke-v1"
    signature = provider.ml_dsa_sign("ML-DSA-65", keys.secret_key, message)
    if not provider.ml_dsa_verify("ML-DSA-65", keys.public_key, message, signature):
        raise SystemExit("ML-DSA-65 round trip failed")

    if provider.ml_dsa_verify(
        "ML-DSA-65", keys.public_key, message + b"-tampered", signature
    ):
        raise SystemExit("ML-DSA accepted tampered message")

    print("PQ_SMOKE_OK", provider.provider_id, provider.provider_version)


if __name__ == "__main__":
    main()
