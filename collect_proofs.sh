#!/usr/bin/env bash
# collect_proofs.sh — capture patch banner, snap→ORDER_OK/filled block, and Prom JSON/value
set -euo pipefail
IFS=$'\n\t'

LOG="${LOG:-momentum.log}"
PROM="${PROM:-http://localhost:9090}"
SNAP_TIMEOUT="${SNAP_TIMEOUT:-900}"   # seconds

# --- jq fallback ---
if command -v jq >/dev/null 2>&1; then
  JQ="jq"
else
  alias jq="python3 -c 'import sys,json;print(json.dumps(json.loads(sys.stdin.read() or "{}"), indent=2))'"
fi

# --- timeout fallback (macOS often needs gtimeout) ---
TIMEOUT_BIN="timeout"
if ! command -v timeout >/dev/null 2>&1; then
  if command -v gtimeout >/dev/null 2>&1; then
    TIMEOUT_BIN="gtimeout"
  else
    echo "NOTE: 'timeout' not found. Install with 'brew install coreutils' (provides gtimeout), or CTRL-C to stop the wait manually."
    TIMEOUT_BIN=""
  fi
fi

echo "== using LOG=$LOG, PROM=$PROM =="

# 1) Patch banner (prove sitecustomize loaded)
echo "---- PATCH BANNER ----"
grep -n '^\[patch\] simple create_order snap active' "$LOG" | tail -n1 || echo "PATCH BANNER MISSING"

# 2) Snap → ORDER_OK/filled block (wait up to SNAP_TIMEOUT seconds)
echo "---- SNAP → ORDER_OK/FILLED (capturing up to 20 lines after first snap) ----"
# Corrected awk regex to match literal [patch] prefix
capture_cmd='tail -n0 -F '"$LOG"' | awk '\''/^\[patch\] create_order snap/{print; c=20; next} c{print; c--; if (c==0) exit}'\'''
if [[ -n "$TIMEOUT_BIN" ]]; then
  bash -c "$TIMEOUT_BIN $SNAP_TIMEOUT bash -c $capture_cmd" | tee /tmp/snap_block.txt || echo "SNAP TIMEOUT"
else
  # no timeout available; run without it (CTRL-C to stop)
  bash -c "$capture_cmd" | tee /tmp/snap_block.txt || true
fi

# Persist proof snippet
cat /tmp/snap_block.txt >> first_proofs.txt 2>/dev/null || true

# 3) Prometheus metric JSON + numeric value
echo "---- PROM JSON (momentum_trades_total) ----"
curl -s "$PROM/api/v1/query?query=momentum_trades_total" | jq | tee -a first_proofs.txt

echo "---- PROM VALUE ----"
curl -s "$PROM/api/v1/query?query=momentum_trades_total" \
| python3 - <<'PY'
import sys,json
d=json.loads(sys.stdin.read() or '{}')
r=d.get('data',{}).get('result',[])
print(r[0]['value'][1] if r else 'NA')
PY

# 4) If Prom empty, hit local exporter ports directly
if ! curl -s "$PROM/api/v1/query?query=momentum_trades_total" | grep -q '"result": \['; then
  echo "---- EXPORTER FALLBACK (first momentum_trades_total seen) ----"
  for p in 9108 9109 9110 9111 9112; do
    out="$(curl -s "http://127.0.0.1:$p/metrics" | egrep -m1 'momentum_trades_total' || true)"
    if [[ -n "$out" ]]; then
      echo ":$p => $out"
      break
    fi
  done
fi

# 5) If no snap, quick hints
if ! grep -q '^\[patch\] create_order snap' /tmp/snap_block.txt 2>/dev/null; then
  echo "---- NO SNAP SEEN (quick diagnostics) ----"
  grep -i 'Momentum bot started' "$LOG" | tail -n1 || true
  egrep -i '^\[edge\] (skip|check_before_order)' "$LOG" | tail -n20 || true
  egrep -i 'open failed.*not multiple' "$LOG" || echo "no step_size rejects"
  echo "If entries are skipped, check free USDT and edge thresholds."
fi
