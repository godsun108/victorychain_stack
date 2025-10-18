# Rehearsal go-live targets with optional Prom p95 gate
REH_P95_ASSERT ?= 1
REH_P95_LATENCY_S ?= 1.2
REH_P95_REQUIRE_DATA ?=
REH_P95_FAIL_CMD ?=
REH_P95_STRICT ?=

REHEARSAL_PREFLIGHT_SKIP ?=

# Use preflight gate by default unless skipped
ifeq ($(REHEARSAL_PREFLIGHT_SKIP),1)
REH_PREFLIGHT_CMD := @echo "[rehearsal] preflight skipped"
else
REH_PREFLIGHT_CMD := @$(MAKE) preflight-suite PREFLIGHT_PROM_URL=$(PROM_URL) PREFLIGHT_ENV_FILE=$(ENV_FILE) PREFLIGHT_WINDOWS=$(WINDOWS_FILE) || { echo "✖ Preflight failed — aborting rehearsal"; exit 2; }
endif

# p95 assert call (rehearsal flavor)
reh_p95_call = $(if $(REH_P95_ASSERT),$(call p95_assert,$(REH_P95_LATENCY_S),$(REH_P95_REQUIRE_DATA),rehearsal,$(REH_P95_FAIL_CMD),$(REH_P95_STRICT)),@echo "[rehearsal] p95 assert disabled")

.PHONY: go-rehearsal go-rehearsal-fast

go-rehearsal:
	$(REH_PREFLIGHT_CMD)
	$(reh_p95_call)
	@echo "[go-rehearsal] placeholder — run validator + gate + post hooks (no flip)"

# Fast variant: skip preflight by default, but still allow p95 check
ifeq ($(REHEARSAL_PREFLIGHT_SKIP),)
REHEARSAL_PREFLIGHT_SKIP := 1
endif

go-rehearsal-fast:
	@echo "[go-rehearsal-fast] running"
	$(reh_p95_call)
	@echo "[go-rehearsal-fast] done"
