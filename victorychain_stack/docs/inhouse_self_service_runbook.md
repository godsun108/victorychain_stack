# In-House Self-Service Runbook

## 1. Bootstrap (Local)

```bash
./scripts/self_service_bootstrap.sh
source .venv/bin/activate
uvicorn src.victory_impact.main:app --reload
```

API docs: `http://localhost:8000/docs`

## 2. Bootstrap (Docker)

```bash
cp .env.example .env
make up
make logs
```

## 3. Admin Access Tokens (Header)

Use `x-api-token` on admin endpoints:

- `admin-token`
- `board-token`
- `compliance-token`

## 4. Core Self-Service Workflows

1. Create card/bank intent: `POST /payments/intent`
2. Capture settled donation: `POST /payments/capture`
3. Crypto settlement check: `POST /webhooks/crypto/confirm`
4. vUSD event ingest: `POST /webhooks/vusd`
5. Review treasury state: `GET /admin/treasury`
6. Update runtime policies: `PATCH /admin/policies`
7. Update category treasury wallet: `PATCH /admin/categories/{category_code}/treasury-wallet`

## 5. OpenAPI Example Payloads

### Create Payment Intent

`POST /payments/intent`

```json
{
  "donor_email": "donor@example.org",
  "category": "WIDOW",
  "payment_method": "card",
  "amount": 125.5,
  "currency": "USD"
}
```

### Capture Donation

`POST /payments/capture`

```json
{
  "donor_email": "donor@example.org",
  "category": "WIDOW",
  "project_id": "W-HELP-2026",
  "impact_notes": "Housing and food support",
  "amount": 125.5,
  "currency": "USD",
  "payment_reference": "inhouse-card-20260516094500"
}
```

### Direct Crypto Donation

`POST /donors/donate`

```json
{
  "donor_email": "donor@example.org",
  "category": "ORPHAN",
  "payment_method": "crypto",
  "currency": "vUSD",
  "amount": 200,
  "tx_hash": "0xabc123",
  "impact_notes": "School kits",
  "project_id": "O-SCHOOL-2026"
}
```

### Earth Restoration Donation

`POST /donors/donate`

```json
{
  "donor_email": "earth-donor@example.org",
  "category": "EARTH",
  "payment_method": "bank",
  "currency": "USD",
  "amount": 1000,
  "impact_notes": "Reforestation and watershed restoration",
  "project_id": "E-RESTORE-2026"
}
```

### Advisory Vote

`POST /governance/vote`

```json
{
  "voter_email": "donor@example.org",
  "project_id": "O-SCHOOL-2026",
  "category": "ORPHAN",
  "signal": "support"
}
```

### Runtime Policy Update

`PATCH /admin/policies`

```json
{
  "tax_receipts_enabled": true,
  "enforce_ofac_screening": true,
  "enforce_kyc_kyb_large_threshold": true
}
```

## 6. Reproducibility Checklist

- Use `.env.example` as baseline.
- Run `make setup && make test` before deployment.
- Run `make up` for deterministic local stack.
- Run `scripts/reseed_demo_data.py` for deterministic sample data.
- Track contract + API versions in release notes.

## 7. Webhook and Chain Verification

- Stripe webhook endpoint verifies `Stripe-Signature` using `STRIPE_WEBHOOK_SECRET`.
- Crypto confirmation endpoint verifies receipt and block confirmations through `EVM_RPC_URL`.
- vUSD webhook verifies tx confirmation and optional contract-address match against `VUSD_CONTRACT_ADDRESS`.
