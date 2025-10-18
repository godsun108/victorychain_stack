#!/usr/bin/env bash
# Rebuild clean venv + install pinned deps for trillion_bot_momentum.py
set -euo pipefail

# must be in repo root
test -f trillion_bot_momentum.py || { echo "❌ not in repo root"; pwd; ls -al; exit 1; }

echo "[bootstrap] removing old .venv"
deactivate >/dev/null 2>&1 || true
rm -rf .venv

PYBIN="$(command -v python3)" || { echo "❌ python3 missing"; exit 1; }

echo "[bootstrap] creating venv with $PYBIN"
"$PYBIN" -m venv .venv
. .venv/bin/activate
python -V

echo "[bootstrap] upgrading pip"
python -m pip install -U pip >/dev/null

echo "[bootstrap] installing pinned deps"
python -m pip install "ccxt>=4,<5" "prometheus-client>=0.20,<0.24" "websockets>=12,<13" "numpy>=1.26,<2" "python-dotenv>=1,<2" -q

echo "[bootstrap] sanity import test"
python - <<'PY'
import ccxt, numpy, prometheus_client, websockets, dotenv
print("✅ deps OK")
PY

echo "[bootstrap] done. Activate with:  . .venv/bin/activate"

