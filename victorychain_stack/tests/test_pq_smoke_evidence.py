import json

from src.victory_impact.pq_evidence import PQEvidence, evidence_record


def test_evidence_json_is_stable_and_explicitly_research_only():
    evidence = PQEvidence(
        provider_id="test-provider",
        provider_version="1.0",
        ml_kem_parameter_set="ML-KEM-768",
        ml_dsa_parameter_set="ML-DSA-65",
        kem_round_trip=True,
        dsa_valid_signature=True,
        dsa_modified_message_rejected=True,
    )
    record = evidence_record(evidence)
    encoded = json.dumps(record, sort_keys=True)
    decoded = json.loads(encoded)

    assert decoded["fingerprint"] == evidence.fingerprint()
    assert decoded["evidence"]["evidence_class"] == "research-smoke"
    assert decoded["evidence"]["deployment_approved"] is False
    assert decoded["evidence"]["dsa_modified_message_rejected"] is True
