#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# load .env if present
if [ -f ".env" ]; then set -a; source .env; set +a; fi

# loop forever unless disabled
RUN_FOREVER="${RUN_FOREVER:-true}"
SLEEP_BETWEEN_SCANS_SEC="${SLEEP_BETWEEN_SCANS_SEC:-30}"

echo "[VictoryBot] 24/7 loop starting @ $(date)"
while true; do
  # drive the launcher with pre-filled answers: risks YES, strategy A, duration 8h, START
  python3 launch_live_trading.py <<EOF
YES I UNDERSTAND RISKS
YES
A
8
START LIVE TRADING
EOF

  echo "[VictoryBot] cycle ended @ $(date). Sleeping ${SLEEP_BETWEEN_SCANS_SEC}s..."
  sleep "${SLEEP_BETWEEN_SCANS_SEC}"

  if [ "${RUN_FOREVER}" != "true" ]; then
    echo "[VictoryBot] RUN_FOREVER=false; exiting."
    exit 0
  fi
done
