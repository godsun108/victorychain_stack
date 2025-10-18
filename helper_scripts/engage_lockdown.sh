#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Usage: engage_lockdown.sh [-y] [-r reason] [-t trace_id]
#  -y            Do not prompt for confirmation
#  -r reason     Reason for lockdown (default: manual_cli_lockdown)
#  -t trace_id   Optional trace id; if omitted, one will be generated

CONFIRM=1
REASON=${LOCK_REASON:-}
TRACE_ID=${TRACE_ID:-}

while getopts ":yr:t:h" opt; do
  case $opt in
    y) CONFIRM=0 ;;
    r) REASON="$OPTARG" ;;
    t) TRACE_ID="$OPTARG" ;;
    h)
      echo "Usage: $0 [-y] [-r reason] [-t trace_id]" ; exit 0 ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2 ; exit 1 ;;
    :)  echo "Option -$OPTARG requires an argument." >&2 ; exit 1 ;;
  esac
done

if [[ -z "${REASON}" ]]; then
  REASON="manual_cli_lockdown"
fi

if (( CONFIRM )); then
  echo "About to engage LOCKDOWN"
  echo "  reason   = ${REASON}"
  if [[ -n "${TRACE_ID}" ]]; then
    echo "  trace_id = ${TRACE_ID}"
  else
    echo "  trace_id = <auto-generate>"
  fi
  read -r -p "Proceed? [y/N] " ans
  case ${ans:-N} in
    y|Y|yes|YES) : ;;
    *) echo "Aborted." ; exit 1 ;;
  esac
fi

# Engage emergency lockdown via Python governance.vault
LOCK_REASON="$REASON" TRACE_ID="${TRACE_ID}" exec python - <<'PY'
import os, sys, uuid
try:
    from governance import vault
except Exception as e:
    print(f"ERROR: cannot import governance.vault: {e}", file=sys.stderr)
    raise

reason = os.environ.get('LOCK_REASON') or 'manual_cli_lockdown'
trace_id = os.environ.get('TRACE_ID') or ''
if not trace_id:
    trace_id = str(uuid.uuid4())

vault.lockdown(reason, trace_id)
print(f'LOCKDOWN engaged | reason={reason} | trace_id={trace_id}')
PY
