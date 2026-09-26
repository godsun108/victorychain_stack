"""Evidence records for Victory post-quantum research."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json


@dataclass(frozen=True)
class PQEvidence:
    provider_id: str
    provider_version: str
    ml_kem_parameter_set: str
    ml_dsa_parameter_set: str
    kem_round_trip: bool
    dsa_valid_signature: bool
    dsa_modified_message_rejected: bool
    evidence_class: str = "research-smoke"
    deployment_approved: bool = False

    def canonical_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


def evidence_record(evidence: PQEvidence) -> dict:
    return {
        "evidence": asdict(evidence),
        "fingerprint": evidence.fingerprint(),
        "claim": "research evidence only",
    }
