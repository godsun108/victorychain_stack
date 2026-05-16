# VictoryChain Nonprofit Impact-Token MVP

Production-oriented MVP scaffold for a nonprofit donation-token platform where donors support:

- Widows
- Elderly
- Orphans
- General Mercy Fund
- Earth Restoration Fund

Entity structure:
- Victory Foundation for Restoration: foundation oversight, treasury stewardship, grant allocation.
- Sacred Earth Restoration Alliance: operating arm for verification, delivery, and reporting.

Impact tokens are donation receipts and governance signals only. They are non-investment records and do not represent profit rights.

## Quick Start

```bash
pip install -r requirements.txt
uvicorn src.victory_impact.main:app --reload
```

## Deliverables Included

- System architecture: `docs/nonprofit_impact_mvp.md`
- Database schema: `db/schema.sql`
- Smart contract stubs: `contracts/*.sol`
- API routes: `src/victory_impact/routers/*.py`
- Frontend structure: `frontend/src/pages/*.tsx`
- Admin dashboard structure: `/admin/treasury` route and frontend admin page
- Security model: `docs/nonprofit_impact_mvp.md` + `src/victory_impact/security.py`
- Compliance checklist: `docs/nonprofit_impact_mvp.md`
- Deployment plan: `docs/nonprofit_impact_mvp.md`
- Test plan: `docs/nonprofit_impact_mvp.md`

## Core API Endpoints

- `POST /donors/donate`
- `POST /beneficiaries`
- `POST /beneficiaries/requests`
- `POST /beneficiaries/disbursements`
- `POST /governance/vote`
- `GET /admin/treasury`
- `GET /transparency/ledger`
- `GET /transparency/impact-updates`

## In-House Self-Service Ops

- Local bootstrap: `./scripts/self_service_bootstrap.sh`
- Docker stack: `make up`
- Sovereign in-house stack: `docker compose -f compose.inhouse.yml up -d --build`
- API docs: `http://localhost:8000/docs`
- Runbook: `docs/inhouse_self_service_runbook.md`
- Sovereign plan: `docs/sovereign_inhouse_plan.md`
- Frontend app: `frontend/` (`npm install && npm run dev`)
- Webhook retry worker logs: `make logs-worker`
- One-shot local retry run: `make retry-once`

Additional self-service endpoints:

- `POST /payments/intent`
- `POST /payments/capture`
- `POST /webhooks/stripe`
- `POST /webhooks/vusd`
- `POST /webhooks/crypto/confirm`
- `PATCH /admin/policies`
- `PATCH /admin/categories/{category_code}/treasury-wallet`
- `GET /admin/compliance/reviews`
- `GET /admin/webhooks/events`
- `GET /admin/webhooks/metrics`
- `POST /admin/webhooks/retry`
- `PATCH /admin/webhooks/events/{event_id}/remediation`
- `GET /transparency/audit-proof/{entity_type}/{entity_id}`
- `GET /metrics` (Prometheus-style operational metrics)

Sovereign defaults:

- `SOVEREIGN_MODE=true`
- `ENABLE_EXTERNAL_STRIPE_WEBHOOKS=false`
- `ENABLE_EXTERNAL_WALLETCONNECT=false`
- `ENFORCE_INTERNAL_ENDPOINTS_IN_SOVEREIGN_MODE=true`
- `EVM_RPC_URL` must be private/internal
- `INHOUSE_PAYMENT_GATEWAY_BASE_URL` must be private/internal

## Nonprofit Guardrails

- Non-transferable/restricted impact token design
- Treasury wallet routing by humanitarian category
- Compliance and sanctions screening placeholders
- KYC/KYB escalation for large amounts
- Tax receipt issuance switch gated by legal review
- Stripe signature verification and EVM confirmation checks
- Stripe SDK event construction + signature verification (`stripe.Webhook.construct_event`)
- Wagmi + WalletConnect frontend wallet connection
