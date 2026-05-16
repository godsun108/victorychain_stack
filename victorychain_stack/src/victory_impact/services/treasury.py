from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import (
    Beneficiary,
    BeneficiaryRequest,
    Disbursement,
    Donation,
    DonationCategory,
    DonationCategoryCode,
    RequestStatus,
)


def treasury_stats(db: Session, category_code: DonationCategoryCode) -> dict:
    category = db.scalar(select(DonationCategory).where(DonationCategory.code == category_code))
    if not category:
        raise ValueError("category not found")

    total_received = db.scalar(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(Donation.category_id == category.id)
    )
    total_distributed = db.scalar(
        select(func.coalesce(func.sum(Disbursement.amount), 0)).where(Disbursement.category_id == category.id)
    )
    beneficiaries_supported = db.scalar(
        select(func.count(func.distinct(Beneficiary.id))).where(Beneficiary.category_id == category.id)
    )
    pending_requests = db.scalar(
        select(func.count())
        .select_from(BeneficiaryRequest)
        .join(Beneficiary, Beneficiary.id == BeneficiaryRequest.beneficiary_id)
        .where(
            Beneficiary.category_id == category.id,
            BeneficiaryRequest.status == RequestStatus.SUBMITTED,
        )
    )

    total_received_dec = Decimal(str(total_received or 0))
    total_distributed_dec = Decimal(str(total_distributed or 0))

    return {
        "category": category_code,
        "total_received": total_received_dec,
        "total_distributed": total_distributed_dec,
        "reserve_balance": total_received_dec - total_distributed_dec,
        "beneficiaries_supported": int(beneficiaries_supported or 0),
        "pending_requests": int(pending_requests or 0),
    }
