from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class DonationCategoryCode(str, enum.Enum):
    WIDOW = "WIDOW"
    ELDER = "ELDER"
    ORPHAN = "ORPHAN"
    MERCY = "MERCY"
    EARTH = "EARTH"


class VerificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class RequestStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PARTIALLY_FUNDED = "PARTIALLY_FUNDED"
    REJECTED = "REJECTED"


class DisbursementStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    CANCELED = "CANCELED"


class ComplianceStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    wallet_address: Mapped[str | None] = mapped_column(String(128), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="donor")
    kyc_level: Mapped[str] = mapped_column(String(50), default="none")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Donor(Base):
    __tablename__ = "donors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    donor_reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    communication_opt_in: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class DonationCategory(Base):
    __tablename__ = "donation_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[DonationCategoryCode] = mapped_column(Enum(DonationCategoryCode), unique=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    treasury_wallet: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class TreasuryAccount(Base):
    __tablename__ = "treasury_accounts"
    __table_args__ = (UniqueConstraint("category_id", name="uq_treasury_category"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id: Mapped[int] = mapped_column(ForeignKey("donation_categories.id"), nullable=False)
    steward_entity: Mapped[str] = mapped_column(String(128), default="Victory Foundation for Restoration")
    account_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    reserve_balance: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id: Mapped[int] = mapped_column(ForeignKey("donation_categories.id"), nullable=False)
    project_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    operating_entity: Mapped[str] = mapped_column(String(128), default="Sacred Earth Restoration Alliance")
    public_summary: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Donation(Base):
    __tablename__ = "donations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    donor_id: Mapped[str] = mapped_column(ForeignKey("donors.id"), nullable=False)
    donor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("donation_categories.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    compliance_status: Mapped[ComplianceStatus] = mapped_column(Enum(ComplianceStatus), default=ComplianceStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ImpactToken(Base):
    __tablename__ = "impact_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    donation_id: Mapped[str] = mapped_column(ForeignKey("donations.id"), nullable=False)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_contract: Mapped[str] = mapped_column(String(128), nullable=False)
    token_standard: Mapped[str] = mapped_column(String(16), default="ERC-1155")
    token_id_onchain: Mapped[str] = mapped_column(String(128), nullable=False)
    non_transferable: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_uri: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    minted_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id: Mapped[int] = mapped_column(ForeignKey("donation_categories.id"), nullable=False)
    reference_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    needs_assessment: Mapped[str] = mapped_column(Text, default="")
    private_profile_json: Mapped[dict] = mapped_column(JSON, default=dict)
    public_summary: Mapped[str] = mapped_column(Text, default="")
    operating_entity: Mapped[str] = mapped_column(String(128), default="Sacred Earth Restoration Alliance")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class BeneficiaryRequest(Base):
    __tablename__ = "beneficiary_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    beneficiary_id: Mapped[str] = mapped_column(ForeignKey("beneficiaries.id"), nullable=False)
    program_id: Mapped[str | None] = mapped_column(ForeignKey("programs.id"), nullable=True)
    requested_aid_amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    requested_currency: Mapped[str] = mapped_column(String(32), nullable=False)
    request_reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.SUBMITTED)
    approved_amount: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Disbursement(Base):
    __tablename__ = "disbursements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    beneficiary_request_id: Mapped[str] = mapped_column(ForeignKey("beneficiary_requests.id"), nullable=False)
    program_id: Mapped[str | None] = mapped_column(ForeignKey("programs.id"), nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("donation_categories.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(32), nullable=False)
    treasury_wallet: Mapped[str] = mapped_column(String(128), nullable=False)
    destination_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    disbursement_status: Mapped[DisbursementStatus] = mapped_column(Enum(DisbursementStatus), default=DisbursementStatus.QUEUED)
    tx_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    donation_id: Mapped[str | None] = mapped_column(ForeignKey("donations.id"), nullable=True)
    disbursement_id: Mapped[str | None] = mapped_column(ForeignKey("disbursements.id"), nullable=True)
    receipt_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    legal_text_version: Mapped[str] = mapped_column(String(32), default="v1")
    tax_receipt_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class DonorVote(Base):
    __tablename__ = "donor_votes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    voter_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    donor_id: Mapped[str | None] = mapped_column(ForeignKey("donors.id"), nullable=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("donation_categories.id"), nullable=False)
    token_weight: Mapped[float] = mapped_column(Float, nullable=False)
    signal: Mapped[str] = mapped_column(String(32), nullable=False)
    advisory_only: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class ComplianceReview(Base):
    __tablename__ = "compliance_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subject_type: Mapped[str] = mapped_column(String(32), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(64), nullable=False)
    review_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[ComplianceStatus] = mapped_column(Enum(ComplianceStatus), default=ComplianceStatus.PENDING)
    findings: Mapped[str] = mapped_column(Text, default="")
    reviewed_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("provider", "provider_event_id", name="uq_webhook_provider_event"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    delivery_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processing_status: Mapped[str] = mapped_column(String(32), default="received")
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dead_lettered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    remediation_owner_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    remediation_status: Mapped[str] = mapped_column(String(32), default="none")
    remediation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class PublicImpactUpdate(Base):
    __tablename__ = "public_impact_updates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    category_id: Mapped[int] = mapped_column(ForeignKey("donation_categories.id"), nullable=False)
    program_id: Mapped[str | None] = mapped_column(ForeignKey("programs.id"), nullable=True)
    disbursement_id: Mapped[str | None] = mapped_column(ForeignKey("disbursements.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    anonymized_summary: Mapped[str] = mapped_column(Text, nullable=False)
    media_links_json: Mapped[dict] = mapped_column(JSON, default=dict)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
