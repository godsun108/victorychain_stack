from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Donation, DonationCategory, DonationCategoryCode, Donor, DonorVote, User


def donor_weight_for_category(db: Session, donor: User, category: DonationCategory) -> float:
    total = db.scalar(
        select(func.coalesce(func.sum(Donation.amount), 0)).where(
            Donation.donor_user_id == donor.id,
            Donation.category_id == category.id,
        )
    )
    return float(total or 0.0)


def cast_vote(db: Session, donor: User, category_code: DonationCategoryCode, project_id: str, signal: str) -> DonorVote:
    category = db.scalar(select(DonationCategory).where(DonationCategory.code == category_code))
    if not category:
        raise ValueError("Unknown category")
    donor_profile = db.scalar(select(Donor).where(Donor.user_id == donor.id))

    vote = DonorVote(
        voter_user_id=donor.id,
        donor_id=donor_profile.id if donor_profile else None,
        category_id=category.id,
        project_id=project_id,
        signal=signal,
        token_weight=donor_weight_for_category(db, donor, category),
        advisory_only=True,
    )
    db.add(vote)
    db.commit()
    db.refresh(vote)
    return vote
