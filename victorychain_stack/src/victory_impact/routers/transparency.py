from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Disbursement, DonationCategory, PublicImpactUpdate
from ..schemas import PublicDisbursement, PublicImpactUpdateItem
from ..services.audit_proofs import build_audit_proof

router = APIRouter(prefix="/transparency", tags=["transparency"])


@router.get("/ledger", response_model=list[PublicDisbursement])
def transparency_ledger(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Disbursement, DonationCategory)
        .join(DonationCategory, DonationCategory.id == Disbursement.category_id)
        .order_by(Disbursement.created_at.desc())
        .limit(200)
    ).all()

    return [
        PublicDisbursement(
            disbursement_id=d.id,
            category=c.code,
            amount=d.amount,
            currency=d.currency,
            tx_hash=d.tx_hash,
            created_at=d.created_at,
        )
        for d, c in rows
    ]


@router.get("/impact-updates", response_model=list[PublicImpactUpdateItem])
def impact_updates(db: Session = Depends(get_db)):
    rows = db.execute(
        select(PublicImpactUpdate, DonationCategory)
        .join(DonationCategory, DonationCategory.id == PublicImpactUpdate.category_id)
        .order_by(PublicImpactUpdate.published_at.desc())
        .limit(200)
    ).all()
    return [
        PublicImpactUpdateItem(
            update_id=update.id,
            category=category.code,
            title=update.title,
            anonymized_summary=update.anonymized_summary,
            program_id=update.program_id,
            disbursement_id=update.disbursement_id,
            published_at=update.published_at,
        )
        for update, category in rows
    ]


@router.get("/audit-proof/{entity_type}/{entity_id}")
def public_audit_proof(entity_type: str, entity_id: str, db: Session = Depends(get_db)):
    try:
        return build_audit_proof(db, entity_type, entity_id, settings.audit_proof_secret)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
