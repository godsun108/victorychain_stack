#!/usr/bin/env python3
"""Bot-aware Prometheus metrics hook (v2).

Adds a bot_id label so multiple runners can coexist.
Exposes:
  momentum_trades_total{symbol,side,bot_id}
  momentum_position_size{symbol,bot_id}        (signed base units)
  momentum_weekly_pnl_usd{bot_id}
  momentum_open_positions{symbol,bot_id} (optional count gauge, only if used)

API:
    from momentum.metrics_hook_v2 import (
        start_metrics, inc_trade, set_position_size, set_weekly_pnl,
        set_open_positions_count
    )

Call start_metrics(port, bot_id) exactly once per process.
"""
from __future__ import annotations
from prometheus_client import Counter, Gauge, start_http_server
from typing import Optional
import threading

_started = False
_lock = threading.Lock()
_bot_id: Optional[str] = None

# Metric objects (late init labels through .labels())
_trade_counter = Counter(
    "momentum_trades_total",
    "Momentum bot trades total (executed fills)",
    ["symbol", "side", "bot_id"],
)
_position_size = Gauge(
    "momentum_position_size",
    "Signed base position size per symbol (long>0 short<0)",
    ["symbol", "bot_id"],
)
_weekly_pnl = Gauge(
    "momentum_weekly_pnl_usd",
    "Rolling 7d realized PnL (USD)",
    ["bot_id"],
)
_open_positions_count = Gauge(
    "momentum_open_positions",
    "Open position COUNT per symbol (legacy / optional)",
    ["symbol", "bot_id"],
)


def start_metrics(port: int = 9108, bot_id: str = "default"):
    global _started, _bot_id
    with _lock:
        if _started:
            return
        _bot_id = bot_id
        start_http_server(port)
        _started = True


def inc_trade(symbol: str, side: str, bot_id: Optional[str] = None):
    if not _started:
        return
    _trade_counter.labels(
        symbol=symbol, side=side.upper(), bot_id=bot_id or _bot_id
    ).inc()


def set_position_size(symbol: str, size: float, bot_id: Optional[str] = None):
    if not _started:
        return
    _position_size.labels(symbol=symbol, bot_id=bot_id or _bot_id).set(float(size))


def set_open_positions_count(symbol: str, count: float, bot_id: Optional[str] = None):
    if not _started:
        return
    _open_positions_count.labels(symbol=symbol, bot_id=bot_id or _bot_id).set(
        float(count)
    )


def set_weekly_pnl(value: float, bot_id: Optional[str] = None):
    if not _started:
        return
    _weekly_pnl.labels(bot_id=bot_id or _bot_id).set(float(value))
