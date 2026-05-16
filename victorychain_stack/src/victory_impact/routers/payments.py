from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import DonationResponse, PaymentCapturePayload, PaymentIntentCreate, PaymentIntentResponse
from ..services.donations import create_donation_and_token, ensure_default_categories, get_or_create_donor
from ..services.payment_adapters import InHouseCardBankAdapter

router = APIRouter(prefix="/payments", tags=["payments"])

adapter = InHouseCardBankAdapter()


@router.post("/intent", response_model=PaymentIntentResponse)
def create_payment_intent(payload: PaymentIntentCreate, db: Session = Depends(get_db)):
    ensure_default_categories(db)
    intent = adapter.create_intent(payload.payment_method, payload.amount, payload.currency, payload.donor_email)
    return PaymentIntentResponse(
        intent_id=intent.intent_id,
        provider=intent.provider,
        status=intent.status,
        checkout_url=intent.checkout_url,
    )


@router.post("/capture", response_model=DonationResponse)
def capture_payment(payload: PaymentCapturePayload, db: Session = Depends(get_db)):
    ensure_default_categories(db)
    donor = get_or_create_donor(db, payload.donor_email)

    try:
        donation, token, receipt, category = create_donation_and_token(
            db=db,
            donor=donor,
            category_code=payload.category,
            amount=payload.amount,
            currency=payload.currency,
            payment_method="card_or_bank",
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
        non_investment_disclaimer=token.metadata_json["disclaimer"],
    )
