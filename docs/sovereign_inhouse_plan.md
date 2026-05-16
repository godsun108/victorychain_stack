# Sovereign In-House Operation Plan

This stack is configured to run in sovereign mode by default.

## Default Sovereign Guardrails

- `SOVEREIGN_MODE=true`
- `ENABLE_EXTERNAL_STRIPE_WEBHOOKS=false`
- `ENABLE_EXTERNAL_WALLETCONNECT=false`
- `ENFORCE_INTERNAL_ENDPOINTS_IN_SOVEREIGN_MODE=true`

With these defaults:

- Stripe webhook endpoint is blocked (`/webhooks/stripe` returns `403`).
- WalletConnect is disabled in frontend unless explicitly opt-in.
- Startup fails closed if `EVM_RPC_URL` or `INHOUSE_PAYMENT_GATEWAY_BASE_URL` is not internal/private.
- Donation processing, treasury routing, beneficiary flow, worker retries, and reporting run fully in-house.

## In-House Deployment Profile

Use:

```bash
docker compose -f compose.inhouse.yml up -d --build
```

Included services:

- API
- Worker
- Postgres
- Prometheus
- Grafana

Required internal endpoints:

- `EVM_RPC_URL=http://evm-node.internal:8545` (example)
- `INHOUSE_PAYMENT_GATEWAY_BASE_URL=https://payments.internal` (example)

## Mass Adoption Readiness (In-House)

1. Run multiple API replicas behind an internal load balancer.
2. Use managed internal Postgres HA (primary/replica + backups).
3. Keep worker horizontal scale for webhook/retry throughput.
4. Place Prometheus/Grafana behind internal SSO and private network.
5. Use internal object storage for receipts, reports, and audit exports.
6. Use internal key management and secret rotation.

## Opt-In External Integrations

If legal/compliance later allows selective external integrations, enable them explicitly and per-environment:

- `ENABLE_EXTERNAL_STRIPE_WEBHOOKS=true`
- `ENABLE_EXTERNAL_WALLETCONNECT=true`

Never enable by default in production.
