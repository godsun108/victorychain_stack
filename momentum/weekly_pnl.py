#!/usr/bin/env python3
"""Weekly (rolling 7d) realized PnL computation for the momentum bot.

Reads the JSONL governance / trading ledger and aggregates net realized
profit over the last 7 * 24h window based on `trade_close` events.

A `trade_close` line is expected to contain either a pre-computed
`profit_usd_net` field, or (fallback) the fields: `entry_price`,
`exit_price`, and `amount` to compute gross PnL. If fees/slippage are not
available the fallback becomes a gross approximation.

Usage:
    from momentum.weekly_pnl import compute_weekly_pnl
    v = compute_weekly_pnl("runtime/ledger/live_ledger.jsonl")
    print("Weekly PnL:", v)

Set env var EMIT_WEEKLY_PNL=1 on exactly ONE process to avoid duplicate
reporting to the Prometheus gauge.
"""
from __future__ import annotations
import json, os, math
from datetime import datetime, timedelta, timezone
from typing import Iterable, Dict, Any

__all__ = ["compute_weekly_pnl"]

ROLLING_WINDOW_HOURS = 24 * 7


def _iter_ledger(path: str) -> Iterable[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def compute_weekly_pnl(path: str) -> float:
    """Return rolling 7d realized net PnL (USD).

    Only includes trade_close events within the last 7*24 hours relative
    to current UTC. Missing / malformed numbers are skipped gracefully.
    """
    cutoff = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(
        hours=ROLLING_WINDOW_HOURS
    )
    total = 0.0
    for rec in _iter_ledger(path):
        if rec.get("event") != "trade_close":
            continue
        ts_raw = rec.get("ts")
        dt = None
        if isinstance(ts_raw, str):
            try:
                # Expect ISO8601 with Z
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except Exception:
                dt = None
        if dt is None:
            # allow int timestamp
            try:
                dt = datetime.utcfromtimestamp(float(ts_raw)).replace(
                    tzinfo=timezone.utc
                )
            except Exception:
                continue
        if dt < cutoff:
            continue
        if "profit_usd_net" in rec:
            try:
                total += float(rec.get("profit_usd_net") or 0.0)
            except Exception:
                pass
        else:
            try:
                entry = float(rec.get("entry_price") or 0.0)
                exitp = float(rec.get("exit_price") or 0.0)
                amt = float(rec.get("amount") or 0.0)
                total += (exitp - entry) * amt
            except Exception:
                pass
    return round(total, 8)


if __name__ == "__main__":  # simple manual test
    import sys

    p = sys.argv[1] if len(sys.argv) > 1 else "runtime/ledger/live_ledger.jsonl"
    print(compute_weekly_pnl(p))
