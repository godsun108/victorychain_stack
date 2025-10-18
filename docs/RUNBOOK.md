# Trillion Bot (VictoryChain) Runbook

This runbook describes the Paper-Mode Proof procedure and governance operations.

Core commands
- Status: ./status.sh --json
- Engage lockdown: ./engage_lockdown.sh -y -r "<reason>"
- Unlock (requires approval token): APPROVAL_TOKEN=<token> ./unlock.sh -y

Paper-Mode Proof (local)
- make proof
  - Preflight (prompt hash + git), guardrail scan, tests
  - Engage lockdown, verify block on live action
  - Unlock with minted test token
  - Verify approval gate: blocked without token, allowed with token (paper-safe)
  - Generate daily bundle; filename includes prompt hash

Paper-Mode Proof (CI)
- GitHub Actions: Trillion Bot Paper-Mode Proof Run
  - Job env: MODE=paper, APPROVAL_SECRET from Actions secret
  - Uploads artifacts: proof.log and reports/**

Governance
- Lockdown halts all live actions (deny-all)
- Live approvals require APPROVAL_SECRET (no fallback); missing secret raises approval_secret_required_in_live
- Ledger events include prompt_hash and git_commit (anchor-ready)

On-call checklist
- Confirm status.sh shows expected state (locked/unlocked)
- Verify guard-rail scan outputs GUARDRAIL_SCAN OK
- Verify proof.log includes PROMPT_VERSION and GIT_COMMIT
- Confirm daily bundle filename contains the prompt hash

---

Additional details

Environment variables
- MODE: paper or live. Live enforces approvals and lockdown guard.
- APPROVAL_SECRET: required in live for any approval verification.
- APPROVAL_TOKEN: short-lived token for a specific action (e.g., order.create, vault.unlock).
- VICTORY_ANCHOR_REF: optional; included in ledger events for anchoring.
- EXPORTS_DIR: directory for chain handoff JSON (default runtime/exports)
- EXPORT_SESSION_CRON_MINUTES: minutes cadence for periodic session export

Exports and chain handoff
- Session summary: `${EXPORTS_DIR}/session_summary.json`
- ISO reserves snapshot: `${EXPORTS_DIR}/iso_reserves.json`

Session summary schema (example)
```
{
  "ts": 1734748800,
  "session_id": "2025-08-20T00:00Z",
  "ledger_head": "<hex>",
  "ledger_tail": "<hex>",
  "trades_closed": 7,
  "realized_pnl_usd": 42.18,
  "iso_banked_usd": 10.54,
  "iso_breakdown": {"XRP": 4.1, "XLM": 3.2, "ALGO": 3.24}
}
```

ISO reserves schema (example)
```
{
  "as_of": "2025-08-20T18:00:00Z",
  "iso_reserves": [
    {"asset":"XRP","amount":1234.56,"est_usd":6543.21},
    {"asset":"XLM","amount":789.01,"est_usd":1234.56}
  ],
  "total_est_usd": 7777.77
}
```

Triggering exports
- Periodic: bot writes both files at least hourly per EXPORT_SESSION_CRON_MINUTES
- On profitable trade_close: iso_reserves.json is refreshed immediately
- On shutdown: session_summary.json is written best-effort
- Manual: `make export-session ENV=.env.live` forces session_summary.json now

One-command local proof
- make proof
  - Prints ORDER_BLOCKED when locked, APPROVAL_BLOCKED without token, and ORDER_RESULT True with valid token.
  - Produces proof.log-equivalent output and a daily bundle under reports/.

Expected proof artifacts
- proof.log (CI artifact): includes prompt version, git commit, lockdown status, guardrail scan outcome, and reports listing.
- reports/daily_YYYYMMDD_<prompt8>_<git7>.txt with prompt_hash and git_commit inside.
- trade_ledger.jsonl (if ledger events were fired during run).

GitHub Actions end-to-end proof
- Workflow path: .github/workflows/proof-run.yml
- Triggers: workflow_dispatch, push to main, pull_request to main.
- Steps performed:
  - Preflight, unit tests, guardrail scan
  - Lockdown engage, block live action, unlock via minted test token
  - Approval gate checks (fail without token, pass with token)
  - Daily report generation and artifact upload
- Retrieve artifacts from the run named trillion-bot-proof.

Guard coverage
- Exchange adapter guards (libs/exchange_adapters/binance_us.py):
  - guarded_create_order (market/limit + params)
  - guarded_cancel_order
  - guarded_create_oco (OCO/stop-style via params)
  - guarded_withdraw
- Global deny-all via governance.vault.deny_all() checked by guards.
- Guardrail scan forbids raw ccxt imports outside allowlist. Script: .hooks/forbid_raw_ccxt.py

Approvals
- Token format: base64url(action|expiry|params_json|hmac).
- Live requires APPROVAL_SECRET; no fallback allowed. Missing secret yields approval_secret_required_in_live.
- Paper/CI supports deterministic fallback secret tied to prompt hash for tests and proof.
- Mint test tokens:
  - governance.approvals.mint_test_token(action="order.create", ttl_seconds=120)
  - governance.approvals.mint_test_token(action="vault.unlock", ttl_seconds=120)

Lockdown operations
- Engage: ./engage_lockdown.sh -y -r "reason"
- Status: ./status.sh --json (includes prompt_version and git_commit)
- Unlock: APPROVAL_TOKEN=<token> ./unlock.sh -y
- Ledger events emitted: LOCKDOWN, UNLOCK_ATTEMPT, UNLOCKED/UNLOCK_FAILED with prompt_hash/git_commit.

Relaunch in paper mode
- VS Code Task: Run Optimizer (paper) or make run-paper.
- Confirm guard coverage remains by running make preflight and make guard-scan.

VS Code tasks
- Build VictoryChain Bot
- Run Optimizer (paper)
- Run Optimizer (request live)
- Run Dashboard
- Run Microcap Scanner (paper)
- Engage Lockdown
- Unlock
- List VS Code Tasks
- Preflight

Troubleshooting
- approval_secret_required_in_live: Set APPROVAL_SECRET when MODE=live.
- missing_verifier: Ensure governance/approvals is importable or libs/common/approvals available.
- lockdown_active: Unlock via approved token or switch to MODE=paper for proofs.
- Guardrail failures: remove raw ccxt imports; use the guarded adapter APIs.

Compliance
- Daily bundles and ledger file provide immutable trace: prompt_hash, git_commit, victory_anchor_ref.
- See docs/COMPLIANCE.md for detailed controls and audit steps.

---

## Trillion Bot — Live-on-BinanceUS Quick Runbook

0) Preconditions (one-time)

- BinanceUS account with API key/secret (trading enabled, withdrawals disabled).
- Small live test USD balance (e.g., $50–$200).
- Repo has:
  - adapter/get_client(mode) that returns ccxt.binanceus in MODE=live, paper stub otherwise.
  - Guarded order methods (short-circuit in paper; in live: validate filters, require approvals, log immutable ledger).
  - smoke_live_binanceus.py (create→cancel flow; emits LIVE_SMOKE_TEST_OK/FAIL).
  - Makefile targets: preflight, live-smoke, proof.

1) .env (or env vars) required

Create/update .env.live:

```
MODE=live
EXCHANGE=binanceus

# API
BINANCEUS_KEY=XXXXXXXXXXXXXXXX
BINANCEUS_SECRET=YYYYYYYYYYYYYYYYYYYY

# Risk guardrails
SYMBOLS=BTC/USDT,ETH/USDT
MAX_NOTIONAL_PER_ORDER=50         # USD cap per order during live smoke
MAX_OPEN_ORDERS=2
SLIPPAGE_BPS=10                   # 0.10%
MIN_PROFIT_BPS=5                  # 0.05% for tiny smoke

# Approvals
APPROVAL_SECRET=choose-a-long-random-string
APPROVERS=nic@church.example,ops@trust.example
REQUIRE_APPROVALS=true

# Ledger / telemetry
LEDGER_PATH=./runtime/ledger/live_ledger.jsonl
SMOKE_LOG=./runtime/logs/smoke_live.log

# Compliance & timing
TIMEOUT_MS=20000
ENABLE_RATE_LIMIT=true
REGION=US
```

Keep your real secret for CI in GitHub Secrets (below). Local file is just for your box.

2) Sanity checks (preflight + proof)

From repo root:

```
# ensure env loads (direnv/export or dotenv in Makefile)
make preflight ENV=.env.live
make proof ENV=.env.live
```

preflight should check:

- MODE == live, EXCHANGE == binanceus
- CCXT loads; fetch exchange.load_markets()
- Precision/filters for SYMBOLS (minQty, minNotional, stepSize, tickSize)
- All guardrail envs present and numeric
- API creds not using withdrawal perms

proof should produce:

- A digest of config (redact secrets)
- Market filter snapshot for allowed symbols
- Hash of the current code (git SHA)
- Signed proof blob (HMAC with APPROVAL_SECRET)
- Writes to ./runtime/proofs/live_proof.json

3) Live smoke test (create→cancel)

```
make live-smoke ENV=.env.live
# This should:
# 1) Place a tiny LIMIT order (e.g., $5–$10 notional) on first symbol
# 2) Immediately cancel it
# 3) Emit LIVE_SMOKE_TEST_OK or FAIL and write smoke_live.log
```

Expected successful tail of runtime/logs/smoke_live.log:

```
... placing test order ... ok
... canceling test order ... ok
LIVE_SMOKE_TEST_OK
```

And appended immutable record in live_ledger.jsonl:

```
{"ts":"...","mode":"live","event":"order.create","symbol":"BTC/USDT", ...}
{"ts":"...","mode":"live","event":"order.cancel","id":"...","symbol":"BTC/USDT", ...}
```

# Approval token details (auto-mint)

Makefile live-smoke auto-mints a short-lived approval token:

- Token fields: { "who":"<git_user>", "scope":"live_smoke", "exp": <unix_ts+120s> }
- Signature: hmac_sha256(APPROVAL_SECRET, compact_json(token))
- Strategy-side validation: reject if exp < now, scope mismatch, or sig invalid.

Adapter env-name preference
- primary: BINANCEUS_KEY / BINANCEUS_SECRET
- fallback: BINANCEUS_API_KEY / BINANCEUS_API_SECRET

Non-interactive CI guard values
- MAX_NOTIONAL_PER_ORDER=5 (CI live smoke)
- MAX_OPEN_ORDERS=1
- SYMBOLS narrowed to BTC/USDT

Artifacts
- live-proof (runtime/proofs/live_proof.json)
- smoke-live-logs (runtime/logs/smoke_live.log)

PR comment template

```
CI Results:
- preflight: ✅
- proof: ✅ (artifact: live-proof)
- live_smoke: ⏳ gated by label `approved-live`

Secrets: not printed.
Guardrails: MAX_NOTIONAL_PER_ORDER=$5 (CI), $50 (local).
```

.gitignore essentials

```
.env*
!example.env
runtime/ledger/**.tmp
runtime/proofs/**.sig.tmp
```

---

## Trillion Momentum Pack

New targets
- make momentum: run the micro-momentum bot (continuous)
- make momentum-once: run a single tick (dry sanity)
- make dashboard: launch Streamlit stewardship dashboard
- make export-session: write session_summary.json now

Dashboard
- File: `dashboard_streamlit.py`
- Start: `make dashboard` (default port 8501)
- Shows: prompt hash, git commit, key metrics, open positions, ISO banking map, ISO Reserves (Vault Feed), recent ledger events.
- Uses LEDGER_PATH and STATE_PATH from env; honors PAUSE file presence; reads exports from `${EXPORTS_DIR}`.

ISO map per exchange
- Dashboard computes available ISO pairs by scanning markets for ISO_COINS on QUOTE_PREFS.
- Coins without pairs remain listed with null symbol; UI does not crash on missing markets.

Autopause hooks
- Bot triggers auto-pause on:
  - Error burst: >=3 errors within 60s
  - Latency spike: p95 >= 5s over last 60s
  - Presence of runtime/PAUSE file
- Dashboard surfaces active pause reason.

Acceptance checklist (Momentum Pack)
- [ ] `trillion_bot_momentum.py` present and runnable
- [ ] `dashboard_streamlit.py` present; `make dashboard` works
- [ ] Makefile targets: momentum, momentum-once, dashboard, export-session
- [ ] `.env.example` updated with required fields including export knobs
- [ ] Session summary written hourly and on shutdown; iso_reserves refreshed after profitable close and hourly
- [ ] ISO map resilient to missing pairs
- [ ] Autopause hooks active; PAUSE file respected
- [ ] Live smoke artifacts captured; ledger includes prompt hash
- [ ] RUNBOOK updated with Momentum Pack steps and schemas
