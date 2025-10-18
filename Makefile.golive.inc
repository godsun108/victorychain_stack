# Go-Live gated by preflight-suite
# Provide targets go-live and go-live-skip-alerts if not already defined elsewhere.

GO_LIVE_PREFLIGHT_SKIP ?=

# Helper macro to run preflight unless bypassed
ifeq ($(GO_LIVE_PREFLIGHT_SKIP),1)
PRELIVE_CMD := @echo "[go-live] preflight skipped (GO_LIVE_PREFLIGHT_SKIP=1)"
else
PRELIVE_CMD := @echo "→ Preflight suite gate" ; \
	$(MAKE) preflight-suite PREFLIGHT_PROM_URL=$(PROM_URL) PREFLIGHT_ENV_FILE=$(ENV_FILE) PREFLIGHT_WINDOWS=$(WINDOWS_FILE) \
		|| { echo "✖ Preflight failed — aborting go-live"; exit 2; }
endif

# If upstream already defines go-live, we append the gate via a wrapper target name.
.PHONY: go-live
ifndef GO_LIVE_DEFINED

go-live:
	$(PRELIVE_CMD)
	@echo "[go-live] placeholder — call your existing go-no-go pipeline here"
	@echo "Tip: Or include your existing Makefile.go-no-go.release.inc before this file."

endif

.PHONY: go-live-skip-alerts
ifndef GO_LIVE_SKIP_ALERTS_DEFINED

go-live-skip-alerts:
	$(PRELIVE_CMD)
	@echo "[go-live-skip-alerts] placeholder — call your existing go-no-go pipeline with GO_NOGO_SKIP_ALERTS=1"

endif

# p95 gates (pre-flip and post-flip)
GO_LIVE_P95_ASSERT ?= 1
P95_LATENCY_S ?= 1.2
P95_REQUIRE_DATA ?= 1
P95_FAIL_CMD ?=
GO_LIVE_P95_STRICT ?= 1

GO_LIVE_PREFLIP_P95_ASSERT ?= 1
PREFLIP_P95_LATENCY_S ?= 1.2
PREFLIP_P95_REQUIRE_DATA ?= 1
PREFLIP_P95_FAIL_CMD ?=
GO_LIVE_PREFLIP_P95_STRICT ?= 1

# Helper: run a p95 assert target with provided threshold and strictness
p95_assert = \
	$(MAKE) prom-p95-assert PROM_URL=$(PROM_URL) P95_LATENCY_S=$1 $(if $2,P95_REQUIRE_DATA=1,) || { \
	  echo "✖ PromQL p95 assert failed ($3)"; \
	  $(if $4,$(4) || true,) \
	  $(if $5,exit 2,) true; }

# If go-live is defined elsewhere, this file only provides knobs and expects callers to invoke $(call p95_assert,...)
# Otherwise, our placeholder target remains in effect.
