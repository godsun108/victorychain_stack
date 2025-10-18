#!/usr/bin/env bash
set -euo pipefail

# --- repo root guard ---
test -f trillion_bot_momentum.py || { echo "Run from repo root (trillion_bot_momentum.py not found)"; exit 1; }

# --- python pick ---
if [ -x .venv/bin/python ]; then PY=.venv/bin/python
elif [ -x venv/bin/python ]; then PY=venv/bin/python
else PY="$(command -v python3)"; fi
echo "[runner] using $PY"

# --- load env (optional) ---
[ -f .env.live ] && { set -a; . .env.live; set +a; }

# --- fast VaR warmup defaults (can be overridden in .env.live) ---
export VAR_BUCKET_SECS="${VAR_BUCKET_SECS:-10}"
export VAR_RET_WINDOW_SECS="${VAR_RET_WINDOW_SECS:-300}"

# --- metrics port + check ---
export METRICS_PORT="${METRICS_PORT:-9112}"
if command -v lsof >/dev/null 2>&1; then
  if lsof -i :"$METRICS_PORT" >/dev/null 2>&1; then
    echo "[runner] Port $METRICS_PORT busy"; exit 1
  fi
fi

# --- approval token to avoid skips ---
mkdir -p runtime runtime/logs
: "${APPROVAL_TOKEN_PATH:=runtime/APPROVAL_TOKEN.txt}"
# Ensure approval token not overwritten if exists
if [ ! -s "$APPROVAL_TOKEN_PATH" ]; then
  date +%s | awk '{print $1+3600}' > "$APPROVAL_TOKEN_PATH"
fi
export APPROVAL_TOKEN_PATH

# --- required keys ---
: "${BINANCEUS_KEY:?BINANCEUS_KEY missing}"
: "${BINANCEUS_SECRET:?BINANCEUS_SECRET missing}"

# --- clean shutdown ---
trap 'echo "[shutdown] stopping…"; pkill -f "trillion_bot_momentum.py" || true; exit 0' INT TERM

# --- fresh log + no stale procs ---
LOG="runtime/logs/momentum.fg.log"
: > "$LOG"
pkill -f "trillion_bot_momentum.py" 2>/dev/null || true

# --- Append: optional dry-run wrapper and symbol defaults ---
: "${ALLOWED_SYMBOLS:=XRP/USDT,HBAR/USDT}"
: "${DRY_RUN:=false}"
export ALLOWED_SYMBOLS DRY_RUN

echo "[runner] symbols=$ALLOWED_SYMBOLS dry_run=$DRY_RUN"

# --- run ---
export PYTHONUNBUFFERED=1 PYTHONPATH=. MODE=live DRY_RUN=false
exec "$PY" -u trillion_bot_momentum.py 2>&1 | tee "$LOG"
