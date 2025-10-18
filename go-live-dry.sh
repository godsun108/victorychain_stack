#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
LOG_DIR="runtime/logs"
PID_DIR="runtime/pids"
mkdir -p "$LOG_DIR" "$PID_DIR" runtime/reinvest

stamp() { date "+%Y-%m-%d %H:%M:%S"; }
log() { echo "[$(stamp)] $*"; }

# Load env
if [ -f .env.live ]; then
  set -a
  . ./.env.live
  set +a
fi
export DRY_RUN=true

# Default URLs for host checks
PROM_URL=${PROM_URL:-http://localhost:9090}
AGENT_URL=${AGENT_URL:-http://localhost:8080}

# Detect venv
if [ -d .venv ]; then VENV=.venv; elif [ -d venv ]; then VENV=venv; else VENV=.venv; fi
. "$VENV"/bin/activate || true

log "== GO-LIVE DRY START =="
log "Apply XRP/HBAR reinvest preset (direct)"
python - <<'PY'
import json, os
preset = {
  "name": "xrp-hbar-preset",
  "weights": {
    "XRP/USDT": 0.6,
    "HBAR/USDT": 0.4
  }
}
os.makedirs('runtime/reinvest', exist_ok=True)
with open('runtime/reinvest/preset.json','w') as f:
    json.dump(preset, f, indent=2)
print('Wrote runtime/reinvest/preset.json')
PY

log "Bring up monitoring stack (Prometheus/Grafana/Agent)"
docker compose -f docker-compose.stack.yml up -d --build || true

log "Ensure Prometheus reload enabled and reload config at $PROM_URL"
curl -fsS -X POST "$PROM_URL/-/reload" >/dev/null 2>&1 || true

# Start treasury exporter if not up
TREASURY_METRICS_PORT=${TREASURY_METRICS_PORT:-9112}
if ! curl -sf "http://127.0.0.1:${TREASURY_METRICS_PORT}/metrics" >/dev/null 2>&1; then
  log "Start treasury exporter on :${TREASURY_METRICS_PORT}"
  nohup python scripts/treasury_exporter.py >>"$LOG_DIR/treasury_exporter.log" 2>&1 & echo $! >"$PID_DIR/treasury_exporter.pid" || true
  # wait until up (5s timeout)
  for i in $(seq 1 10); do
    if curl -sf "http://127.0.0.1:${TREASURY_METRICS_PORT}/metrics" >/dev/null 2>&1; then break; fi
    sleep 0.5
  done
fi

log "Run momentum-once (dry-run)"
MODE=paper SINGLE_TICK=1 python trillion_bot_momentum.py --once 2>&1 | tee "$LOG_DIR/momentum-once.log" || true

log "Edge log tail (if any)"
( tail -n 200 "$LOG_DIR/momentum-once.log" 2>/dev/null | grep "\[edge\]" | tail -n 5 ) || true

log "Prometheus target summary"
( curl -sf "$PROM_URL/api/v1/targets" | head -c 2000 || true )

log "Treasury exporter metrics head"
( curl -sf "http://127.0.0.1:${TREASURY_METRICS_PORT}/metrics" | egrep -E "^vc_(treasury|reinvest|realized|last)|^vc_reinvest_preset_weight" || true ) | head -n 20

log "== GO-LIVE DRY DONE =="
