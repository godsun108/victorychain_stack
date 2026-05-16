from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..compliance import NON_INVESTMENT_DISCLAIMER, donation_compliance_status
from ..config import settings
from ..models import (
    AuditLog,
    ComplianceReview,
    ComplianceStatus,
    Donation,
    DonationCategory,
    DonationCategoryCode,
    Donor,
    ImpactToken,
    Receipt,
    TreasuryAccount,
    User,
)
from ..policies import runtime_policies


TOKEN_ID_BY_CATEGORY = {
    DonationCategoryCode.WIDOW: "1",
    DonationCategoryCode.ELDER: "2",
    DonationCategoryCode.ORPHAN: "3",
    DonationCategoryCode.MERCY: "4",
    DonationCategoryCode.EARTH: "5",
}


def ensure_default_categories(db: Session) -> None:
    categories = {
        DonationCategoryCode.WIDOW: ("Widows", settings.treasury_widow_wallet),
        DonationCategoryCode.ELDER: ("Elderly", settings.treasury_elder_wallet),
        DonationCategoryCode.ORPHAN: ("Orphans", settings.treasury_orphan_wallet),
        DonationCategoryCode.MERCY: ("General Mercy Fund", settings.treasury_mercy_wallet),
        DonationCategoryCode.EARTH: ("Earth Restoration Fund", settings.treasury_earth_wallet),
    }
    for code, (name, wallet) in categories.items():
        category = db.scalar(select(DonationCategory).where(DonationCategory.code == code))
        if not category:
            category = DonationCategory(code=code, display_name=name, treasury_wallet=wallet, is_active=True)
            db.add(category)
            db.flush()
        treasury = db.scalar(select(TreasuryAccount).where(TreasuryAccount.category_id == category.id))
        if not treasury:
            db.add(
                TreasuryAccount(
                    category_id=category.id,
                    account_reference=wallet,
                    steward_entity="Victory Foundation for Restoration",
                )
            )
    db.commit()


def get_or_create_donor(db: Session, email: str, wallet_address: str | None = None, full_name: str | None = None) -> User:
    donor_user = db.scalar(select(User).where(User.email == email))
    if not donor_user:
        donor_user = User(email=email, wallet_address=wallet_address, full_name=full_name, role="donor")
        db.add(donor_user)
        db.flush()

    donor_profile = db.scalar(select(Donor).where(Donor.user_id == donor_user.id))
    if not donor_profile:
        donor_count = (db.scalar(select(func.count()).select_from(Donor)) or 0) + 1
        donor_profile = Donor(user_id=donor_user.id, donor_reference=f"DONOR-{donor_count:08d}")
        db.add(donor_profile)

    db.commit()
    db.refresh(donor_user)
    return donor_user


def get_donor_profile(db: Session, donor_user_id: str) -> Donor:
    profile = db.scalar(select(Donor).where(Donor.user_id == donor_user_id))
    if not profile:
        raise ValueError("Donor profile not found")
    return profile


def _next_receipt_number(db: Session) -> str:
    count = db.scalar(select(func.count()).select_from(Receipt)) or 0
    return f"VC-IMPACT-{count + 1:08d}"


def create_donation_and_token(
    db: Session,
    donor: User,
    category_code: DonationCategoryCode,
    amount: Decimal,
    currency: str,
    payment_method: str,
    payment_reference: str | None,
    tx_hash: str | None,
    impact_notes: str,
    project_id: str,
) -> tuple[Donation, ImpactToken, Receipt, DonationCategory]:
    category = db.scalar(select(DonationCategory).where(DonationCategory.code == category_code))
    if not category:
        raise ValueError(f"Unknown category: {category_code}")

    if payment_reference:
        existing = db.scalar(
            select(Donation).where(
                Donation.payment_reference == payment_reference,
                Donation.payment_method == payment_method,
            )
        )
        if existing:
            existing_token = db.scalar(select(ImpactToken).where(ImpactToken.donation_id == existing.id))
            existing_receipt = db.scalar(select(Receipt).where(Receipt.donation_id == existing.id))
            return existing, existing_token, existing_receipt, category

    donor_profile = get_donor_profile(db, donor.id)
    compliance_status = donation_compliance_status(amount)
    donation = Donation(
        donor_id=donor_profile.id,
        donor_user_id=donor.id,
        category_id=category.id,
        amount=amount,
        currency=currency,
        payment_method=payment_method,
        payment_reference=payment_reference,
        tx_hash=tx_hash,
        compliance_status=compliance_status,
    )
    db.add(donation)
    db.flush()

    receipt_number = _next_receipt_number(db)
    receipt = Receipt(
        donation_id=donation.id,
        receipt_number=receipt_number,
        tax_receipt_eligible=runtime_policies.tax_receipts_enabled,
    )
    db.add(receipt)

    metadata = {
        "donation_category": category.code.value,
        "timestamp": datetime.now(UTC).isoformat(),
        "receipt_id": receipt_number,
        "project_id": project_id,
        "impact_notes": impact_notes,
        "anonymized_impact_summary": "Pending program report.",
        "disclaimer": NON_INVESTMENT_DISCLAIMER,
        "steward_entity": "Victory Foundation for Restoration",
        "operating_entity": "Sacred Earth Restoration Alliance",
    }
    token = ImpactToken(
        donation_id=donation.id,
        owner_user_id=donor.id,
        token_contract="ImpactReceipt1155",
        token_standard="ERC-1155",
        token_id_onchain=TOKEN_ID_BY_CATEGORY[category.code],
        non_transferable=True,
        metadata_json=metadata,
    )
    db.add(token)

    if compliance_status != ComplianceStatus.APPROVED:
        db.add(
            ComplianceReview(
                subject_type="donation",
                subject_id=donation.id,
                review_type="KYC_KYB_THRESHOLD",
                status=ComplianceStatus.NEEDS_REVIEW,
                findings="Donation exceeds threshold and requires manual compliance review.",
            )
        )

    db.add(
        AuditLog(
            actor_user_id=donor.id,
            action="DONATION_CREATED",
            entity_type="donation",
            entity_id=donation.id,
            metadata_json={
                "category": category.code.value,
                "amount": str(amount),
                "currency": currency,
                "payment_method": payment_method,
                "steward_entity": "Victory Foundation for Restoration",
                "operating_entity": "Sacred Earth Restoration Alliance",
            },
        )
    )

    db.commit()
    db.refresh(donation)
    db.refresh(token)
    db.refresh(receipt)
    return donation, token, receipt, category
