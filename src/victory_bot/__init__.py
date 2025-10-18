"""
victory_bot/__init__.py
Victory Trading Bot unified package
"""

# Expose key modules for unified import

import asyncio

ws_price_cache = {}


async def stream_all_usdt_prices_and_candles(symbols, interval="1m"):
    # ...existing websocket connection code...
    # On each new price/candle:
    ws_price_cache[symbol] = {
        "price": latest_price,
        "candles": latest_candles,
        # ...other data...
    }
    # ...existing code...
