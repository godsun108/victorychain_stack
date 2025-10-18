# VictoryChain Makefile

VENV ?= $(shell [ -d .venv ] && echo .venv || echo venv)

.PHONY: help setup venv install lint test fmt run-paper run-dashboard docker-up docker-down lockdown preflight guard-scan tasks proof live-smoke momentum momentum-once dashboard export-session approve anchor gateway-mock metrics stack-up stack-down stack-smoke

help:
	@echo "Common targets:"
	@echo "  setup        - create venv and install deps"
	@echo "  install      - pip install -r requirements.txt"
	@echo "  lint         - run linters"
	@echo "  test         - run tests"
	@echo "  fmt          - format code"
	@echo "  run-paper    - run optimizer in paper mode"
	@echo "  run-dashboard- start dashboard"
	@echo "  momentum     - run micro-momentum bot (continuous)"
	@echo "  momentum-once- run micro-momentum bot single tick"
	@echo "  dashboard    - start Streamlit stewardship dashboard"
	@echo "  export-session- write session_summary.json now"
	@echo "  approve      - mint short-lived approval token for live entries"
	@echo "  anchor       - post latest session_summary.json to VictoryChain gateway"
	@echo "  gateway-mock - run local VictoryChain gateway mock on :8787"
	@echo "  docker-up    - docker compose up"
	@echo "  docker-down  - docker compose down"
	@echo "  lockdown     - engage emergency lockdown (local)"
	@echo "  preflight    - governance preflight (prompt hash, guard scan, tasks)"
	@echo "  guard-scan   - scan source for forbidden raw ccxt imports"
	@echo "  tasks        - list VS Code tasks"
	@echo "  proof        - run full proof sequence (like GitHub Action)"
	@echo "  live-smoke   - dry-live smoke on BinanceUS (tiny size, guarded)"
	@echo "  metrics      - run Prometheus metrics server"
	@echo "  stack-up     - start monitoring/proxy stack"
	@echo "  stack-down   - stop monitoring/proxy stack"
	@echo "  stack-smoke   - run smoke test on monitoring/proxy stack"
	@echo "  reinvest-apply-preset-xrp-hbar - write preset weights for XRP/HBAR"
	@echo "  start-treasury-exporter        - start /metrics server for treasury"
	@echo "  prom-reload                    - POST /-/reload to Prometheus"

venv:
	python3 -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -U pip

setup: venv install

install:
	. $(VENV)/bin/activate && pip install -r requirements.txt

lint:
	. $(VENV)/bin/activate && flake8 . && black --check .

fmt:
	. $(VENV)/bin/activate && black .

# --- Treasury / Reinvest helpers ---
TREASURY_PRESET := runtime/reinvest/preset.json

.PHONY: reinvest-apply-preset-xrp-hbar
reinvest-apply-preset-xrp-hbar:
	@mkdir -p runtime/reinvest
	@python - <<-'PY'
	import json, os
	preset = {
	  "name": "xrp-hbar-preset",
	  "weights": {
	    "XRP/USDT": 0.6,
	    "HBAR/USDT": 0.4
	  }
	}
	os.makedirs('runtime/reinvest', exist_ok=True)
	with open('runtime/reinvest/preset.json','w') as f:
	    json.dump(preset, f, indent=2)
	print('Wrote runtime/reinvest/preset.json')
	PY

.PHONY: start-treasury-exporter
start-treasury-exporter:
	@echo "[treasury] starting exporter on :$${TREASURY_METRICS_PORT:-9112}"
	. $(VENV)/bin/activate && TREASURY_METRICS_PORT=$${TREASURY_METRICS_PORT:-9112} python scripts/treasury_exporter.py 2>&1 | tee $${TREASURY_EXPORTER_LOG:-runtime/logs/treasury_exporter.log}

.PHONY: prom-reload
prom-reload:
	@echo "POST /-/reload -> $${PROM_URL:-http://localhost:9090}"
	@curl -fsS -X POST "$${PROM_URL:-http://localhost:9090}/-/reload" && echo "ok" || { echo "reload failed"; exit 2; }

test:
	. $(VENV)/bin/activate && pytest -q

run-paper:
	MODE=paper . $(VENV)/bin/activate && python launch_magic_optimizer.py

run-dashboard:
	. $(VENV)/bin/activate && python live_trading_dashboard.py

lockdown:
	python -c "from governance import vault; vault.lockdown('makefile_lockdown')" && echo "LOCKDOWN engaged"

# List VS Code tasks without requiring jq
tasks:
	@python - <<-'PY'
	import json, sys
	try:
	    with open('.vscode/tasks.json') as f:
	        data = json.load(f)
	    print('TASKS:')
	    for t in data.get('tasks', []):
	        print(t.get('label'))
	except Exception as e:
	    print('(no .vscode/tasks.json)')
	PY

# Guardrail scan for forbidden raw ccxt imports, allowlist handled in script
guard-scan:
	@python .hooks/forbid_raw_ccxt.py $$(git ls-files "**/*.py")

# Governance preflight: prompt version + git, guard scan, VS Code tasks
preflight:
	@echo "== PROMPT VERSION + GIT =="; \
	python - <<-'PY'
	from governance.prompt_version import current_version
	ph, gc = current_version()
	print('PROMPT_VERSION', ph)
	print('GIT_COMMIT', (gc or '')[:12] if isinstance(gc, str) else gc)
	PY
	@echo "== GUARDRAIL SCAN =="; \
	python .hooks/forbid_raw_ccxt.py $$(git ls-files "**/*.py") && echo "GUARDRAIL_SCAN OK" || true
	@echo "== VS CODE TASKS =="; \
	python - <<-'PY'
	import json
	try:
	    with open('.vscode/tasks.json') as f:
	        data = json.load(f)
	    for t in data.get('tasks', []):
	        print(t.get('label'))
	except Exception:
	    print('(no .vscode/tasks.json)')
	PY
	@echo "== ENV + EXCHANGE CHECK =="; \
	python -m tools.preflight || true

# === Preflight Suite (Prometheus, agent, riskd, windows, token) ===
# Accept both PREFLIGHT_* vars and compatibility aliases PROM_URL/ENV_FILE/WINDOWS_FILE
PREFLIGHT_PROM_URL ?= http://localhost:9090
PREFLIGHT_ENV_FILE ?= .env.live
PREFLIGHT_WINDOWS ?= riskd/riskd_windows.auto.json
PREFLIGHT_TIMEOUT ?= 5
ifdef PROM_URL
PREFLIGHT_PROM_URL := $(PROM_URL)
endif
ifdef ENV_FILE
PREFLIGHT_ENV_FILE := $(ENV_FILE)
endif
ifdef WINDOWS_FILE
PREFLIGHT_WINDOWS := $(WINDOWS_FILE)
endif

.PHONY: preflight-suite preflight-suite-fast preflight-all
preflight-suite:
	@echo "[PREFLIGHT] running full preflight (timeout=$(PREFLIGHT_TIMEOUT)s)" ; \
	set -a; [ -f $(PREFLIGHT_ENV_FILE) ] && . $(PREFLIGHT_ENV_FILE) || true; set +a; \
	python3 scripts/preflight.py \
	  --prom $(PREFLIGHT_PROM_URL) \
	  --env-file $(PREFLIGHT_ENV_FILE) \
	  --windows-file $(PREFLIGHT_WINDOWS) \
	  --expect-guardrails \
	  --timeout $(PREFLIGHT_TIMEOUT)

preflight-suite-fast:
	@echo "[PREFLIGHT] running fast preflight (timeout=3s)" ; \
	set -a; [ -f $(PREFLIGHT_ENV_FILE) ] && . $(PREFLIGHT_ENV_FILE) || true; set +a; \
	PREFLIGHT_TIMEOUT=3 python3 scripts/preflight.py \
	  --prom $(PREFLIGHT_PROM_URL) \
	  --env-file $(PREFLIGHT_ENV_FILE) \
	  --windows-file $(PREFLIGHT_WINDOWS)

# Run legacy governance preflight + the new Prom/agent/riskd preflight
preflight-all: preflight preflight-suite

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

ENV ?= .env.live
WINDOWS_FILE ?= riskd/riskd_windows.auto.json
# export $(shell sed 's/=.*//' $(ENV) 2>/dev/null)

# Mark that we provide go-live ourselves; include will not add placeholders
GO_LIVE_DEFINED := 1

# Optionally include go-live gating and helpers
-include Makefile.golive.inc
-include Makefile.golive_rehearsal.inc
-include Makefile.golive_rehearsal_fast.inc
-include Makefile.treasury.inc

# Real go-live targets that call scripts
.PHONY: go-live go-live-dry

go-live:
	$(PRELIVE_CMD)
	@echo "[go-live] executing go-live.sh" ; \
	PROM_URL=$(PROM_URL) ./go-live.sh

go-live-dry:
	@echo "[go-live-dry] executing go-live-dry.sh" ; \
	PROM_URL=$(PROM_URL) ./go-live-dry.sh

.PHONY: proof
proof:
	@echo "[0] Ensure scripts are executable"
	@chmod +x ./engage_lockdown.sh ./status.sh ./unlock.sh || true
	@mkdir -p runtime/logs runtime/proofs reports || true
	@echo "[1] Preflight + tests"
	@MODE=paper $(MAKE) preflight | tee runtime/logs/local-preflight.log || true
	@pytest -q tests/test_governance.py || true
	@pytest -q tests/test_adapter_guards.py || true
	@echo "[2] Guardrail scan"
	@$(MAKE) guard-scan
	@echo "[3] Status (expect UNLOCKED)"
	@./status.sh --json || true
	@echo "[4] Engage lockdown"
	@./engage_lockdown.sh -y -r "make_proof_lockdown"
	@./status.sh --json
	@echo "[5] Order attempt while locked (expect block)"
	@MODE=live python scripts/proof_order_attempt.py --locked
	@echo "[6] Unlock with invalid token (expect fail)"
	@APPROVAL_TOKEN=TEST_ONLY_FAKE_TOKEN_SHOULD_FAIL ./unlock.sh -y || echo "UNLOCK_EXPECTED_FAIL_OK"
	@echo "[7] Mint test token + unlock"
	@APPROVAL_TOKEN=$$(python - <<-'PY' \
	from governance.approvals import mint_test_token; print(mint_test_token(action="vault.unlock", ttl_seconds=120))
	PY
	) ./unlock.sh -y
	@./status.sh --json
	@echo "[8] Live order without token (expect approval block)"
	@MODE=live python scripts/proof_order_attempt.py --no-token
	@echo "[9] Live order with valid token (expect pass / paper-safe)"
	@APPROVAL_TOKEN=$$(python - <<-'PY' \
	from governance.approvals import mint_test_token; print(mint_test_token(action="order.create", ttl_seconds=120))
	PY
	) MODE=live python scripts/proof_order_attempt.py --with-token
	@echo "[10] Reports include prompt hash"
	@python - <<-'PY'
	from reporting.daily import generate_daily_bundle
	p = generate_daily_bundle()
	print("DAILY_BUNDLE", p)
	PY
	@ls -1 reports || true
	@echo "[11] Generate signed live_proof.json"
	@mkdir -p runtime/proofs
	@python -m tools.proof --out runtime/proofs/live_proof.json | tee runtime/logs/local-proof.log
	@echo "[DONE] Proof complete."

.PHONY: live-smoke
live-smoke:
	@echo "[LIVE-SMOKE] checking environment" ; \
	req_envs="MODE APPROVAL_SECRET BINANCEUS_API_KEY BINANCEUS_API_SECRET" ; \
	for v in $$req_envs; do \
	  if [ -z "$$($$SHELL -lc 'echo $$'$$v)" ]; then echo "GO_LIVE_BLOCKED:missing_env:$$v"; exit 2; fi; \
	done ; \
	if [ "$$MODE" != "live" ]; then echo "GO_LIVE_BLOCKED:MODE_not_live"; exit 2; fi ; \
	mkdir -p runtime/logs runtime/ledger ; \
	echo "[LIVE-SMOKE] status" ; ./status.sh --json || true ; \
	echo "[LIVE-SMOKE] mint short-lived approval token" ; \
	export APPROVAL_TOKEN=$$(python - <<-'PY'
	from governance.approvals import mint_test_token
	print(mint_test_token(action="order.create", ttl_seconds=120))
	PY
	); \
	echo "[LIVE-SMOKE] create->cancel tiny order" ; \
	python scripts/smoke_live_binanceus.py | tee $${SMOKE_LOG:-runtime/logs/smoke_live.log} ; \
	echo "[LIVE-SMOKE] ledger tail" ; tail -n 20 $${LEDGER_PATH:-trade_ledger.jsonl} 2>/dev/null || true ; \
	echo "[LIVE-SMOKE] done"

.PHONY: momentum momentum-once dashboard export-session approve anchor gateway-mock

momentum:
	@mkdir -p runtime/logs runtime/state runtime/ledger || true
	APPROVAL_TOKEN=$$( [ -f runtime/APPROVAL_TOKEN.txt ] && cat runtime/APPROVAL_TOKEN.txt || printf "%s" "$$APPROVAL_TOKEN" ) . $(VENV)/bin/activate && python trillion_bot_momentum.py 2>&1 | tee ${MOMENTUM_LOG:-runtime/logs/momentum.log}

momentum-once:
	@mkdir -p runtime/logs runtime/state runtime/ledger || true
	APPROVAL_TOKEN=$$( [ -f runtime/APPROVAL_TOKEN.txt ] && cat runtime/APPROVAL_TOKEN.txt || printf "%s" "$$APPROVAL_TOKEN" ) SINGLE_TICK=1 . $(VENV)/bin/activate && python trillion_bot_momentum.py --once 2>&1 | tee ${MOMENTUM_LOG:-runtime/logs/momentum-once.log}

# Streamlit dashboard for stewardship metrics and ISO banking
dashboard:
	@mkdir -p runtime/logs || true
	. $(VENV)/bin/activate && streamlit run dashboard_streamlit.py --server.port $${PORT:-8501} 2>&1 | tee $${DASHBOARD_LOG:-runtime/logs/dashboard.log}

# Force an immediate session summary export (VictoryChain anchor payload)
export-session:
	@mkdir -p runtime/logs || true
	. $(VENV)/bin/activate && python trillion_bot_momentum.py --export-session 2>&1 | tee $${EXPORT_LOG:-runtime/logs/export-session.log}

# Mint and store a short-lived approval token for live entries (saved to runtime/APPROVAL_TOKEN.txt)
approve:
	@mkdir -p runtime || true
	@python - <<-'PY'
	from governance.approvals import mint_test_token
	import os
	# 5 minutes default TTL for convenience
	print('Minting order.create approval token (ttl=300s) ...')
	ok = mint_test_token(action='order.create', ttl_seconds=300)
	print('APPROVAL_TOKEN='+ok)
	with open('runtime/APPROVAL_TOKEN.txt','w', encoding='utf-8') as f:
	    f.write(ok)
	print('Saved to runtime/APPROVAL_TOKEN.txt')
	PY
	@echo "Use automatically on next 'make momentum' run (reads runtime/APPROVAL_TOKEN.txt)."

# Anchor latest session summary to VictoryChain gateway (if configured)
anchor:
	@mkdir -p runtime/logs || true
	. $(VENV)/bin/activate && python anchor_victorychain.py 2>&1 | tee $${ANCHOR_LOG:-runtime/logs/anchor.log}

# Run VictoryChain FastAPI gateway mock on port 8787
gateway-mock:
	@mkdir -p runtime/logs || true
	. $(VENV)/bin/activate && uvicorn gateway_mock:app --host 0.0.0.0 --port 8787 2>&1 | tee $${GATEWAY_LOG:-runtime/logs/gateway-mock.log}

.PHONY: metrics
metrics:
	. $(VENV)/bin/activate && python - <<-'PY'
	from scripts.strategy_metrics import start_metrics_server
	start_metrics_server(int(__import__('os').getenv('METRICS_PORT','9108')))
	print('Metrics server on port', __import__('os').getenv('METRICS_PORT','9108'))
	import time
	while True:
	    time.sleep(3600)
	PY

.PHONY: stack-up stack-down stack-smoke
stack-up:
	docker compose -f docker-compose.stack.yml up -d --build

stack-down:
	docker compose -f docker-compose.stack.yml down

stack-smoke:
	docker compose -f docker-compose.stack.yml run --rm stack-smoke

# === Postdeploy Smoke ===
P95_LATENCY_S ?= 1.2
SMOKE_SAMPLES ?= 20
SMOKE_TIMEOUT ?= 5

.PHONY: postdeploy-smoke postdeploy-smoke-fast
postdeploy-smoke:
	@echo "[POSTDEPLOY] standard smoke" ; \
	python3 scripts/postdeploy_smoke.py \
	  --prom $(PROM_URL) \
	  --agent $(AGENT_URL) \
	  --p95-s $(P95_LATENCY_S) \
	  --samples $(SMOKE_SAMPLES) \
	  --timeout $(SMOKE_TIMEOUT)

postdeploy-smoke-fast:
	@echo "[POSTDEPLOY] fast smoke" ; \
	P95_LATENCY_S=1.5 SMOKE_TIMEOUT=3 python3 scripts/postdeploy_smoke.py \
	  --prom $(PROM_URL) \
	  --agent $(AGENT_URL)

# === PromQL p95 assert ===
P95_METRIC ?= agent_request_latency_seconds_bucket
P95_WINDOW ?= 5m
P95_QUANTILE ?= 0.95
P95_FILTER ?= path!~"/metrics"
P95_GROUP_BY ?= le
P95_LATENCY_S ?= 1.2
P95_TIMEOUT ?= 5

.PHONY: prom-p95-assert postdeploy-smoke-plus
prom-p95-assert:
	@echo "[P95] asserting PromQL p95 <= $(P95_LATENCY_S)s over $(P95_WINDOW)" ; \
	python3 scripts/prom_p95_assert.py \
	  --prom $(PROM_URL) \
	  --metric $(P95_METRIC) \
	  --window $(P95_WINDOW) \
	  --quantile $(P95_QUANTILE) \
	  --filter '$(P95_FILTER)' \
	  --group-by $(P95_GROUP_BY) \
	  --p95-s $(P95_LATENCY_S) \
	  --timeout $(P95_TIMEOUT) \
	  $(if $(P95_REQUIRE_DATA),--require-data,)

postdeploy-smoke-plus: postdeploy-smoke prom-p95-assert
	@echo "[POSTDEPLOY] smoke+PromQL p95 assert complete"
