"""
victory_bot/metrics.py
Prometheus metrics exporter for Victory Trading Bot
"""

from prometheus_client import start_http_server, Gauge, Counter, Histogram
from .config import METRICS_PORT

# Example metrics (expand as needed)
trade_profit = Gauge("victory_trade_profit", "Profit per trade", ["symbol"])
trade_count = Counter("victory_trade_count", "Total trades executed", ["symbol"])

# Always-on metrics
bot_status = Gauge("victory_bot_status", "Bot running status: 1=running, 0=stopped")
bot_balance = Gauge("victory_bot_balance_usdt", "Current USDT balance")

# Advanced metrics (from trillion bot)
daily_realized_pnl = Gauge(
    "momentum_daily_realized_pnl_usd", "Realized PnL today", ["bot_id"]
)
intraday_drawdown_pct = Gauge(
    "momentum_intraday_drawdown_pct", "Realized drawdown pct", ["bot_id"]
)
risk_blocking = Gauge(
    "momentum_risk_blocking", "Risk gate active", ["bot_id", "reason"]
)
order_rejects = Counter(
    "momentum_order_rejects_total", "Order rejects", ["bot_id", "reason"]
)
slippage_bps = Histogram(
    "momentum_slippage_bps",
    "Slippage bps",
    buckets=[1, 2, 5, 10, 20, 50, 100, 200, 500, 1000],
)
heartbeat_ts = Gauge("momentum_heartbeat_ts", "Heartbeat ts", ["bot_id"])
treasury_buffer = Gauge("momentum_realized_pnl_buffer_usd", "PnL buffer", ["bot_id"])
treasury_reserve_val = Gauge(
    "momentum_reserve_value_usd", "Reserve USD", ["bot_id", "reserve"]
)
treasury_last_ts = Gauge("momentum_treasury_last_bank_ts", "Last bank ts", ["bot_id"])
treasury_events = Counter(
    "momentum_treasury_bank_events_total", "Bank events", ["bot_id"]
)
gross_exposure = Gauge("momentum_gross_exposure_usd", "Gross exposure", ["bot_id"])
adaptive_risk_mult = Gauge(
    "momentum_adaptive_risk_multiplier", "Adaptive multiplier", ["bot_id"]
)

# Advanced analytics metrics
realized_pnl = Gauge("victory_realized_pnl_usd", "Realized P&L in USD", ["symbol"])
unrealized_pnl = Gauge(
    "victory_unrealized_pnl_usd", "Unrealized P&L in USD", ["symbol"]
)
trade_win_count = Counter(
    "victory_trade_win_count", "Number of winning trades", ["symbol"]
)
trade_loss_count = Counter(
    "victory_trade_loss_count", "Number of losing trades", ["symbol"]
)
max_drawdown = Gauge("victory_max_drawdown_pct", "Maximum drawdown percent", ["symbol"])
sharpe_ratio = Gauge("victory_sharpe_ratio", "Rolling Sharpe ratio", ["symbol"])
slippage_hist = Histogram(
    "victory_slippage_bps",
    "Order slippage in basis points",
    ["symbol"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 20, 50, 100],
)
api_latency = Histogram(
    "victory_api_latency_ms",
    "API latency in ms",
    buckets=[10, 50, 100, 200, 500, 1000, 2000, 5000],
)
error_count = Counter("victory_error_count", "System error count", ["type"])

# Start Prometheus exporter in main process
_exporter_started = False


def start_metrics_exporter():
    global _exporter_started
    if not _exporter_started:
        try:
            start_http_server(METRICS_PORT)
            print(
                f"[VictoryBot][metrics] Prometheus HTTP server started on port {METRICS_PORT}"
            )
        except Exception as e:
            print(
                f"[VictoryBot][metrics][ERROR] Failed to start Prometheus HTTP server: {e}"
            )
        _exporter_started = True


def update_bot_metrics(running: bool, usdt_balance: float):
    print(
        f"[VictoryBot][metrics] update_bot_metrics called: running={running}, "
        f"usdt_balance={usdt_balance}"
    )
    bot_status.set(1 if running else 0)
    bot_balance.set(usdt_balance)
    # Optionally, add more always-on metrics here


# For testing: curl -s http://localhost:9400/metrics | grep victory
