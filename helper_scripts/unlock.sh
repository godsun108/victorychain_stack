#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

TOKEN=${APPROVAL_TOKEN:-}
TRACE_ID=${TRACE_ID:-}
ASSUME_YES=0

usage() {
  echo "Usage: $0 [-y] [-t <trace_id>]" >&2
  echo "  -y            Do not prompt for confirmation" >&2
  echo "  -t trace_id   Optional trace id to display/target" >&2
}

while getopts ":yt:h" opt; do
  case $opt in
    y) ASSUME_YES=1 ;;
    t) TRACE_ID="$OPTARG" ;;
    h) usage; exit 0 ;;
    \?) echo "Invalid option: -$OPTARG" >&2; usage; exit 1 ;;
    :)  echo "Option -$OPTARG requires an argument." >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$TOKEN" ]]; then
  echo "APPROVAL_TOKEN env var required (for action=vault.unlock)" >&2
  exit 1
fi

if (( ASSUME_YES == 0 )); then
  if [[ -t 0 ]]; then
    prompt="Confirm unlock"
    [[ -n "$TRACE_ID" ]] && prompt+=" for TRACE_ID=$TRACE_ID"
    read -r -p "$prompt? (yes/no) " ans
    case ${ans:-no} in
      yes|y|YES|Y) : ;;
      *) echo "Aborted." ; exit 1 ;;
    esac
  else
    echo "Refusing to prompt on non-interactive stdin; pass -y to confirm." >&2
    exit 1
  fi
fi

# Attempt unlock via Python governance.vault, log immutable attempt
APPROVAL_TOKEN="$TOKEN" TRACE_ID="$TRACE_ID" python - <<'PY'
import os
from governance import vault

token = os.environ.get('APPROVAL_TOKEN','')
trace_id = os.environ.get('TRACE_ID') or None

s = vault.status()
if not s.get('locked'):
    print('Already unlocked')
    raise SystemExit(0)

try:
    vault.unlock(token)
    print('LOCKDOWN cleared')
except Exception as e:
    print(f'Unlock failed: {e}')
    raise
PY
