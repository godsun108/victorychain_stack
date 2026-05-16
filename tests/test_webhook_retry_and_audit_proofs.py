from __future__ import annotations

import hashlib
import hmac
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from src.victory_impact.routers import admin as admin_router
from src.victory_impact.models import (
    Base,
    Beneficiary,
    BeneficiaryRequest,
    Disbursement,
    DisbursementStatus,
    DonationCategory,
    DonationCategoryCode,
    Receipt,
    WebhookEvent,
)
from src.victory_impact.schemas import WebhookRemediationUpdate
from src.victory_impact.services.audit_proofs import build_audit_proof
from src.victory_impact.services.donations import ensure_default_categories
from src.victory_impact.services.payment_adapters import EVMIndexerAdapter, VUSDAdapter
from src.victory_impact.services.webhook_events import (
    STATUS_DEAD_LETTER,
    STATUS_RETRY_QUEUED,
    compute_retry_delay_seconds,
    mark_retry_or_dead_letter,
    register_webhook_event,
)
from src.victory_impact.services.observability import build_prometheus_metrics
from src.victory_impact.services.webhook_processing import process_webhook_event
from src.victory_impact.services.webhook_retry import run_retry_batch, webhook_queue_metrics


def build_db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    return factory()


def test_retry_transitions_to_dead_letter_after_max_attempts():
    db = build_db()
    event, _ = register_webhook_event(
        db,
        provider="stripe",
        provider_event_id="evt-retry-1",
        event_type="payment_intent.succeeded",
        payload_json={"simulate_failure": True},
        max_retries=2,
    )

    for _ in range(2):
        try:
            process_webhook_event("stripe", event.payload_json, VUSDAdapter(EVMIndexerAdapter("http://rpc.local"), "0x0"))
        except Exception as exc:
            event = mark_retry_or_dead_letter(db, event, str(exc), retry_interval_seconds=1)

    assert event.retry_count == 2
    assert event.processing_status == STATUS_DEAD_LETTER
    assert event.dead_lettered_at is not None
    db.close()


def test_retry_stays_queued_before_max_attempts():
    db = build_db()
    event, _ = register_webhook_event(
        db,
        provider="stripe",
        provider_event_id="evt-retry-2",
        event_type="payment_intent.succeeded",
        payload_json={"simulate_failure": True},
        max_retries=3,
    )

    try:
        process_webhook_event("stripe", event.payload_json, VUSDAdapter(EVMIndexerAdapter("http://rpc.local"), "0x0"))
    except Exception as exc:
        event = mark_retry_or_dead_letter(db, event, str(exc), retry_interval_seconds=60)

    assert event.retry_count == 1
    assert event.processing_status == STATUS_RETRY_QUEUED
    assert event.next_retry_at is not None
    db.close()


def test_signed_audit_proof_for_webhook_event_is_deterministic():
    db = build_db()
    event, _ = register_webhook_event(
        db,
        provider="stripe",
        provider_event_id="evt-proof-1",
        event_type="payment_intent.succeeded",
        payload_json={"note": "proof"},
        max_retries=2,
    )
    secret = "proof-secret"
    proof = build_audit_proof(db, "webhook_event", event.id, secret)
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        proof["canonical_payload"].encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    assert proof["signature_hex"] == expected_sig
    db.close()


def test_signed_audit_proof_for_disbursement():
    db = build_db()
    ensure_default_categories(db)
    category = db.scalar(select(DonationCategory).where(DonationCategory.code == DonationCategoryCode.MERCY))
    beneficiary = Beneficiary(
        category_id=category.id,
        reference_code="BEN-PROOF-1",
        needs_assessment="support",
        public_summary="anonymized",
        private_profile_json={},
    )
    db.add(beneficiary)
    db.flush()
    req = BeneficiaryRequest(
        beneficiary_id=beneficiary.id,
        requested_aid_amount=Decimal("50.00"),
        requested_currency="USD",
        request_reason="test",
    )
    db.add(req)
    db.flush()
    disb = Disbursement(
        beneficiary_request_id=req.id,
        category_id=category.id,
        amount=Decimal("25.00"),
        currency="USD",
        treasury_wallet="MERCY_TREASURY_PLACEHOLDER",
        destination_reference="dest",
        disbursement_status=DisbursementStatus.SENT,
    )
    db.add(disb)
    db.flush()
    db.add(
        Receipt(
            disbursement_id=disb.id,
            receipt_number="VC-DISB-000001",
            legal_text_version="v1",
            tax_receipt_eligible=False,
        )
    )
    db.commit()

    proof = build_audit_proof(db, "disbursement", disb.id, "proof-secret")
    assert proof["entity_type"] == "disbursement"
    assert "signature_hex" in proof
    db.close()


def test_retry_batch_processes_queued_event():
    db = build_db()
    event, _ = register_webhook_event(
        db,
        provider="stripe",
        provider_event_id="evt-batch-1",
        event_type="payment_intent.succeeded",
        payload_json={"simulate_failure": True},
        max_retries=3,
    )
    event = mark_retry_or_dead_letter(db, event, "first failure", retry_interval_seconds=1)
    assert event.processing_status == STATUS_RETRY_QUEUED

    result = run_retry_batch(
        db=db,
        vusd_adapter=VUSDAdapter(EVMIndexerAdapter("http://rpc.local"), "0x0"),
        include_dead_letter=False,
        limit=100,
        event_ids=[event.id],
        processor=lambda provider, payload, vusd: None,
    )
    assert result["attempted"] == 1
    assert result["processed"] == 1
    refreshed = db.scalar(select(WebhookEvent).where(WebhookEvent.id == event.id))
    assert refreshed is not None
    assert refreshed.processing_status == "processed"
    db.close()


def test_webhook_queue_metrics_counts():
    db = build_db()
    queued_event, _ = register_webhook_event(
        db,
        provider="stripe",
        provider_event_id="evt-metric-queued",
        event_type="payment_intent.succeeded",
        payload_json={"simulate_failure": True},
        max_retries=3,
    )
    dead_event, _ = register_webhook_event(
        db,
        provider="stripe",
        provider_event_id="evt-metric-dead",
        event_type="payment_intent.succeeded",
        payload_json={"simulate_failure": True},
        max_retries=1,
    )

    queued_event = mark_retry_or_dead_letter(db, queued_event, "queued failure", retry_interval_seconds=1)
    dead_event = mark_retry_or_dead_letter(db, dead_event, "dead failure", retry_interval_seconds=1)
    assert dead_event.processing_status == STATUS_DEAD_LETTER
    queued_event.next_retry_at = queued_event.first_seen_at
    db.commit()

    metrics = webhook_queue_metrics(db)
    assert metrics["retry_queue_depth"] >= 1
    assert metrics["total_retry_queued"] >= 1
    assert metrics["dead_letter_count"] >= 1
    assert metrics["oldest_pending_event_id"] is not None
    db.close()


def test_exponential_backoff_with_jitter_bounds(monkeypatch):
    monkeypatch.setattr("src.victory_impact.services.webhook_events.random.uniform", lambda a, b: 1.0)
    d1 = compute_retry_delay_seconds(1, 60, 3600, 0.2)
    d2 = compute_retry_delay_seconds(2, 60, 3600, 0.2)
    d3 = compute_retry_delay_seconds(3, 60, 3600, 0.2)
    assert d1 == 60
    assert d2 == 120
    assert d3 == 240


def test_admin_remediation_update_and_metrics_payload():
    db = build_db()
    event, _ = register_webhook_event(
        db,
        provider="stripe",
        provider_event_id="evt-remed-1",
        event_type="payment_intent.succeeded",
        payload_json={"simulate_failure": True},
        max_retries=1,
    )
    event = mark_retry_or_dead_letter(db, event, "failed", retry_interval_seconds=1)
    assert event.processing_status == STATUS_DEAD_LETTER

    payload = WebhookRemediationUpdate(
        owner_user_id="owner-123",
        remediation_status="in_progress",
        remediation_notes="Investigating source system",
    )
    response = admin_router.update_webhook_remediation(event.id, payload, db, role="admin")
    assert response["status"] == "updated"
    assert response["remediation_status"] == "in_progress"
    assert response["remediation_owner_user_id"] == "owner-123"

    metrics = build_prometheus_metrics(db)
    assert "webhook_dead_letter_total" in metrics
    assert "disbursements_total" in metrics
    assert "webhook_status_count_count" in metrics
    db.close()
