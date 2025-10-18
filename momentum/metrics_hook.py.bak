#!/usr/bin/env python3
"""Prometheus metrics hook for the momentum (Trillion) bot.

Use inside runtime:
    from momentum.metrics_hook import start_metrics, inc_trade, set_open_positions, set_weekly_pnl
    start_metrics(9108)
    inc_trade("BTCUSDT", "BUY")

Functions are no-ops until start_metrics is called (idempotent).
"""
from typing import Optional
from prometheus_client import Counter, Gauge, start_http_server
import threading

_trade_counter = Counter(
    "momentum_trades_total",
    "Momentum bot trades total",
    ["symbol", "side"],
)
_open_positions = Gauge(
    "momentum_open_positions",
    "Open position count per symbol",
    ["symbol"],
)
_weekly_pnl = Gauge(
    "momentum_weekly_pnl_usd",
    "Week-to-date realized PnL (USD)",
)
_started = False
_lock = threading.Lock()


def start_metrics(port: int = 9108):
    global _started
    with _lock:
        if _started:
            return
        start_http_server(port)
        _started = True


def inc_trade(symbol: str, side: str):
    if not _started:
        return
    _trade_counter.labels(symbol=symbol, side=side.upper()).inc()


def set_open_positions(symbol: str, count: int):
    if not _started:
        return
    _open_positions.labels(symbol=symbol).set(count)


def set_weekly_pnl(value: float):
    if not _started:
        return
    _weekly_pnl.set(float(value))
