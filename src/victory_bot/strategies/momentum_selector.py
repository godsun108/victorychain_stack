"""
victory_bot/strategies/momentum_selector.py
Selects top-performing assets for allocation based on recent momentum.
"""

import numpy as np
import ccxt
from typing import List, Dict
from victory_bot.utils.binance_ws import get_price, get_candles


class MomentumSelector:
    def __init__(self, exchange, lookback_hours=24, top_n=5):
        self.exchange = exchange
        self.lookback_hours = lookback_hours
        self.top_n = top_n

    async def get_top_assets(self, symbols: List[str]) -> List[str]:
        """Return the top N symbols by % price change over lookback period."""
        changes = {}
        for symbol in symbols:
            try:
                price = await get_price(symbol)
                candles = await get_candles(symbol)
                if len(candles) < self.lookback_hours:
                    continue
                start_price = candles[0][4]
                end_price = candles[-1][4]
                pct_change = (end_price - start_price) / start_price * 100
                changes[symbol] = pct_change
            except Exception:
                continue
        # Sort by descending momentum
        top = sorted(changes, key=changes.get, reverse=True)[: self.top_n]
        return top
