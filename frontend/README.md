# Frontend Structure (MVP)

Mobile-first page map:

- `LandingPage`: Choose who your gift protects
- `LandingPage`: Choose where compassion flows
- `DonatePage`: Wallet connect + payment flow + legal consent
- `PoolDetailPage`: Per-category pool details and active programs
- `ImpactDashboardPage`: Category treasury metrics
- `ReceiptWalletPage`: Donor impact token/receipt view
- `BeneficiaryPortalPage`: Request aid workflow
- `AdminReviewDashboardPage`: Review/compliance/disbursement controls
- `TreasuryDashboardPage`: Foundation treasury controls and flows
- `ComplianceDashboardPage`: Compliance review and legal controls
- `ImpactReportsPage`: Public anonymized reporting
- `TransparencyLedgerPage`: Public disbursement ledger

Core design intent:

- Warm, sacred, trustworthy, simple
- Category-first cards (Widows, Elderly, Orphans, Mercy, Earth Restoration)
- Clear source-to-beneficiary flow of funds
- Privacy-preserving impact summaries

Run locally:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Set API base URL (optional):
- `VITE_API_BASE_URL=http://localhost:8000`
- `VITE_ADMIN_TOKEN=admin-token` (for admin-protected dashboard routes)
- `VITE_WALLETCONNECT_PROJECT_ID=<walletconnect_project_id>` (enables WalletConnect)
