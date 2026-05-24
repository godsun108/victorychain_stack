#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Run a full admin-auth incident-recovery drill against a temporary env config.

Usage:
  ./scripts/run_admin_auth_recovery_drill.sh [options]

Options:
  --source-env <path>     Source env file to copy (default: .env)
  --port <n>              Drill API port (default: 9010)
  --startup-timeout <n>   Health/startup timeout seconds (default: 45)
  --help                  Show this help
EOF
}

source_env=".env"
port="9010"
startup_timeout="45"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-env)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --source-env" >&2
        exit 1
      fi
      source_env="$2"
      shift 2
      ;;
    --port)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --port" >&2
        exit 1
      fi
      port="$2"
      shift 2
      ;;
    --startup-timeout)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --startup-timeout" >&2
        exit 1
      fi
      startup_timeout="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$source_env" ]]; then
  echo "Source env file not found: $source_env" >&2
  exit 1
fi

if ! [[ "$port" =~ ^[0-9]+$ ]]; then
  echo "--port must be numeric" >&2
  exit 1
fi

if ! [[ "$startup_timeout" =~ ^[0-9]+$ ]]; then
  echo "--startup-timeout must be numeric" >&2
  exit 1
fi

root_dir="$(cd "$(dirname "$0")/.." && pwd)"
uvicorn_bin="${VICTORY_IMPACT_DRILL_UVICORN_BIN:-}"
if [[ -z "$uvicorn_bin" ]]; then
  if [[ -x "$root_dir/.venv_victoryimpact/bin/uvicorn" ]]; then
    uvicorn_bin="$root_dir/.venv_victoryimpact/bin/uvicorn"
  elif command -v uvicorn >/dev/null 2>&1; then
    uvicorn_bin="$(command -v uvicorn)"
  fi
fi
if [[ -z "$uvicorn_bin" ]] || [[ ! -x "$uvicorn_bin" ]]; then
  echo "Unable to locate executable uvicorn binary for drill runtime." >&2
  echo "Set VICTORY_IMPACT_DRILL_UVICORN_BIN or provision .venv_victoryimpact/bin/uvicorn." >&2
  exit 1
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
artifacts_dir="$root_dir/runtime/drills"
mkdir -p "$artifacts_dir"
drill_log="$artifacts_dir/admin_auth_recovery_drill_${timestamp}.log"
drill_db="$artifacts_dir/admin_auth_recovery_drill_${timestamp}.db"
tmp_dir="$(mktemp -d)"
tmp_env="$tmp_dir/.env.drill"
session_payload="$tmp_dir/session_payload.json"
post_disable_payload="$tmp_dir/post_disable_payload.json"

server_pid=""

cleanup() {
  if [[ -n "$server_pid" ]] && kill -0 "$server_pid" >/dev/null 2>&1; then
    kill "$server_pid" >/dev/null 2>&1 || true
    wait "$server_pid" >/dev/null 2>&1 || true
  fi
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

wait_for_health() {
  local attempt=0
  while (( attempt < startup_timeout )); do
    if [[ -n "$server_pid" ]] && ! kill -0 "$server_pid" >/dev/null 2>&1; then
      echo "Drill API exited early. Check $drill_log" >&2
      return 1
    fi
    if curl --silent --show-error --fail --max-time 2 "http://127.0.0.1:${port}/" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    attempt=$((attempt + 1))
  done
  echo "Timed out waiting for drill API on port $port" >&2
  return 1
}

start_server() {
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $port is already in use before drill server startup" >&2
    exit 1
  fi
  (
    cd "$root_dir"
    python3 - "$tmp_env" "$uvicorn_bin" "$port" "$drill_db" <<'PY'
import os
import sys
from pathlib import Path

env_file = Path(sys.argv[1])
uvicorn_bin = sys.argv[2]
port = sys.argv[3]
drill_db = sys.argv[4]

env = dict(os.environ)
for raw_line in env_file.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    if line.startswith("export "):
        line = line[len("export ") :].strip()
    if "=" not in line:
        continue
    key, value = line.split("=", 1)
    env[key.strip()] = value.strip()

env["DATABASE_URL"] = f"sqlite:///{drill_db}"
env["APP_ENV"] = "dev"
env["PUBLIC_WEB_MODE"] = "false"
env["INHOUSE_ONLY_MODE"] = "false"

os.execvpe(
    uvicorn_bin,
    [
        uvicorn_bin,
        "src.victory_impact.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        port,
    ],
    env,
)
PY
  ) >>"$drill_log" 2>&1 &
  server_pid="$!"
  wait_for_health
}

stop_server() {
  if [[ -n "$server_pid" ]] && kill -0 "$server_pid" >/dev/null 2>&1; then
    kill "$server_pid" >/dev/null 2>&1 || true
    wait "$server_pid" >/dev/null 2>&1 || true
  fi
  server_pid=""
  local attempt=0
  while lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; do
    if (( attempt == 5 )); then
      lingering_pids="$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | tr '\n' ' ')"
      if [[ -n "${lingering_pids:-}" ]]; then
        # Isolated drill port only; force clear lingering listeners.
        kill ${lingering_pids} >/dev/null 2>&1 || true
      fi
    fi
    if (( attempt == 10 )); then
      lingering_pids="$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | tr '\n' ' ')"
      if [[ -n "${lingering_pids:-}" ]]; then
        kill -9 ${lingering_pids} >/dev/null 2>&1 || true
      fi
    fi
    if (( attempt >= 15 )); then
      echo "Port $port still listening after drill server stop" >&2
      return 1
    fi
    sleep 1
    attempt=$((attempt + 1))
  done
}

cp "$source_env" "$tmp_env"

echo "[drill] bootstrap recovery phase: enabling bootstrap in temporary env"
"$root_dir/scripts/rotate_admin_tokens.sh" --env-file "$tmp_env" --enable-bootstrap --roles admin >/dev/null

bootstrap_mapping="$(sed -n 's/^ADMIN_BOOTSTRAP_TOKENS=//p' "$tmp_env")"
bootstrap_token="$(printf "%s" "$bootstrap_mapping" | cut -d',' -f1 | cut -d':' -f1)"
if [[ -z "$bootstrap_token" ]]; then
  echo "Failed to parse bootstrap token from temporary env" >&2
  exit 1
fi

echo "[drill] starting isolated drill API on port $port"
start_server

echo "[drill] minting admin bearer session via bootstrap token"
curl --silent --show-error --fail \
  -X POST "http://127.0.0.1:${port}/admin/auth/session" \
  -H "x-api-token: ${bootstrap_token}" \
  -H "Content-Type: application/json" >"$session_payload"

bearer_token="$(
  python3 - "$session_payload" <<'PY'
import json
import sys
with open(sys.argv[1], "r", encoding="utf-8") as fh:
    payload = json.load(fh)
token = payload.get("token", "")
if not token:
    raise SystemExit(1)
print(token, end="")
PY
)"

echo "[drill] verifying bearer access and revoke flow"
curl --silent --show-error --fail \
  "http://127.0.0.1:${port}/admin/treasury" \
  -H "Authorization: Bearer ${bearer_token}" >/dev/null

curl --silent --show-error --fail \
  -X POST "http://127.0.0.1:${port}/admin/auth/revoke" \
  -H "Authorization: Bearer ${bearer_token}" >/dev/null

echo "[drill] post-recovery hardening: disabling bootstrap"
"$root_dir/scripts/rotate_admin_tokens.sh" --env-file "$tmp_env" >/dev/null

stop_server
start_server

echo "[drill] asserting bootstrap session mint is blocked after disablement"
http_code="$(
  curl --silent --show-error \
    -o "$post_disable_payload" \
    -w "%{http_code}" \
    -X POST "http://127.0.0.1:${port}/admin/auth/session" \
    -H "x-api-token: ${bootstrap_token}" \
    -H "Content-Type: application/json"
)"
if [[ "$http_code" != "401" ]]; then
  echo "Expected 401 after bootstrap disablement, got $http_code" >&2
  cat "$post_disable_payload" >&2 || true
  exit 1
fi

if ! grep -q "admin_auth_mode bootstrap_enabled=False" "$drill_log"; then
  echo "Expected admin_auth_mode bootstrap_enabled=False in drill log: $drill_log" >&2
  exit 1
fi

echo "[drill] PASS"
echo "[drill] log: $drill_log"
echo "[drill] db: $drill_db"
