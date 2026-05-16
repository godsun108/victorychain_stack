from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import ComplianceReview, DonationCategory, DonationCategoryCode, TreasuryAccount, WebhookEvent
from ..policies import runtime_policies
from ..schemas import RuntimePolicyUpdate, TreasuryStats, WebhookRemediationUpdate, WebhookRetryRequest
from ..security import current_role
from ..services.donations import ensure_default_categories
from ..services.payment_adapters import EVMIndexerAdapter, VUSDAdapter
from ..services.treasury import treasury_stats
from ..services.webhook_events import (
    list_webhook_events,
)
from ..services.webhook_retry import run_retry_batch, webhook_queue_metrics

router = APIRouter(prefix="/admin", tags=["admin"])
retry_indexer_adapter = EVMIndexerAdapter(settings.evm_rpc_url, settings.evm_required_confirmations)
retry_vusd_adapter = VUSDAdapter(retry_indexer_adapter, settings.vusd_contract_address)


def _assert_admin_or_board(role: str) -> None:
    if role not in {"admin", "board", "compliance"}:
        raise HTTPException(status_code=403, detail="admin or board role required")


@router.get("/treasury", response_model=list[TreasuryStats])
def get_treasury_dashboard(db: Session = Depends(get_db), role: str = Depends(current_role)):
    _assert_admin_or_board(role)
    ensure_default_categories(db)
    return [treasury_stats(db, code) for code in DonationCategoryCode]


@router.get("/policies")
def get_runtime_policies(role: str = Depends(current_role)):
    _assert_admin_or_board(role)
    return {
        "tax_receipts_enabled": runtime_policies.tax_receipts_enabled,
        "enforce_ofac_screening": runtime_policies.enforce_ofac_screening,
        "enforce_kyc_kyb_large_threshold": runtime_policies.enforce_kyc_kyb_large_threshold,
    }


@router.patch("/policies")
def update_runtime_policies(payload: RuntimePolicyUpdate, role: str = Depends(current_role)):
    _assert_admin_or_board(role)

    if payload.tax_receipts_enabled is not None:
        runtime_policies.tax_receipts_enabled = payload.tax_receipts_enabled
    if payload.enforce_ofac_screening is not None:
        runtime_policies.enforce_ofac_screening = payload.enforce_ofac_screening
    if payload.enforce_kyc_kyb_large_threshold is not None:
        runtime_policies.enforce_kyc_kyb_large_threshold = payload.enforce_kyc_kyb_large_threshold

    return {
        "status": "updated",
        "policies": {
            "tax_receipts_enabled": runtime_policies.tax_receipts_enabled,
            "enforce_ofac_screening": runtime_policies.enforce_ofac_screening,
            "enforce_kyc_kyb_large_threshold": runtime_policies.enforce_kyc_kyb_large_threshold,
        },
    }


@router.patch("/categories/{category_code}/treasury-wallet")
def update_treasury_wallet(category_code: DonationCategoryCode, treasury_wallet: str, db: Session = Depends(get_db), role: str = Depends(current_role)):
    _assert_admin_or_board(role)
    category = db.scalar(select(DonationCategory).where(DonationCategory.code == category_code))
    if not category:
        raise HTTPException(status_code=404, detail="category not found")
    category.treasury_wallet = treasury_wallet
    treasury = db.scalar(select(TreasuryAccount).where(TreasuryAccount.category_id == category.id))
    if treasury:
        treasury.account_reference = treasury_wallet
    db.commit()
    return {"status": "updated", "category": category_code, "treasury_wallet": treasury_wallet}


@router.get("/compliance/reviews")
def list_compliance_reviews(limit: int = 100, db: Session = Depends(get_db), role: str = Depends(current_role)):
    _assert_admin_or_board(role)
    rows = db.scalars(select(ComplianceReview).order_by(ComplianceReview.created_at.desc()).limit(limit)).all()
    return [
        {
            "id": row.id,
            "subject_type": row.subject_type,
            "subject_id": row.subject_id,
            "review_type": row.review_type,
            "status": row.status.value,
            "findings": row.findings,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/webhooks/events")
def list_webhook_monitor_events(
    provider: str | None = None,
    processing_status: str | None = None,
    remediation_status: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    role: str = Depends(current_role),
):
    _assert_admin_or_board(role)
    rows = list_webhook_events(
        db,
        provider=provider,
        processing_status=processing_status,
        remediation_status=remediation_status,
        limit=limit,
    )
    return [
        {
            "id": row.id,
            "provider": row.provider,
            "provider_event_id": row.provider_event_id,
            "event_type": row.event_type,
            "delivery_count": row.delivery_count,
            "processed": row.processed,
            "processing_status": row.processing_status,
            "retry_count": row.retry_count,
            "max_retries": row.max_retries,
            "last_error": row.last_error,
            "next_retry_at": row.next_retry_at,
            "processed_at": row.processed_at,
            "dead_lettered_at": row.dead_lettered_at,
            "first_seen_at": row.first_seen_at,
            "last_seen_at": row.last_seen_at,
            "remediation_owner_user_id": row.remediation_owner_user_id,
            "remediation_status": row.remediation_status,
            "remediation_notes": row.remediation_notes,
            "remediated_at": row.remediated_at,
        }
        for row in rows
    ]


@router.post("/webhooks/retry")
def retry_webhook_events(
    payload: WebhookRetryRequest,
    db: Session = Depends(get_db),
    role: str = Depends(current_role),
):
    _assert_admin_or_board(role)
    return run_retry_batch(
        db=db,
        vusd_adapter=retry_vusd_adapter,
        include_dead_letter=payload.include_dead_letter,
        limit=payload.limit,
        event_ids=payload.event_ids,
    )


@router.get("/webhooks/metrics")
def webhook_metrics(
    db: Session = Depends(get_db),
    role: str = Depends(current_role),
):
    _assert_admin_or_board(role)
    return webhook_queue_metrics(db)


@router.patch("/webhooks/events/{event_id}/remediation")
def update_webhook_remediation(
    event_id: str,
    payload: WebhookRemediationUpdate,
    db: Session = Depends(get_db),
    role: str = Depends(current_role),
):
    _assert_admin_or_board(role)
    event = db.scalar(select(WebhookEvent).where(WebhookEvent.id == event_id))
    if not event:
        raise HTTPException(status_code=404, detail="webhook event not found")

    if payload.owner_user_id is not None:
        event.remediation_owner_user_id = payload.owner_user_id or None
    if payload.remediation_notes is not None:
        event.remediation_notes = payload.remediation_notes[:4000] if payload.remediation_notes else None
    if payload.remediation_status is not None:
        event.remediation_status = payload.remediation_status
        if payload.remediation_status == "resolved":
            event.remediated_at = datetime.now(UTC)
        elif payload.remediation_status in {"none", "open", "in_progress"}:
            event.remediated_at = None

    event.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(event)
    return {
        "status": "updated",
        "event_id": event.id,
        "remediation_owner_user_id": event.remediation_owner_user_id,
        "remediation_status": event.remediation_status,
        "remediation_notes": event.remediation_notes,
        "remediated_at": event.remediated_at,
    }
