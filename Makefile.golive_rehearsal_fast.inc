# Fast rehearsal add-on (minimal)
REH_P95_ASSERT ?= 1
REH_P95_LATENCY_S ?= 1.2
REH_P95_REQUIRE_DATA ?=
REH_P95_FAIL_CMD ?=
REH_P95_STRICT ?=

.PHONY: go-rehearsal-superfast

go-rehearsal-superfast:
	@echo "[go-rehearsal-superfast]" 
	$(if $(REH_P95_ASSERT),$(call p95_assert,$(REH_P95_LATENCY_S),$(REH_P95_REQUIRE_DATA),rehearsal-fast,$(REH_P95_FAIL_CMD),$(REH_P95_STRICT)),@echo "[rehearsal] p95 assert disabled")
	@echo "[go-rehearsal-superfast] done"
