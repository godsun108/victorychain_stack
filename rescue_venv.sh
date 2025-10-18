#!/usr/bin/env bash
set -euo pipefail

echo "== repo root check =="
test -f "trillion_bot_momentum.py" || { echo "❌ Not in repo root"; pwd; ls -al; exit 1; }

# --- pick python3 (prefer Homebrew path on macOS) ---
PYBIN="$(command -v python3 || true)"
if [ -z "${PYBIN}" ] && [ -x /opt/homebrew/bin/python3 ]; then
  PYBIN=/opt/homebrew/bin/python3
fi
[ -x "${PYBIN:-}" ] || { echo "❌ python3 not found in PATH"; exit 1; }
echo "Using python: $PYBIN"
"$PYBIN" -V

# --- create venv (venv → virtualenv fallback) ---
echo "== nuking old .venv =="
deactivate >/dev/null 2>&1 || true
rm -rf .venv

echo "== creating .venv via venv =="
if "$PYBIN" -c "import venv" 2>/dev/null; then
  "$PYBIN" -m venv -vvv .venv || true
fi

if [ ! -f .venv/bin/activate ]; then
  echo "== venv missing; ensuring ensurepip then retry =="
  "$PYBIN" -m ensurepip --upgrade || true
  "$PYBIN" -m venv -vvv .venv || true
fi

if [ ! -f .venv/bin/activate ]; then
  echo "== falling back to virtualenv =="
  "$PYBIN" -m pip install --user -q virtualenv
  "$PYBIN" -m virtualenv -vvv .venv
fi

test -f .venv/bin/activate || { echo "❌ venv creation failed (no .venv/bin/activate)"; exit 1; }

# --- activate & install deps (pinned) ---
# shellcheck disable=SC1091
. .venv/bin/activate
echo "Activated: ${VIRTUAL_ENV:-<none>}"
python -V

echo "== upgrade pip/setuptools/wheel =="
python -m pip install -q -U pip setuptools wheel

echo "== install pinned deps =="
python -m pip install -q \
  "ccxt>=4,<5" \
  "prometheus-client>=0.20,<0.24" \
  "websockets>=12,<13" \
  "numpy>=1.26,<2" \
  "python-dotenv>=1,<2"

echo "== sanity imports =="
python - <<'PY'
import ccxt, numpy, prometheus_client, websockets, dotenv
print("✅ deps OK")
PY

echo "✅ .venv ready. Activate any time:  . .venv/bin/activate"

# --- optional quick run helper (comment out if you don’t want to auto-run) ---
if [ "${RUN_NOW:-0}" = "1" ]; then
  echo "== optional: foreground run =="
  mkdir -p runtime/logs
  : > runtime/logs/momentum.fg.log
  export PYTHONUNBUFFERED=1 PYTHONPATH=. MODE=live DRY_RUN=false
  python -u trillion_bot_momentum.py 2>&1 | tee runtime/logs/momentum.fg.log
fi
