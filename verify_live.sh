#!/usr/bin/env bash
set -euo pipefail
LOG="runtime/logs/momentum.fg.log"
METRICS_PORT="${METRICS_PORT:-9112}"

echo "== startup/ws/risk lines =="
egrep -ni "^\[patch\]|Bot start|WS_|websocket|var95|HEARTBEAT|APPROVAL|RISK|ORDER_" "$LOG" | tail -n 60 || true

echo; echo "== exporter (:${METRICS_PORT}) peek =="
curl -s "http://127.0.0.1:${METRICS_PORT}/metrics" | egrep -m1 "momentum_trades_total|var95|heartbeat|exposure" || echo "no exporter yet"

echo; echo "== step_size rejects (should be none) =="
egrep -i "open failed.*not multiple" "$LOG" || echo "none"

echo; echo "== recent audit (HEARTBEAT / ORDER / RISK) =="
tail -n 20 runtime/audit/*.jsonl 2>/dev/null | egrep -i "HEARTBEAT|ORDER_|RISK|var95|unreal|exposure" || true
