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
- ISO20022 institutional runbook: `docs/iso20022_vusd_institutional_compliance.md`
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
- Admin auth rotation runbook: `docs/admin_auth_rotation.md`
- Ops handoff checklist: `docs/ops_handoff_checklist.md`
- Sovereign plan: `docs/sovereign_inhouse_plan.md`
- Public ingress plan: `docs/public_launch_ingress.md`
- In-house only public launch: `docs/inhouse_only_public_launch.md`
- iPhone in-house onboarding: `docs/iphone_inhouse_onboarding.md`
- TestFlight release checklist: `docs/testflight_release_checklist.md`
- TestFlight notes template: `docs/testflight_release_notes_template.md`
- SLO cron automation: `docs/slo_cron_automation.md`
- API process supervision: `docs/victory_impact_api_supervision.md`
- Prometheus entitlement alerts: `docs/prometheus_entitlement_alerts.md`
- Grafana entitlement dashboard: `docs/grafana_entitlement_dashboard.md`
- Frontend app: `frontend/` (`npm install && npm run dev`)
- Public launch portal route: `/launch` (web) or `/#/launch` (native shell)
- In-house checkout route: `/checkout`
- Webhook retry worker logs: `make logs-worker`
- One-shot local retry run: `make retry-once`
- Generate admin bootstrap tokens: `make admin-token-gen` (`ROLES=... TOKEN_LENGTH=... INCLUDE_LEGACY=true` optional)
- Rotate admin token mappings in env file: `make admin-token-rotate ENV_FILE=.env` (backs up then validates)
- Validate admin env hygiene: `make admin-env-check ENV_FILE=.env.example`
- Run admin incident-recovery drill: `make admin-auth-recovery-drill ENV_FILE=.env PORT=9010`
- vUSD auto-retry (last N hours): `make vusd-auto-retry`
- vUSD auto-retry dry-run preview: `make vusd-auto-retry-dry`
- SLO control-loop execute: `make slo-control-loop`
- SLO control-loop dry-run preview: `make slo-control-loop-dry`
- API health sentinel one-shot: `make api-health-sentinel PORT=9100`
- Prometheus config/rules validation: `make prometheus-check`
- Managed API start enforces dependency parity (`VICTORY_IMPACT_SYNC_REQUIREMENTS_ON_START=true` by default)

SLO automation notes:

- `scripts/run_slo_control_loop.sh` posts `POST /admin/slo/control-loop`.
- When `post_status.overall_healthy=false`, it logs an ops alert via `POST /admin/ops/action` (`action=slo_alert`) by default.
- Optional degraded notifications: `SLO_NOTIFY_SLACK_WEBHOOK_URL`, `SLO_NOTIFY_TELEGRAM_BOT_TOKEN`, `SLO_NOTIFY_TELEGRAM_CHAT_ID`.
- File-based secrets supported via `*_FILE` env vars (admin + notifier credentials).
- Notification controls: `SLO_NOTIFY_COOLDOWN_SECONDS`, `SLO_NOTIFY_ON_RECOVERY`, `SLO_NOTIFY_STATE_FILE`.
- Set `SLO_EXIT_NONZERO_ON_DEGRADED=true` to make cron/CI fail fast on degraded status.

Additional self-service endpoints:

- `POST /payments/intent`
- `GET /payments/intent/{intent_id}`
- `POST /payments/capture`
- `POST /payments/compliance/iso20022/validate`
- `POST /payments/compliance/iso20022/status-report`
- `GET /payments/compliance/iso20022/status-report/{correlation_id}`
- `POST /payments/compliance/iso20022/exception-report`
- `GET /payments/compliance/iso20022/exception-report/{correlation_id}`
- `POST /payments/compliance/iso20022/cancellation-response`
- `POST /payments/compliance/iso20022/cancellation-auto-resolve`
- `POST /payments/compliance/iso20022/acknowledgement`
- `GET /payments/compliance/iso20022/acknowledgement/{correlation_id}`
- `POST /payments/compliance/iso20022/rejection-notification`
- `POST /payments/compliance/iso20022/disposition-auto-resolve`

ISO lifecycle write endpoints support optional body field `idempotency_key` for replay-safe processing.
- `GET /delivery/providers`
- `POST /delivery/orders`
- `GET /delivery/orders/{order_id}`
- `POST /delivery/orders/{order_id}/status`
- `POST /delivery/providers/{provider}/sync/{provider_order_id}`
- `POST /delivery/webhooks/{provider}/status`
- `POST /webhooks/stripe`
- `POST /webhooks/vusd`
- `POST /webhooks/crypto/confirm`
- `GET /public/services`
- `POST /public/auth/challenge`
- `POST /public/auth/verify`
- `POST /public/auth/revoke`
- `GET /public/wallet/{wallet_address}`
- `POST /public/vusd/verify`
- `POST /public/vusd/verify` requires `user_email` or a valid bearer wallet session for entitlement metering
- `POST /public/ai/chat` requires `user_email` or a valid bearer wallet session for entitlement metering
- `POST /public/analytics/event` consumes `calendar_events` entitlement when `event_name` is calendar-related (`user_email` or bearer wallet session required)
- `GET /subscriptions/plans`
- `POST /subscriptions/subscribe`
- `POST /subscriptions/cancel`
- `GET /subscriptions/status`
- `POST /subscriptions/entitlements/check`
- `POST /subscriptions/entitlements/consume`
- `POST /subscriptions/admin/grants`
- `GET /subscriptions/admin/invoices`
- `POST /admin/auth/session`
- `POST /admin/auth/rotate`
- `POST /admin/auth/revoke`
- `PATCH /admin/policies`
- `PATCH /admin/categories/{category_code}/treasury-wallet`
- `GET /admin/compliance/reviews`
- `GET /admin/entitlements/usage`
- `GET /admin/entitlements/summary`
- `GET /admin/webhooks/events`
- `GET /admin/webhooks/metrics`
- `POST /admin/webhooks/retry`
- `PATCH /admin/webhooks/events/{event_id}/remediation`
- `GET /admin/vusd/verifications`
- `GET /admin/vusd/verifications/summary`
- `GET /admin/vusd/verifications/export.csv`
- `POST /admin/vusd/retry`
- `POST /admin/vusd/retry-failed-range`
- `POST /admin/vusd/retry-last-hours`
- `GET /admin/vusd/retry-audit`
- `GET /admin/vusd/retry-audit/export.csv`
- `GET /admin/slo/status`
- `GET /admin/slo/history`
- `POST /admin/slo/control-loop`
- `GET /admin/payments/intents`
- `POST /admin/payments/intents/bulk-action`
- `GET /transparency/audit-proof/{entity_type}/{entity_id}`
- `GET /metrics` (Prometheus-style operational metrics, including entitlement usage/breach gauges and recent 5m/1h breach ratios)

Sovereign defaults:

- `SOVEREIGN_MODE=true`
- `ENABLE_EXTERNAL_STRIPE_WEBHOOKS=false`
- `ENABLE_EXTERNAL_WALLETCONNECT=false`
- `PUBLIC_WEB_MODE=false`
- `INHOUSE_ONLY_MODE=false`
- `ENFORCE_INTERNAL_ENDPOINTS_IN_SOVEREIGN_MODE=true`
- `EVM_RPC_URL` must be private/internal
- `INHOUSE_PAYMENT_GATEWAY_BASE_URL` must be private/internal

Public launch hardening controls:

- `PUBLIC_AUTH_NONCE_TTL_SECONDS` (default `300`)
- `PUBLIC_WALLET_SESSION_TTL_SECONDS` (default `3600`)
- `ADMIN_SESSION_TTL_SECONDS` (default `3600`)
- `ADMIN_SESSION_ROTATE_BEFORE_EXPIRY_SECONDS` (default `600`)
- `ADMIN_SESSION_MAX_ACTIVE_PER_ROLE` (default `5`)
- `ADMIN_BOOTSTRAP_ENABLED` (default `false`)
- `ADMIN_BOOTSTRAP_TOKENS` (default empty; format `token:role`, comma/newline/semicolon-separated)
- `ADMIN_BOOTSTRAP_ALLOWED_ROLES` (default `admin,board,compliance`)
- `ADMIN_ALLOW_LEGACY_API_TOKENS` (default `false`)
- `ADMIN_LEGACY_API_TOKENS` (default empty; format `token:role`, comma/newline/semicolon-separated; only used when legacy auth is enabled)
- Use `./scripts/generate_admin_tokens.sh --include-legacy` (or `make admin-token-gen INCLUDE_LEGACY=true`) to generate `.env`-ready mappings.
- Use `./scripts/rotate_admin_tokens.sh --env-file .env` (or `make admin-token-rotate ENV_FILE=.env`) to rotate mappings in-place with backup + validation.
- `PUBLIC_RATE_LIMIT_WINDOW_SECONDS` (default `60`)
- `PUBLIC_RATE_LIMIT_MAX_REQUESTS` (default `120`)
- `TRUST_PROXY_HEADERS` (default `false`)
- `TRUSTED_PROXY_CIDRS` (default `127.0.0.1/32,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16`)
- `INHOUSE_CHECKOUT_APP_BASE_URL` (recommended: your app domain)
- `INHOUSE_PAYMENT_INTENT_TTL_SECONDS` (default `1800`)
- `DELIVERY_SUPPORTED_PROVIDERS` (default `instacart,doordash,uber_eats,grubhub,shipt,generic`)
- `DELIVERY_WEBHOOK_TOKEN` (optional shared secret for `/delivery/webhooks/{provider}/status`)
- `DELIVERY_AUTO_VERIFY_SETTLEMENT_TX` (default `true`)
- `DELIVERY_PROVIDER_API_TIMEOUT_SECONDS` (default `15`)
- `DELIVERY_INSTACART_BASE_URL`, `DELIVERY_INSTACART_API_KEY`
- `DELIVERY_DOORDASH_BASE_URL`, `DELIVERY_DOORDASH_API_KEY`
- `DELIVERY_UBER_EATS_BASE_URL`, `DELIVERY_UBER_EATS_API_KEY`
- `DELIVERY_GRUBHUB_BASE_URL`, `DELIVERY_GRUBHUB_API_KEY`
- `DELIVERY_SHIPT_BASE_URL`, `DELIVERY_SHIPT_API_KEY`
- `SANCTIONS_SCREENING_PROVIDER` (default `local_rules`)
- `SANCTIONS_BLOCKED_WALLETS` (comma/newline/semicolon-separated denylist)
- `SANCTIONS_BLOCKED_TERMS` (comma/newline/semicolon-separated denylist keywords)
- `ISO20022_SCHEMA_ROOT` (override schema root, default bundled pack)
- `ISO20022_INSTITUTIONAL_PROFILE_PATH` (override institutional profile JSON)
- `ISO20022_REQUIRE_EXTERNAL_SCHEMA_PACK` (default `false`; set `true` in production)
- `VICTORYCHAIN_ISO20022_ONCHAIN_ENABLED` (default `true`)
- `VICTORYCHAIN_REQUIRE_ISO20022_ONCHAIN` (default `false`; set `true` for strict enforcement)

In `APP_ENV=prod` with `PUBLIC_WEB_MODE=true`:

- `ENABLE_EXTERNAL_WALLETCONNECT` must be `true`
- `CORS_ORIGINS` must be HTTPS public origins (no localhost)
- `ADMIN_ALLOW_LEGACY_API_TOKENS` must be `false`
- `ADMIN_BOOTSTRAP_ENABLED` should be `false` unless you explicitly need bootstrap issuance

In `INHOUSE_ONLY_MODE=true`:

- `SOVEREIGN_MODE` must be `true`
- `ENABLE_EXTERNAL_STRIPE_WEBHOOKS` must be `false`
- `ENABLE_EXTERNAL_WALLETCONNECT` must be `false`
- `ADMIN_ALLOW_LEGACY_API_TOKENS` must be `false`
- `EVM_RPC_URL` must be internal/private

One-command in-house public stack:

- `APP_DOMAIN=app.victory.local API_DOMAIN=api.victory.local ./scripts/deploy_inhouse_public.sh`

Production go/no-go gate:

- `./scripts/release_go_no_go.sh inhouse`
- `./scripts/release_go_no_go.sh public`

## Nonprofit Guardrails

- Non-transferable/restricted impact token design
- Treasury wallet routing by humanitarian category
- Runtime OFAC/sanctions screening enforcement toggle (`PATCH /admin/policies`)
- KYC/KYB escalation for large amounts
- Tax receipt issuance switch gated by legal review
- Stripe signature verification and EVM confirmation checks
- Stripe SDK event construction + signature verification (`stripe.Webhook.construct_event`)
- Wagmi + WalletConnect frontend wallet connection
