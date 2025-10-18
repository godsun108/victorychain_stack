"""
victory_bot/universe.py
Claude AI 592 token universe integration for Victory Trading Bot
"""

import ccxt
import os
import numpy as np
import json
from pathlib import Path


def get_news_sentiment(symbol):
    """Fetch news sentiment for a symbol (placeholder: returns 0)."""
    # Integrate with a real news API for production
    return 0


PERF_FILE = Path(__file__).parent.parent / "runtime" / "symbol_performance.json"


def load_symbol_performance():
    if PERF_FILE.exists():
        try:
            with open(PERF_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[VictoryBot] Could not load symbol performance: {e}")
    return {}


def update_symbol_performance(symbol, pnl):
    """Update the cumulative profit for a symbol in symbol_performance.json."""
    data = load_symbol_performance()
    data[symbol] = float(data.get(symbol, 0)) + float(pnl)
    try:
        PERF_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PERF_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[VictoryBot] Updated symbol performance: {symbol} -> {data[symbol]}")
    except Exception as e:
        print(f"[VictoryBot] Could not update symbol performance: {e}")


def get_dynamic_symbol_universe(exchange, account_currency="USDT", top_n=30):
    """
    Dynamically selects the top_n tradable USDT pairs by multi-factor score.
    Factors: volume, volatility, sentiment, recent performance (optional).
    Uses the provided authenticated exchange object for all API calls.
    """
    markets = exchange.load_markets()
    balances = exchange.fetch_balance()
    usd_balance = balances["total"].get(account_currency, 0)
    usdt_balance = balances["total"].get("USDT", 0)
    print(f"[VictoryBot] Available {account_currency} balance: {usd_balance}")
    print(f"[VictoryBot] Available USDT balance: {usdt_balance}")

    # Filter for active, spot, liquid USDT pairs
    symbols = [
        s
        for s, info in markets.items()
        if s.endswith("USDT")
        and info.get("active", True)
        and info.get("spot", True)
        and info.get("quoteVolume", 0) > 0
    ]

    # Load recent performance if available
    performance = load_symbol_performance()

    scored = []
    for symbol in symbols:
        info = markets[symbol]
        volume = info.get("quoteVolume", 0)
        # Volatility: stddev/mean of last 24 hourly closes
        try:
            candles = exchange.fetch_ohlcv(symbol, timeframe="1h", limit=24)
            closes = [c[4] for c in candles]
            volatility = np.std(closes) / np.mean(closes) if closes else 0
        except Exception:
            volatility = 0
        sentiment = get_news_sentiment(symbol)
        recent_pnl = performance.get(symbol, 0)
        # Weighted score: 50% volume, 20% volatility, 10% sentiment, 20% recent pnl
        score = 0.5 * volume + 0.2 * volatility + 0.1 * sentiment + 0.2 * recent_pnl
        scored.append((symbol, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_symbols = [s for s, _ in scored[:top_n]]
    return top_symbols, scored


def get_strategy_overrides(symbol: str):
    # Placeholder: return strategy overrides for a symbol
    return {}
