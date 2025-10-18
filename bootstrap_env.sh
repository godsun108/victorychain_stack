#!/usr/bin/env bash
set -euo pipefail

echo "== repo root check =="
test -f "trillion_bot_momentum.py" || { echo "❌ Not in repo root"; pwd; ls -al; exit 1; }

# Pick a python3
PYBIN="$(command -v python3 || true)"
if [ -z "${PYBIN}" ]; then
  [ -x "/opt/homebrew/bin/python3" ] && PYBIN="/opt/homebrew/bin/python3"
fi
[ -x "${PYBIN:-}" ] || { echo "❌ python3 not found in PATH"; exit 1; }
echo "Using python: $PYBIN"
"$PYBIN" -V

# Nuke any old env
echo "== removing old .venv =="
deactivate >/dev/null 2>&1 || true
rm -rf .venv

echo "== creating venv (.venv) =="
if "$PYBIN" -c "import venv" 2>/dev/null; then
  "$PYBIN" -m venv .venv || true
fi

# Fallback to virtualenv if venv failed
if [ ! -f .venv/bin/activate ]; then
  echo "venv module failed or missing; installing virtualenv fallback…"
  "$PYBIN" -m pip install --user -q virtualenv
  "$PYBIN" -m virtualenv .venv
fi

test -f .venv/bin/activate || { echo "❌ venv creation failed (no .venv/bin/activate)"; exit 1; }

# Activate
# shellcheck disable=SC1091
. .venv/bin/activate
echo "Activated: ${VIRTUAL_ENV:-<none>}"
python -V

echo "== upgrading pip/setuptools/wheel =="
python -m pip install -q -U pip setuptools wheel

echo "== installing pinned deps =="
python -m pip install -q \
  "ccxt>=4,<5" \
  "prometheus-client>=0.20,<0.24" \
  "websockets>=12,<13" \
  "numpy>=1.26,<2" \
  "python-dotenv>=1,<2"

echo "== sanity import check =="
python - <<'PY'
import ccxt, numpy, prometheus_client, websockets, dotenv
print("✅ deps OK")
PY

echo "✅ venv ready at .venv"
echo "👉 activate any time with:  . .venv/bin/activate"
