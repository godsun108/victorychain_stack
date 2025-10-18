#!/usr/bin/env bash
# sanity_pack.sh — Momentum bot live checks (enhanced)

set -euo pipefail
IFS=$'\n\t'

# ---------- tiny color helpers ----------
ok(){   printf "\033[32m%s\033[0m\n" "$*"; }
warn(){ printf "\033[33m%s\033[0m\n" "$*"; }
err(){  printf "\033[31m%s\033[0m\n" "$*"; }

# ---------- jq fallback ----------
if command -v jq >/dev/null 2>&1; then
  JQ="jq"
else
  warn "jq not found; using Python fallback"
  JQ='python3 - <<PY
import sys,json
print(json.dumps(json.loads(sys.stdin.read() or "{}"), indent=2))
PY'
fi

# ---------- inputs & defaults ----------
LOG="${LOG:-}"
if [[ -z "${LOG}" ]]; then
  for f in runtime/logs/momentum.log momentum.log; do
    [[ -f "$f" ]] && LOG="$f" && break
  done
fi
LOG="${LOG:-momentum.log}"
PROM="${PROM:-http://localhost:9090}"
FOLLOW="${FOLLOW:-0}"
# --- args ---
RESTART=0
for a in "$@"; do
  case "$a" in
    --restart) RESTART=1 ;;
  esac
done

echo "Using LOG=$LOG"
echo "PROM endpoint: $PROM"

# --- restart (optional) ---
if [[ "$RESTART" = "1" ]]; then
  echo; echo "== restart =="
  pkill -f 'trillion_bot_momentum.py' || true
  : > "$LOG"
  nohup env PYTHONPATH=. MODE=live DRY_RUN=false python3 trillion_bot_momentum.py >>"$LOG" 2>&1 &
  # wait up to 20s for patch banner
  for i in {1..20}; do
    sleep 1
    if grep -q '^\[patch\] simple create_order snap active' "$LOG"; then
      ok "patch banner detected"
      break
    fi
    [[ $i -eq 20 ]] && warn "patch banner not seen yet"
  done
fi

# ---------- 0) Ensure single runner ----------
echo; echo "== process =="
if ! pgrep -fl 'trillion_bot_momentum.py' >/dev/null; then
  warn "no runner found"
else
  pgrep -fl 'trillion_bot_momentum.py'
fi

# Try to detect the python binary actually running the bot
PYBIN="$(pgrep -fl 'trillion_bot_momentum.py' | awk '{print $2; exit}' || true)"
[[ -x "${PYBIN:-}" ]] || PYBIN="$(command -v python3 || command -v python || echo python3)"

# ---------- 1) sitecustomize presence & path ----------
echo; echo "== sitecustomize =="
if PYTHONPATH=. PYTHONVERBOSE=1 "$PYBIN" -c 'print("ok")' 2>&1 | grep -qi sitecustomize; then
  ok "sitecustomize was loaded"
  if "$PYBIN" - <<'PY' 2>/dev/null; then :; fi
import os, inspect
try:
    import sitecustomize
    print("sitecustomize_file=", os.path.abspath(sitecustomize.__file__))
except Exception as e:
    print("sitecustomize import error:", e)
PY
else
  err "sitecustomize not loaded; ensure PYTHONPATH=. and restart the bot"
fi

# ---------- 2) Patch banner ----------
echo; echo "== patch banner =="
if grep -n '^\[patch\] simple create_order snap active' "$LOG" | tail -n1; then
  ok "patch activation line present"
else
  warn "patch line not found (check sitecustomize and restart)"
fi

# ---------- 3) Universe + Edge flow ----------
echo; echo "== universe & edge =="
egrep -i 'universe|ALLOWED_SYMBOLS|DYNAMIC_UNIVERSE' "$LOG" | tail -n20 || true
egrep -i '^\[edge\] (skip|check_before_order)' "$LOG" | tail -n40 || true

# ---------- 4) Pre-snap lines (entry-pre) ----------
echo; echo "== entry-pre (pre-snap) =="
if ! grep -ni 'entry-pre' "$LOG" | tail -n3; then
  warn "no entry-pre lines yet"
fi

# ---------- 5) step_size rejects (should be none) ----------
echo; echo "== step_size rejects (should be none) =="
if egrep -i 'open failed.*not multiple' "$LOG"; then
  err "found step_size rejects"
else
  ok "no step_size rejects"
fi

# ---------- 6) Last snap block (should precede ORDER_OK/filled) ----------
echo; echo "== last snap block =="
last_snap_ln="$(grep -n '^\[patch\] create_order snap' "$LOG" | tail -n1 | cut -d: -f1 || true)"
if [[ -n "${last_snap_ln}" ]]; then
  sed -n "${last_snap_ln},$((last_snap_ln+12))p" "$LOG"
else
  warn "no snap lines yet"
fi

# Detect lingering rejects after the last snap
if [[ -n "${last_snap_ln}" ]]; then
  # FIX: correct sed range terminator
  if sed -n "${last_snap_ln},\$p" "$LOG" | egrep -i 'open failed.*not multiple' >/dev/null; then
    warn "post-snap step_size rejects present (snapping might be too late in the flow)"
  fi
fi

# ---------- 7) Latest ORDER_OK / filled ----------
echo; echo "== last ORDER_OK / filled =="
egrep -n 'ORDER_OK|filled' "$LOG" | tail -n5 || warn "none yet"

# ---------- 8) Metrics quickscan (local exporter ports) ----------
echo; echo "== metrics quickscan =="
MP=""
for p in 9108 9109 9110 9111 9112; do
  if curl -fsS "http://127.0.0.1:$p/metrics" >/dev/null; then
    ok "metrics up on :$p"
    MP="$p"
    break
  fi
done
if [[ -n "$MP" ]]; then
  curl -s "http://127.0.0.1:$MP/metrics" | egrep -m1 'momentum_trades_total|^# HELP' || true
else
  warn "no local metrics exporter detected on 9108–9112"
fi

# ---------- 9) Prometheus query (distinguish absent vs 0) ----------
echo; echo "== Prom query: momentum_trades_total =="
HTTP_CODE="$(curl -s -o /tmp/mt.json -w '%{http_code}' "$PROM/api/v1/query?query=momentum_trades_total" || true)"
if [[ "$HTTP_CODE" != "200" ]]; then
  err "Prometheus query HTTP $HTTP_CODE"
  head -c 200 /tmp/mt.json || true
else
  # shellcheck disable=SC2086
  cat /tmp/mt.json | eval $JQ
  if grep -q '"result": \[\]' /tmp/mt.json; then
    warn "momentum_trades_total metric present but no series returned (no trades yet or different metric name)"
  fi
fi

# ---------- 9.1) Prom value (numeric only) ----------
echo; echo "== Prom value (numeric) =="
VAL=$(curl -s "$PROM/api/v1/query?query=momentum_trades_total" | python3 - <<'PY'
import sys, json
try:
    d=json.loads(sys.stdin.read() or '{}')
    r=d.get('data',{}).get('result',[])
    print(r[0]['value'][1] if r else 'NA')
except Exception:
    print('NA')
PY
)
echo "momentum_trades_total = ${VAL}"

# ---------- 5b) step_size rejects since last start ----------
echo; echo "== step_size rejects since last start =="
start_ln=$(grep -n 'Momentum bot started' "$LOG" | tail -n1 | cut -d: -f1 || true)
[[ -z "$start_ln" ]] && start_ln=1
if sed -n "${start_ln},\$p" "$LOG" | egrep -i 'open failed.*not multiple' >/dev/null; then
  sed -n "${start_ln},\$p" "$LOG" | egrep -i 'open failed.*not multiple'
else
  ok "none since last start"
fi

# ---------- 9.2) Exchange sanity (balances & min notional) ----------
echo; echo "== exchange sanity (balances & min notional) =="
python3 - <<'PY' || true
import os
try:
    import ccxt
    k=os.getenv('BINANCEUS_KEY'); s=os.getenv('BINANCEUS_SECRET')
    if not (k and s):
        print('binanceus creds not set; skipping')
    else:
        ex=ccxt.binanceus({'apiKey':k,'secret':s,'enableRateLimit':True,'options':{'defaultType':'spot','adjustForTimeDifference':True,'recvWindow':5000}})
        mkts=ex.load_markets()
        bal=ex.fetch_balance()
        free=bal.get('free',{})
        print('free USDT=', free.get('USDT',0), 'free USD=', free.get('USD',0))
        for sym in ('XRP/USDT','HBAR/USDT'):
            if sym in mkts:
                i=mkts[sym]
                limits=i.get('limits',{}) or {}
                cost=limits.get('cost',{}) if isinstance(limits.get('cost'), dict) else {}
                print(sym, 'min_cost=', cost.get('min'), 'amt_step=', (i.get('precision',{}) or {}).get('amount'))
except Exception as e:
    print('ccxt check skipped:', e)
PY

# ---------- 6b) snap → order check ----------
echo; echo "== snap → order check =="
last_snap_ln2="$(grep -n '^\[patch\] create_order snap' "$LOG" | tail -n1 | cut -d: -f1 || true)"
if [[ -n "$last_snap_ln2" ]]; then
  if ! sed -n "${last_snap_ln2},$((last_snap_ln2+20))p" "$LOG" | egrep -i 'ORDER_OK|filled' >/dev/null; then
    warn "snap seen but no ORDER_OK/filled within ~20 lines"
  else
    ok "snap followed by ORDER_OK/filled"
  fi
else
  warn "no snap lines yet"
fi

# ---------- 11) Summary (exit code) ----------
echo; echo "== summary =="
FAIL=0
if ! grep -q '^\[patch\] simple create_order snap active' "$LOG"; then warn "patch banner missing"; FAIL=1; fi
if egrep -qi 'open failed.*not multiple' "$LOG"; then warn "step_size rejects present"; FAIL=1; fi
if [[ "${VAL:-NA}" = "NA" ]]; then warn "Prom metric absent (or no trades yet)"; fi
if [[ $FAIL -eq 0 ]]; then ok "✅ all green"; else err "❌ issues detected"; fi

# ---------- Optional follow ----------
if [[ "${FOLLOW}" = "1" ]]; then
  echo; ok "FOLLOW=1 set — tailing $LOG (Ctrl-C to exit)…"
  tail -f "$LOG"
fi
