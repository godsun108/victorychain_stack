from src.victory_impact.pq_evidence import PQEvidence, evidence_record


def sample():
    return PQEvidence(
        provider_id="provider",
        provider_version="1.2.3",
        ml_kem_parameter_set="ML-KEM-768",
        ml_dsa_parameter_set="ML-DSA-65",
        kem_round_trip=True,
        dsa_valid_signature=True,
        dsa_modified_message_rejected=True,
    )


def test_fingerprint_is_deterministic():
    assert sample().fingerprint() == sample().fingerprint()
    assert len(sample().fingerprint()) == 64


def test_research_record_is_not_deployment_approval():
    record = evidence_record(sample())
    assert record["evidence"]["deployment_approved"] is False
    assert record["claim"] == "research evidence only"
