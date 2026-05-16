from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from .models import DonationCategoryCode


class DonorCreate(BaseModel):
    email: str
    wallet_address: str | None = None
    full_name: str | None = None


class DonationCreate(BaseModel):
    donor_email: str
    category: DonationCategoryCode
    payment_method: Literal["card", "bank", "crypto", "vusd", "wallet"]
    currency: str = "USD"
    amount: Decimal = Field(gt=0)
    payment_reference: str | None = None
    tx_hash: str | None = None
    impact_notes: str = ""
    project_id: str = "GENERAL"


class DonationResponse(BaseModel):
    donation_id: str
    token_id: str
    receipt_id: str
    category: DonationCategoryCode
    treasury_wallet: str
    compliance_status: str
    non_investment_disclaimer: str


class BeneficiaryCreate(BaseModel):
    category: DonationCategoryCode
    reference_code: str
    needs_assessment: str
    public_summary: str
    private_profile_json: dict


class BeneficiaryRequestCreate(BaseModel):
    beneficiary_id: str
    program_id: str | None = None
    requested_aid_amount: Decimal = Field(gt=0)
    requested_currency: str = "USD"
    request_reason: str


class DisbursementCreate(BaseModel):
    beneficiary_request_id: str
    program_id: str | None = None
    amount: Decimal = Field(gt=0)
    currency: str = "USD"
    destination_reference: str


class VoteCreate(BaseModel):
    voter_email: str
    project_id: str
    category: DonationCategoryCode
    signal: Literal["support", "defer", "decline"]


class VoteResponse(BaseModel):
    vote_id: str
    token_weight: float
    advisory_only: bool


class TreasuryStats(BaseModel):
    category: DonationCategoryCode
    total_received: Decimal
    total_distributed: Decimal
    reserve_balance: Decimal
    beneficiaries_supported: int
    pending_requests: int


class PublicDisbursement(BaseModel):
    disbursement_id: str
    category: DonationCategoryCode
    amount: Decimal
    currency: str
    tx_hash: str | None = None
    created_at: datetime


class PublicImpactUpdateItem(BaseModel):
    update_id: str
    category: DonationCategoryCode
    title: str
    anonymized_summary: str
    program_id: str | None = None
    disbursement_id: str | None = None
    published_at: datetime


class PaymentIntentCreate(BaseModel):
    donor_email: str
    category: DonationCategoryCode
    payment_method: Literal["card", "bank"]
    amount: Decimal = Field(gt=0)
    currency: str = "USD"


class PaymentIntentResponse(BaseModel):
    intent_id: str
    provider: str
    status: str
    checkout_url: str | None = None


class PaymentCapturePayload(BaseModel):
    donor_email: str
    category: DonationCategoryCode
    project_id: str = "GENERAL"
    impact_notes: str = ""
    amount: Decimal = Field(gt=0)
    currency: str = "USD"
    payment_reference: str
    tx_hash: str | None = None


class RuntimePolicyUpdate(BaseModel):
    tax_receipts_enabled: bool | None = None
    enforce_ofac_screening: bool | None = None
    enforce_kyc_kyb_large_threshold: bool | None = None


class WebhookRetryRequest(BaseModel):
    event_ids: list[str] | None = None
    include_dead_letter: bool = False
    limit: int = 50


class WebhookRemediationUpdate(BaseModel):
    owner_user_id: str | None = None
    remediation_status: Literal["none", "open", "in_progress", "resolved"] | None = None
    remediation_notes: str | None = None
