#!/usr/bin/env bash
set -euo pipefail

# Activate virtualenv if present and pick python
if [ -d .venv ]; then
  # shellcheck disable=SC1091
  . ./.venv/bin/activate
  PY=python
elif [ -d venv ]; then
  # shellcheck disable=SC1091
  . ./venv/bin/activate
  PY=python
else
  PY=python
fi

# Ensure logs dir exists before we write into it
mkdir -p runtime/logs

# 0) Load env (after you’ve put NEW, IP-whitelisted keys in .env.live)
set -a; . ./.env.live; set +a

echo "==[1/3] CCXT auth check=="
"$PY" - <<'PY'
import os
try:
    import ccxt
except Exception as e:
    print("ccxt import failed:", e)
    raise
ex = ccxt.binanceus({
    'apiKey': os.getenv('BINANCEUS_KEY') or os.getenv('BINANCEUS_API_KEY'),
    'secret': os.getenv('BINANCEUS_SECRET') or os.getenv('BINANCEUS_API_SECRET'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',
        'adjustForTimeDifference': True,
        'recvWindow': 5000,
    },
})
mkts = ex.load_markets()
print("markets:", "XRP/USDT" in mkts, "HBAR/USDT" in mkts)
bal = ex.fetch_balance()
print("free USDT:", (bal.get('free') or {}).get('USDT', 0))
PY
echo

echo "==[2/3] Monitoring up?=="
# Ensure stack is up and exporter running
( docker compose -f docker-compose.stack.yml up -d >/dev/null 2>&1 || true ) || ( docker-compose -f docker-compose.stack.yml up -d >/dev/null 2>&1 || true )
( make start-treasury-exporter >/dev/null 2>&1 || true )
( make prom-reload PROM_URL=http://localhost:9090 >/dev/null 2>&1 || true )

TARGETS_JSON=$(curl -s http://localhost:9090/api/v1/targets || true)
if command -v jq >/dev/null 2>&1; then
  echo "$TARGETS_JSON" | jq -r '.data.activeTargets[].labels.job' | sort -u
else
  echo "$TARGETS_JSON" | "$PY" - <<'PY'
import sys, json
try:
    data = json.load(sys.stdin)
    jobs = sorted({t.get('labels',{}).get('job') for t in data.get('data',{}).get('activeTargets', []) if t.get('labels',{}).get('job')})
    for j in jobs:
        print(j)
except Exception:
    pass
PY
fi

echo

echo "==[3/3] Edge gate firing (dry-tick)=="
# Provide an approval token so entry path runs in paper
APPROVAL_TOKEN=dry-verify SINGLE_TICK=1 MODE=paper DRY_RUN=1 "$PY" trillion_bot_momentum.py --once >> runtime/logs/momentum-once.log 2>&1 || true
( grep -E '\[edge\]' runtime/logs/* 2>/dev/null | tail -n 3 ) || echo "[no edge lines yet]"
