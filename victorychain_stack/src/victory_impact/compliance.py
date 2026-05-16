from decimal import Decimal

from .config import settings
from .models import ComplianceStatus


NON_INVESTMENT_DISCLAIMER = (
    "Impact tokens are donation receipts and governance signals only. "
    "They are not investment assets and do not provide profit, dividends, "
    "appreciation, or guaranteed resale value."
)


def donation_compliance_status(amount: Decimal) -> ComplianceStatus:
    if amount >= Decimal(str(settings.donation_large_amount_usd_threshold)):
        return ComplianceStatus.NEEDS_REVIEW
    return ComplianceStatus.APPROVED


def kyc_required_for_large_donation(amount: Decimal) -> bool:
    return amount >= Decimal(str(settings.donation_large_amount_usd_threshold))


def ofac_screening_placeholder(subject: str) -> dict:
    return {
        "subject": subject,
        "status": "placeholder",
        "notes": "Integrate OFAC/sanctions screening provider before production payouts.",
    }
