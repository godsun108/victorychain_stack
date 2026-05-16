from dataclasses import dataclass

from .config import settings


@dataclass
class RuntimePolicies:
    tax_receipts_enabled: bool
    enforce_ofac_screening: bool
    enforce_kyc_kyb_large_threshold: bool


runtime_policies = RuntimePolicies(
    tax_receipts_enabled=settings.legal_review_tax_receipts_enabled,
    enforce_ofac_screening=False,
    enforce_kyc_kyb_large_threshold=True,
)
