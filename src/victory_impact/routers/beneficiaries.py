from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import (
    AuditLog,
    Beneficiary,
    BeneficiaryRequest,
    Disbursement,
    DisbursementStatus,
    DonationCategory,
    Program,
    PublicImpactUpdate,
    Receipt,
    RequestStatus,
)
from ..schemas import BeneficiaryCreate, BeneficiaryRequestCreate, DisbursementCreate

router = APIRouter(prefix="/beneficiaries", tags=["beneficiaries"])


@router.post("", response_model=dict)
def create_beneficiary(payload: BeneficiaryCreate, db: Session = Depends(get_db)):
    category = db.scalar(select(DonationCategory).where(DonationCategory.code == payload.category))
    if not category:
        raise HTTPException(status_code=400, detail="Unknown donation category")

    beneficiary = Beneficiary(
        category_id=category.id,
        reference_code=payload.reference_code,
        needs_assessment=payload.needs_assessment,
        public_summary=payload.public_summary,
        private_profile_json=payload.private_profile_json,
    )
    db.add(beneficiary)
    db.add(
        AuditLog(
            action="BENEFICIARY_CREATED",
            entity_type="beneficiary",
            entity_id=beneficiary.id,
            metadata_json={"category": payload.category.value, "reference_code": payload.reference_code},
        )
    )
    db.commit()
    db.refresh(beneficiary)
    return {"beneficiary_id": beneficiary.id, "verification_status": beneficiary.verification_status.value}


@router.post("/requests", response_model=dict)
def create_beneficiary_request(payload: BeneficiaryRequestCreate, db: Session = Depends(get_db)):
    beneficiary = db.scalar(select(Beneficiary).where(Beneficiary.id == payload.beneficiary_id))
    if not beneficiary:
        raise HTTPException(status_code=404, detail="Beneficiary not found")

    request = BeneficiaryRequest(
        beneficiary_id=beneficiary.id,
        program_id=payload.program_id,
        requested_aid_amount=payload.requested_aid_amount,
        requested_currency=payload.requested_currency,
        request_reason=payload.request_reason,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return {"request_id": request.id, "status": request.status.value}


@router.post("/disbursements", response_model=dict)
def create_disbursement(payload: DisbursementCreate, db: Session = Depends(get_db)):
    request = db.scalar(select(BeneficiaryRequest).where(BeneficiaryRequest.id == payload.beneficiary_request_id))
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    beneficiary = db.scalar(select(Beneficiary).where(Beneficiary.id == request.beneficiary_id))
    category = db.scalar(select(DonationCategory).where(DonationCategory.id == beneficiary.category_id))

    request.status = RequestStatus.APPROVED
    request.approved_amount = payload.amount

    disbursement = Disbursement(
        beneficiary_request_id=request.id,
        program_id=payload.program_id or request.program_id,
        category_id=category.id,
        amount=payload.amount,
        currency=payload.currency,
        treasury_wallet=category.treasury_wallet,
        destination_reference=payload.destination_reference,
        disbursement_status=DisbursementStatus.QUEUED,
    )
    db.add(disbursement)
    db.flush()

    receipt = Receipt(
        disbursement_id=disbursement.id,
        receipt_number=f"VC-DISP-{disbursement.id[:8].upper()}",
        tax_receipt_eligible=False,
    )
    db.add(receipt)

    program = None
    if disbursement.program_id:
        program = db.scalar(select(Program).where(Program.id == disbursement.program_id))

    summary = (
        f"Program {program.project_id} disbursed {payload.amount} {payload.currency} to approved recipients."
        if program
        else f"Disbursed {payload.amount} {payload.currency} to an approved {category.display_name.lower()} request."
    )
    db.add(
        PublicImpactUpdate(
            category_id=category.id,
            program_id=disbursement.program_id,
            disbursement_id=disbursement.id,
            title=f"{category.display_name} Disbursement Update",
            anonymized_summary=summary,
            media_links_json={},
        )
    )

    db.add(
        AuditLog(
            action="DISBURSEMENT_CREATED",
            entity_type="disbursement",
            entity_id=disbursement.id,
            metadata_json={
                "amount": str(payload.amount),
                "currency": payload.currency,
                "destination_reference": payload.destination_reference,
            },
        )
    )

    db.commit()
    db.refresh(disbursement)
    db.refresh(receipt)
    return {
        "disbursement_id": disbursement.id,
        "status": disbursement.disbursement_status.value,
        "receipt_id": receipt.receipt_number,
    }
