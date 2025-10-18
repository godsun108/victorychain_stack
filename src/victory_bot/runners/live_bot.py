"""
victory_bot/runners/live_bot.py
Main runner for Victory Trading Bot (24/7/365 live trading)
"""

import asyncio
import os
import json  # Added for fallback logic
import logging
import signal
from typing import List, Dict
from logging.handlers import RotatingFileHandler
import requests
import ccxt

from victory_bot.execution.btc_free import BTCFreeExecutionEngine
from victory_bot.risk import all_risk_gates_open
from victory_bot.universe import get_dynamic_symbol_universe
from victory_bot.config import RESERVE_ASSETS, MIN_RESERVE_RATIO
from victory_bot.metrics import start_metrics_exporter
from victory_bot.strategies.momentum_selector import MomentumSelector
from victory_bot.strategies.position_sizing import PositionSizer
from victory_bot.strategies.volatility_breakout import VolatilityBreakout
from victory_bot.strategies.pair_trading import PairTrading
from victory_bot.strategies.ml_signals import MLSignals
from victory_bot.strategies.event_driven import EventDriven
from victory_bot.strategies.dynamic_hedging import DynamicHedging
from victory_bot.strategies.yield_farming import YieldFarming
from victory_bot.strategies.portfolio_insurance import PortfolioInsurance
from victory_bot.strategies.multi_timeframe_momentum import MultiTimeframeMomentum
from victory_bot.strategies.mean_reversion import MeanReversion
from dotenv import load_dotenv

load_dotenv()

from victory_bot.utils.binance_ws import stream_all_usdt_prices_and_candles
from victory_bot.utils.huggingface_sentiment import analyze_sentiment
from victory_bot.utils.news_fetcher import fetch_latest_headlines

# TODO: Fix import if module exists or update path if moved
try:
    from victory_bot.utils.price_cache import get_candles
except ImportError:
    # Fallback: define a dummy async get_candles or update this import to the correct location
    async def get_candles(symbol):
        # Dummy fallback, replace with actual implementation
        return []


# --- Configurable parameters (modularized) ---
DEBUG = os.getenv("VICTORYBOT_DEBUG", "True") == "True"
LOG_FILE = os.getenv("VICTORYBOT_LOG_FILE", "victorybot.log")
LOG_MAX_BYTES = int(os.getenv("VICTORYBOT_LOG_MAX_BYTES", 5_000_000))
LOG_BACKUP_COUNT = int(os.getenv("VICTORYBOT_LOG_BACKUP_COUNT", 3))
PROFIT_THRESHOLD = float(os.getenv("VICTORYBOT_PROFIT_THRESHOLD", 0.05))
CYCLE_INTERVAL = int(os.getenv("VICTORYBOT_CYCLE_INTERVAL", 10))
TOP_N_SYMBOLS = int(os.getenv("VICTORYBOT_TOP_N_SYMBOLS", 30))
MOMENTUM_LOOKBACK = int(os.getenv("VICTORYBOT_MOMENTUM_LOOKBACK", 24))
MOMENTUM_TOP_N = int(os.getenv("VICTORYBOT_MOMENTUM_TOP_N", 15))
MIN_SIZE_USD = float(os.getenv("VICTORYBOT_MIN_SIZE_USD", 15))
MAX_SIZE_USD = float(os.getenv("VICTORYBOT_MAX_SIZE_USD", 10000))
MAX_ASSETS = int(os.getenv("VICTORYBOT_MAX_ASSETS", 5))
MAX_DRAWDOWN = float(os.getenv("VICTORYBOT_MAX_DRAWDOWN", 0.2))
MAX_PORTFOLIO_DRAWDOWN = float(os.getenv("VICTORYBOT_MAX_PORTFOLIO_DRAWDOWN", 0.3))
MIN_LIQUIDITY = float(os.getenv("VICTORYBOT_MIN_LIQUIDITY", 10000))
STOP_LOSS_PCT = float(os.getenv("VICTORYBOT_STOP_LOSS_PCT", 2.0))
TAKE_PROFIT_PCT = float(os.getenv("VICTORYBOT_TAKE_PROFIT_PCT", 4.0))

# --- Fix: Kelly fraction and leverage as persistent variables ---
kelly_fraction = float(os.getenv("VICTORYBOT_KELLY_FRACTION", 0.5))
leverage = int(os.getenv("VICTORYBOT_LEVERAGE", 2))

# --- Advanced logging setup with rotation ---
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT
)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)
else:
    logger.handlers.clear()
    logger.addHandler(handler)

# Optional: External monitoring integration (e.g., Sentry)
# import sentry_sdk
# sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

# --- Graceful shutdown support ---
shutdown_event = asyncio.Event()


def handle_shutdown(signum, frame):
    print(f"[VictoryBot] Received signal {signum}, shutting down gracefully...")
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_event.set()


signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)


async def fetch_portfolio_balances(
    engine: BTCFreeExecutionEngine, symbols: List[str]
) -> Dict[str, float]:
    """
    Fetch live balances and compute USD value for each symbol.
    Returns a dict of {symbol: usd_value}.
    """
    balances = engine.exchange.fetch_balance()
    long_positions = {}
    for s in symbols:
        base = s.replace("USDT", "")
        amount = balances["total"].get(base, 0)
        price = await get_price(s) or 0
        usd_value = amount * price
        if usd_value > 1:  # Only include non-trivial positions
            long_positions[s] = usd_value
    return long_positions


def fetch_latest_headlines():
    # Example: CryptoPanic public API (no key required for headlines)
    url = "https://cryptopanic.com/api/v1/posts/?public=true&currencies=BTC,ETH"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Return a list of headlines
        return [item["title"] for item in data.get("results", [])]
    except Exception as e:
        print(f"[VictoryBot][NEWS][ERROR] {e}")
        return []


async def get_price(symbol):
    # Return the latest price from the WebSocket cache
    return ws_price_cache.get(symbol, {}).get("price")


async def main() -> None:
    """
    Main entry point for Victory Trading Bot live runner.
    Handles initialization, trading loop, diagnostics, and graceful shutdown.
    """
    global kelly_fraction, leverage
    start_metrics_exporter()
    print("\n🚀 Victory Trading Bot: 24/7/365 Live Trading Mode\n" + "=" * 50)
    logger.info("Victory Trading Bot started in live mode.")
    if not all_risk_gates_open():
        print("❌ Risk/approval gates not open. Aborting live trading.")
        return
    engine = BTCFreeExecutionEngine(
        api_key=os.getenv("BINANCEUS_KEY"),
        api_secret=os.getenv("BINANCEUS_SECRET"),  # <-- fix this!
    )
    engine.setup_exchange()
    engine.start_position_monitoring(
        profit_threshold=PROFIT_THRESHOLD,
    )

    # --- FIX: Assign symbols before starting websocket task ---
    top_symbols, scored = get_dynamic_symbol_universe(
        engine.exchange, account_currency="USDT", top_n=TOP_N_SYMBOLS
    )
    top_symbols = [s for s in top_symbols if s.endswith("USDT")]
    scored = [row for row in scored if row[0].endswith("USDT")]
    symbols = top_symbols

    # Start WebSocket listener as a background task (only once)
    ws_task = asyncio.create_task(
        stream_all_usdt_prices_and_candles(symbols, interval="1m")
    )

    # Main trading loop
    while not shutdown_event.is_set():
        # --- Universe Expansion: Use more symbols for more opportunities ---
        top_symbols, scored = get_dynamic_symbol_universe(
            engine.exchange,  # <-- pass the exchange object here too!
            account_currency="USDT",
            top_n=TOP_N_SYMBOLS,
        )
        top_symbols = [s for s in top_symbols if s.endswith("USDT")]
        scored = [row for row in scored if row[0].endswith("USDT")]
        symbols = top_symbols

        # (Do NOT start ws_task again here!)

        # ...rest of your trading logic...
        # (No changes needed below this point except removing duplicate ws_task creation)
        # --- Your allocation, signal, and execution logic follows ---

        await asyncio.sleep(CYCLE_INTERVAL)
    print("[VictoryBot] Shutdown complete.")
    logger.info("Shutdown complete.")


if __name__ == "__main__":
    print("API KEY:", os.getenv("BINANCEUS_KEY"))
    print("SECRET:", os.getenv("BINANCEUS_SECRET"))
    asyncio.run(main())
