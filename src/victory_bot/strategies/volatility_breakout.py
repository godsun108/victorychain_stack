"""
victory_bot/strategies/volatility_breakout.py
Volatility breakout strategy using ATR and Donchian Channels.
"""

from typing import List
import numpy as np
from victory_bot.utils.binance_ws import get_price, get_candles


class VolatilityBreakout:
    def __init__(self, exchange, lookback=20):
        self.exchange = exchange
        self.lookback = lookback

    async def get_signals(self, symbols: List[str]) -> List[str]:
        signals = []
        for symbol in symbols:
            try:
                price = await get_price(symbol)
                candles = await get_candles(symbol)
                ohlcv = candles
                highs = [x[2] for x in ohlcv]
                lows = [x[3] for x in ohlcv]
                closes = [x[4] for x in ohlcv]
                if len(closes) < self.lookback:
                    continue
                donchian_high = max(highs[-self.lookback :])
                donchian_low = min(lows[-self.lookback :])
                if closes[-1] > donchian_high or closes[-1] < donchian_low:
                    signals.append(symbol)
            except Exception:
                continue
        return signals
