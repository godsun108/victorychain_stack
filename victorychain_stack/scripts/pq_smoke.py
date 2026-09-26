"""Credential-free PQ research smoke test with evidence emission.

Passing this is implementation smoke evidence, not certification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.victory_impact.pq_conformance import kem_round_trip
from src.victory_impact.pq_evidence import PQEvidence, evidence_record
from src.victory_impact.providers.liboqs_provider import LibOQSProvider


def run() -> dict:
    provider = LibOQSProvider()
    kem_ok = kem_round_trip(provider, "ML-KEM-768")

    keys = provider.ml_dsa_keygen("ML-DSA-65")
    message = b"victory-pq-smoke-v2"
    signature = provider.ml_dsa_sign("ML-DSA-65", keys.secret_key, message)

    valid_ok = provider.ml_dsa_verify(
        "ML-DSA-65", keys.public_key, message, signature
    )
    modified_rejected = not provider.ml_dsa_verify(
        "ML-DSA-65", keys.public_key, message + b"-modified", signature
    )

    evidence = PQEvidence(
        provider_id=provider.provider_id,
        provider_version=provider.provider_version,
        ml_kem_parameter_set="ML-KEM-768",
        ml_dsa_parameter_set="ML-DSA-65",
        kem_round_trip=kem_ok,
        dsa_valid_signature=valid_ok,
        dsa_modified_message_rejected=modified_rejected,
    )

    if not (kem_ok and valid_ok and modified_rejected):
        raise SystemExit("PQ smoke evidence gate failed")

    return evidence_record(evidence)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-out", type=Path)
    args = parser.parse_args()

    record = run()
    encoded = json.dumps(record, sort_keys=True, indent=2)
    if args.evidence_out:
        args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
        args.evidence_out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


if __name__ == "__main__":
    main()
