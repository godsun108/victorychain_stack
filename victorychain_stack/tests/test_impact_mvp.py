from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.victory_impact.models import Base, ComplianceStatus, DonationCategoryCode
from src.victory_impact.services.donations import (
    create_donation_and_token,
    ensure_default_categories,
    get_or_create_donor,
)
from src.victory_impact.services.governance import cast_vote
from src.victory_impact.services.treasury import treasury_stats


def build_db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    return factory()


def test_donation_issues_token_and_receipt():
    db = build_db()
    ensure_default_categories(db)
    donor = get_or_create_donor(db, "donor@example.org")

    donation, token, receipt, category = create_donation_and_token(
        db=db,
        donor=donor,
        category_code=DonationCategoryCode.WIDOW,
        amount=Decimal("150.00"),
        currency="USD",
        payment_method="card",
        payment_reference="pi_123",
        tx_hash=None,
        impact_notes="Monthly support",
        project_id="W-001",
    )

    assert donation.id
    assert token.non_transferable is True
    assert token.metadata_json["donation_category"] == "WIDOW"
    assert receipt.receipt_number.startswith("VC-IMPACT-")
    assert category.code == DonationCategoryCode.WIDOW


def test_large_donation_flags_compliance_review():
    db = build_db()
    ensure_default_categories(db)
    donor = get_or_create_donor(db, "large@example.org")

    donation, _, _, _ = create_donation_and_token(
        db=db,
        donor=donor,
        category_code=DonationCategoryCode.MERCY,
        amount=Decimal("25000.00"),
        currency="USD",
        payment_method="bank",
        payment_reference="wire-1",
        tx_hash=None,
        impact_notes="Emergency reserve",
        project_id="M-RESERVE",
    )

    assert donation.compliance_status == ComplianceStatus.NEEDS_REVIEW


def test_vote_weight_and_treasury_stats():
    db = build_db()
    ensure_default_categories(db)
    donor = get_or_create_donor(db, "voter@example.org")

    create_donation_and_token(
        db=db,
        donor=donor,
        category_code=DonationCategoryCode.ORPHAN,
        amount=Decimal("300.00"),
        currency="USD",
        payment_method="crypto",
        payment_reference=None,
        tx_hash="0xabc",
        impact_notes="School supplies",
        project_id="O-SCHOOL",
    )

    vote = cast_vote(db, donor, DonationCategoryCode.ORPHAN, "O-SCHOOL", "support")
    stats = treasury_stats(db, DonationCategoryCode.ORPHAN)

    assert vote.token_weight == 300.0
    assert stats["total_received"] == Decimal("300.00")


def test_earth_restoration_category_supported():
    db = build_db()
    ensure_default_categories(db)
    donor = get_or_create_donor(db, "earth@example.org")
    donation, token, _, category = create_donation_and_token(
        db=db,
        donor=donor,
        category_code=DonationCategoryCode.EARTH,
        amount=Decimal("1000.00"),
        currency="USD",
        payment_method="bank",
        payment_reference="earth-wire-1",
        tx_hash=None,
        impact_notes="Watershed and reforestation support",
        project_id="EARTH-1",
    )
    assert donation.id
    assert category.code == DonationCategoryCode.EARTH
    assert token.token_id_onchain == "5"
