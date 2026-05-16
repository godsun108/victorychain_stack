# Victory Foundation for Restoration + Sacred Earth Restoration Alliance

## 1) Full System Architecture

Mission pools:
- Widows
- Elderly
- Orphans
- General Mercy Fund
- Earth Restoration Fund

Entity model:
- Victory Foundation for Restoration: treasury steward, grant allocator, oversight body.
- Sacred Earth Restoration Alliance: operating arm, beneficiary/program verification, delivery, reporting.

Architecture layers:
- Frontend: donor/admin/public experiences.
- API: donation intake, compliance placeholders, approvals, voting, reporting.
- Data: auditable relational records + anonymized impact updates.
- Smart contracts: impact receipt minting, treasury routing, disbursement events, pause controls.

## 2) Database Schema

Implemented table set:
- users
- donors
- donations
- donation_categories
- impact_tokens
- beneficiaries
- beneficiary_requests
- programs
- disbursements
- receipts
- donor_votes
- treasury_accounts
- compliance_reviews
- audit_logs
- public_impact_updates

References:
- `src/victory_impact/models.py`
- `db/schema.sql`

## 3) Smart Contract Stubs

- `contracts/ImpactReceipt1155.sol`
- `contracts/DonationReceiptNFT.sol`
- `contracts/TreasuryRouter.sol`
- `contracts/BeneficiaryDisbursement.sol`

Implemented controls:
- ERC-1155 impact receipt model with non-transfer behavior
- Optional ERC-721 receipt mode with transfer restriction toggle
- Category-based treasury routing including EARTH pool
- RBAC and pause/emergency controls
- Donation/disbursement event emission
- Metadata support for category/timestamp/receipt/project/anonymized impact summary

## 4) API Route Map

Donor and payments:
- `POST /donors/donate`
- `POST /payments/intent`
- `POST /payments/capture`

Webhooks and settlement:
- `POST /webhooks/stripe`
- `POST /webhooks/vusd`
- `POST /webhooks/crypto/confirm`

Beneficiary and disbursement:
- `POST /beneficiaries`
- `POST /beneficiaries/requests`
- `POST /beneficiaries/disbursements`

Governance:
- `POST /governance/vote`

Admin:
- `GET /admin/treasury`
- `GET /admin/policies`
- `PATCH /admin/policies`
- `PATCH /admin/categories/{category_code}/treasury-wallet`
- `GET /admin/compliance/reviews`

Public transparency:
- `GET /transparency/ledger`
- `GET /transparency/impact-updates`

## 5) Frontend Component Plan

Core components:
- `CategoryCard`

Pages:
- Landing page: Choose where compassion flows
- Donate page
- Pool detail pages
- Donor wallet/receipt page
- Public impact ledger
- Beneficiary application page
- Admin dashboard
- Treasury dashboard
- Compliance dashboard
- Impact reports page

References:
- `frontend/src/components/CategoryCard.tsx`
- `frontend/src/pages/*.tsx`

## 6) Admin Dashboard Design

Panels:
- Treasury totals by pool: received, distributed, reserve, pending requests
- Compliance queue: KYC/KYB threshold reviews and OFAC placeholders
- Policy controls: tax receipt enablement and screening toggles
- Treasury account controls: update pool wallet/account routing
- Disbursement controls: approval + queued execution trail

## 7) Compliance Checklist

- Impact-token legal language included (receipt-only)
- Non-investment language included (no yield/profit/dividend/appreciation/resale promises)
- Advisory-only donor voting encoded
- KYC/KYB threshold placeholder and review workflow
- OFAC/sanctions screening placeholder
- Charitable solicitation placeholder by jurisdiction
- Tax receipt gating by legal review toggle
- Privacy split between private beneficiary data and public summaries

## 8) Security Model

- Role-based access for donor/admin/board/compliance
- Non-transferable receipt design by default
- Audit logs for donation/disbursement/admin actions
- Idempotent payment capture by payment reference
- Pause/emergency controls on treasury/disbursement/token contracts
- Principle of least privilege and segregated entity responsibility

## 9) Deployment Plan

1. Configure `.env` and treasury account references.
2. Launch Postgres and API (`docker compose up -d --build`).
3. Initialize categories/treasury accounts on API startup.
4. Deploy contracts to target chain and map addresses into config.
5. Connect payment providers (card/bank/crypto/vUSD adapters).
6. Enable monitoring and backup routines.
7. Run compliance/legal review before production receipts.

## 10) MVP Build Sequence

1. Data model and schema finalization.
2. Donation routing + receipt token issuance.
3. Beneficiary/program/disbursement workflow.
4. Transparency and impact reporting endpoints.
5. Admin and compliance controls.
6. Frontend pages and mobile-first UX integration.
7. Contract deployment and API/contract wiring.
8. End-to-end UAT with legal/compliance signoff.

## 11) Test Suite Plan

Unit tests:
- donation creation and routing
- Earth category support
- idempotent payment capture
- governance advisory weight

API tests:
- donor donation flow
- payment intent/capture
- beneficiary request/disbursement
- transparency ledgers
- admin policy updates with role checks

Contract tests:
- soulbound transfer restrictions
- treasury category routing events
- disbursement events and pause gates

Security/compliance tests:
- role authorization boundaries
- webhook verification stubs
- data privacy exposure checks

Ops tests:
- compose startup, health checks, reseed reproducibility
- restore and audit-log consistency drills
