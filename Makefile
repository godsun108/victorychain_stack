.PHONY: help setup run test up down logs logs-worker reset-db seed retry-once admin-token-gen admin-token-rotate admin-env-check vusd-auto-retry vusd-auto-retry-dry slo-control-loop slo-control-loop-dry prometheus-check release-check ios-bump api-start api-stop api-restart api-status api-health-sentinel

help:
	@echo "setup      Create .venv and install deps"
	@echo "run        Run API locally"
	@echo "test       Run test suite"
	@echo "up         Start docker-compose stack"
	@echo "down       Stop docker-compose stack"
	@echo "logs       Follow API logs"
	@echo "logs-worker Follow webhook worker logs"
	@echo "reset-db   Recreate docker database volume"
	@echo "seed       Seed local dev data"
	@echo "retry-once Run one webhook retry batch locally"
	@echo "admin-token-gen Generate ADMIN_BOOTSTRAP_TOKENS mapping (set ROLES/TOKEN_LENGTH/INCLUDE_LEGACY=true)"
	@echo "admin-token-rotate Rotate admin auth tokens in ENV_FILE with backup + validation"
	@echo "admin-env-check Validate admin env token hygiene (ENV_FILE defaults to .env.example)"
	@echo "vusd-auto-retry Trigger vUSD failed/rejected retry for last N hours"
	@echo "vusd-auto-retry-dry Dry-run vUSD failed/rejected retry for last N hours"
	@echo "slo-control-loop Run SLO control-loop execution with ops alert on degraded"
	@echo "slo-control-loop-dry Run SLO control-loop dry-run with ops alert on degraded"
	@echo "prometheus-check Validate Prometheus config and alert rules"
	@echo "release-check Run production go/no-go gate (default profile=inhouse)"
	@echo "ios-bump   Bump iOS/TestFlight version (use VERSION=x.y.z BUILD=n)"
	@echo "api-start  Start managed Victory Impact API process (PORT=9100 optional)"
	@echo "api-stop   Stop managed Victory Impact API process (PORT=9100 optional)"
	@echo "api-restart Restart managed Victory Impact API process (PORT=9100 optional)"
	@echo "api-status Show managed Victory Impact API runtime status"
	@echo "api-health-sentinel Run one API health sentinel cycle (PORT=9100 optional)"

setup:
	python3 -m venv .venv
	. .venv/bin/activate && python -m pip install -r requirements.txt

run:
	. .venv/bin/activate && uvicorn src.victory_impact.main:app --reload

test:
	. .venv/bin/activate && pytest -q

up:
	cp -n .env.example .env || true
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

reset-db:
	docker compose down -v
	docker compose up -d db

seed:
	. .venv/bin/activate && python scripts/reseed_demo_data.py

retry-once:
	. .venv/bin/activate && python scripts/retry_webhooks.py --limit 100

admin-token-gen:
	@args=""; \
	if [ -n "$${ROLES:-}" ]; then args="$$args --roles $${ROLES}"; fi; \
	if [ -n "$${TOKEN_LENGTH:-}" ]; then args="$$args --length $${TOKEN_LENGTH}"; fi; \
	if [ "$${INCLUDE_LEGACY:-false}" = "true" ]; then args="$$args --include-legacy"; fi; \
	./scripts/generate_admin_tokens.sh $$args

admin-token-rotate:
	@args="--env-file $${ENV_FILE:-.env}"; \
	if [ -n "$${ROLES:-}" ]; then args="$$args --roles $${ROLES}"; fi; \
	if [ -n "$${TOKEN_LENGTH:-}" ]; then args="$$args --length $${TOKEN_LENGTH}"; fi; \
	if [ "$${INCLUDE_LEGACY:-false}" = "true" ]; then args="$$args --include-legacy"; fi; \
	if [ "$${ENABLE_BOOTSTRAP:-false}" = "true" ]; then args="$$args --enable-bootstrap"; fi; \
	./scripts/rotate_admin_tokens.sh $$args

admin-env-check:
	@./scripts/check_admin_env_hygiene.py \
		--env-file "$${ENV_FILE:-.env.example}" \
		$$( [ "$${EXPECT_BOOTSTRAP_DISABLED:-true}" = "true" ] && echo --expect-bootstrap-disabled ) \
		$$( [ "$${EXPECT_LEGACY_DISABLED:-true}" = "true" ] && echo --expect-legacy-disabled ) \
		$$( [ "$${REQUIRE_EMPTY_BOOTSTRAP_TOKENS:-false}" = "true" ] && echo --require-empty-bootstrap-tokens ) \
		$$( [ "$${REQUIRE_EMPTY_LEGACY_TOKENS:-false}" = "true" ] && echo --require-empty-legacy-tokens )

vusd-auto-retry:
	@VICTORY_API_BASE_URL=$${VICTORY_API_BASE_URL:-http://localhost:8000} \
	VUSD_RETRY_HOURS_BACK=$${VUSD_RETRY_HOURS_BACK:-24} \
	VUSD_RETRY_LIMIT=$${VUSD_RETRY_LIMIT:-300} \
	VUSD_RETRY_INCLUDE_DEAD_LETTER=$${VUSD_RETRY_INCLUDE_DEAD_LETTER:-true} \
	VUSD_RETRY_DRY_RUN=false \
	./scripts/run_vusd_auto_retry.sh

vusd-auto-retry-dry:
	@VICTORY_API_BASE_URL=$${VICTORY_API_BASE_URL:-http://localhost:8000} \
	VUSD_RETRY_HOURS_BACK=$${VUSD_RETRY_HOURS_BACK:-24} \
	VUSD_RETRY_LIMIT=$${VUSD_RETRY_LIMIT:-300} \
	VUSD_RETRY_INCLUDE_DEAD_LETTER=$${VUSD_RETRY_INCLUDE_DEAD_LETTER:-true} \
	VUSD_RETRY_DRY_RUN=true \
	./scripts/run_vusd_auto_retry.sh

slo-control-loop:
	@VICTORY_API_BASE_URL=$${VICTORY_API_BASE_URL:-http://localhost:8000} \
	SLO_DRY_RUN=false \
	SLO_MAX_ACTIONS=$${SLO_MAX_ACTIONS:-3} \
	SLO_RETRY_HOURS_BACK=$${SLO_RETRY_HOURS_BACK:-24} \
	SLO_RETRY_LIMIT=$${SLO_RETRY_LIMIT:-300} \
	SLO_ALERT_ON_DEGRADED=$${SLO_ALERT_ON_DEGRADED:-true} \
	SLO_EXIT_NONZERO_ON_DEGRADED=$${SLO_EXIT_NONZERO_ON_DEGRADED:-false} \
	./scripts/run_slo_control_loop.sh

slo-control-loop-dry:
	@VICTORY_API_BASE_URL=$${VICTORY_API_BASE_URL:-http://localhost:8000} \
	SLO_DRY_RUN=true \
	SLO_MAX_ACTIONS=$${SLO_MAX_ACTIONS:-3} \
	SLO_RETRY_HOURS_BACK=$${SLO_RETRY_HOURS_BACK:-24} \
	SLO_RETRY_LIMIT=$${SLO_RETRY_LIMIT:-300} \
	SLO_ALERT_ON_DEGRADED=$${SLO_ALERT_ON_DEGRADED:-true} \
	SLO_EXIT_NONZERO_ON_DEGRADED=$${SLO_EXIT_NONZERO_ON_DEGRADED:-false} \
	./scripts/run_slo_control_loop.sh

prometheus-check:
	@docker run --rm -v "$$PWD/ops/prometheus:/etc/prometheus:ro" prom/prometheus:v2.54.1 \
		promtool check config /etc/prometheus/prometheus.yml
	@docker run --rm -v "$$PWD/ops/prometheus:/etc/prometheus:ro" prom/prometheus:v2.54.1 \
		promtool check rules /etc/prometheus/alerts_entitlements.yml

release-check:
	./scripts/release_go_no_go.sh inhouse

ios-bump:
	@test -n "$(VERSION)" || (echo "VERSION is required (example: VERSION=1.0.1)" && exit 1)
	@test -n "$(BUILD)" || (echo "BUILD is required (example: BUILD=2)" && exit 1)
	./scripts/bump_ios_version.sh $(VERSION) $(BUILD)

api-start:
	./scripts/start_victory_impact_api.sh $${PORT:-9000}

api-stop:
	./scripts/stop_victory_impact_api.sh $${PORT:-9000}

api-restart:
	./scripts/restart_victory_impact_api.sh $${PORT:-9000}

api-status:
	./scripts/status_victory_impact_api.sh $${PORT:-9000}

api-health-sentinel:
	./scripts/run_api_health_sentinel.sh $${PORT:-9000}
