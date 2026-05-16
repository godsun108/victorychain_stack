from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..compliance import NON_INVESTMENT_DISCLAIMER
from ..db import get_db
from ..schemas import DonationCreate, DonationResponse
from ..services.donations import create_donation_and_token, ensure_default_categories, get_or_create_donor

router = APIRouter(prefix="/donors", tags=["donors"])


@router.post("/donate", response_model=DonationResponse)
def donate(payload: DonationCreate, db: Session = Depends(get_db)):
    ensure_default_categories(db)
    donor = get_or_create_donor(db, email=payload.donor_email)
    try:
        donation, token, receipt, category = create_donation_and_token(
            db=db,
            donor=donor,
            category_code=payload.category,
            amount=payload.amount,
            currency=payload.currency,
            payment_method=payload.payment_method,
            payment_reference=payload.payment_reference,
            tx_hash=payload.tx_hash,
            impact_notes=payload.impact_notes,
            project_id=payload.project_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DonationResponse(
        donation_id=donation.id,
        token_id=token.id,
        receipt_id=receipt.receipt_number,
        category=payload.category,
        treasury_wallet=category.treasury_wallet,
        compliance_status=donation.compliance_status.value,
        non_investment_disclaimer=NON_INVESTMENT_DISCLAIMER,
    )
