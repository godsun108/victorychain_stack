from decimal import Decimal

from src.victory_impact.db import Base, SessionLocal, engine
from src.victory_impact.models import DonationCategoryCode
from src.victory_impact.services.donations import create_donation_and_token, ensure_default_categories, get_or_create_donor


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_default_categories(db)
        donor = get_or_create_donor(db, "demo.donor@victorychain.org", full_name="Demo Donor")

        create_donation_and_token(
            db,
            donor,
            DonationCategoryCode.WIDOW,
            Decimal("150.00"),
            "USD",
            "card",
            "demo-card-001",
            None,
            "Emergency rent support",
            "W-DEMO-1",
        )
        create_donation_and_token(
            db,
            donor,
            DonationCategoryCode.ORPHAN,
            Decimal("250.00"),
            "USD",
            "vusd",
            "demo-vusd-001",
            "0xdemotx",
            "School kit aid",
            "O-DEMO-1",
        )
        create_donation_and_token(
            db,
            donor,
            DonationCategoryCode.EARTH,
            Decimal("500.00"),
            "USD",
            "bank",
            "demo-earth-001",
            None,
            "Mangrove and soil regeneration program",
            "E-DEMO-1",
        )
        print("Demo data seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
