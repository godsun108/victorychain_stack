#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv_victoryimpact"
PYTHON_BIN="$VENV_DIR/bin/python"
PORT="${1:-${VICTORY_IMPACT_API_PORT:-9000}}"
HOST="${VICTORY_IMPACT_API_HOST:-0.0.0.0}"
PID_FILE="$ROOT_DIR/.victory_impact_api.pid"
LOG_FILE="$ROOT_DIR/.victory_impact_api.log"
START_TIMEOUT_SECONDS="${VICTORY_IMPACT_START_TIMEOUT_SECONDS:-30}"
HEALTH_CHECK_TIMEOUT_SECONDS="${VICTORY_IMPACT_HEALTH_CHECK_TIMEOUT_SECONDS:-3}"
HEALTH_URL="${VICTORY_IMPACT_HEALTH_URL:-http://127.0.0.1:${PORT}/}"
SYNC_REQUIREMENTS_ON_START="${VICTORY_IMPACT_SYNC_REQUIREMENTS_ON_START:-true}"

is_listening_on_port() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

pid_is_running() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1
}

healthcheck_ok() {
  local url="$1"
  local timeout_s="$2"
  local body=""
  body="$(curl --silent --show-error --fail --max-time "$timeout_s" "$url" 2>/dev/null || true)"
  if [[ -z "$body" ]]; then
    return 1
  fi
  if ! printf "%s" "$body" | python3 -c 'import json,sys; d=json.load(sys.stdin); raise SystemExit(0 if d.get("status")=="ok" else 1)' >/dev/null 2>&1; then
    return 1
  fi
  return 0
}

if [[ ! -x "$VENV_DIR/bin/uvicorn" ]] || [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Missing venv or uvicorn at $VENV_DIR. Create it and install requirements first." >&2
  exit 1
fi

if [[ "$SYNC_REQUIREMENTS_ON_START" == "true" ]]; then
  echo "Syncing runtime dependencies from requirements.txt..."
  "$PYTHON_BIN" -m pip install -r "$ROOT_DIR/requirements.txt" >/dev/null
  "$PYTHON_BIN" -m pip check >/dev/null
fi

if [[ -f "$PID_FILE" ]]; then
  EXISTING_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if pid_is_running "$EXISTING_PID"; then
    echo "Victory Impact API already running with PID $EXISTING_PID (PID file: $PID_FILE)." >&2
    exit 1
  fi
  echo "Removing stale PID file $PID_FILE."
  rm -f "$PID_FILE"
fi

if is_listening_on_port "$PORT"; then
  echo "Port $PORT is already in use by another process. Choose a different port or stop the existing process." >&2
  exit 1
fi

LAN_IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
if [[ -z "${LAN_IP}" ]]; then
  LAN_IP="127.0.0.1"
fi

CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173,http://${LAN_IP}:5173,http://${LAN_IP}:4173,capacitor://localhost,ionic://localhost,http://localhost"

cd "$ROOT_DIR"
nohup env CORS_ORIGINS="$CORS_ORIGINS" "$VENV_DIR/bin/uvicorn" src.victory_impact.main:app --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

for _ in $(seq 1 "$START_TIMEOUT_SECONDS"); do
  if is_listening_on_port "$PORT"; then
    break
  fi
  if ! pid_is_running "$PID"; then
    echo "Victory Impact API process exited before binding to port $PORT. Check $LOG_FILE" >&2
    rm -f "$PID_FILE"
    exit 1
  fi
  sleep 1
done

if ! is_listening_on_port "$PORT"; then
  echo "Failed to start Victory Impact API. Check $LOG_FILE" >&2
  if pid_is_running "$PID"; then
    kill "$PID" >/dev/null 2>&1 || true
  fi
  rm -f "$PID_FILE"
  exit 1
fi

for _ in $(seq 1 "$START_TIMEOUT_SECONDS"); do
  if healthcheck_ok "$HEALTH_URL" "$HEALTH_CHECK_TIMEOUT_SECONDS"; then
    break
  fi
  sleep 1
done

if ! healthcheck_ok "$HEALTH_URL" "$HEALTH_CHECK_TIMEOUT_SECONDS"; then
  echo "Victory Impact API bound to port $PORT but healthcheck failed at $HEALTH_URL." >&2
  if pid_is_running "$PID"; then
    kill "$PID" >/dev/null 2>&1 || true
  fi
  rm -f "$PID_FILE"
  echo "--- recent log tail ---" >&2
  tail -n 40 "$LOG_FILE" >&2 || true
  exit 1
fi

echo "Victory Impact API started on port $PORT"
echo "PID: $PID"
echo "Log: $LOG_FILE"
echo "Health: $HEALTH_URL"
