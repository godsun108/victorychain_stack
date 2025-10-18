"""
victory_bot/strategies/mean_reversion.py
Mean reversion strategy using RSI and Bollinger Bands.
"""

from typing import List
import numpy as np
from victory_bot.utils.binance_ws import get_price, get_candles


class MeanReversion:
    def __init__(self, exchange, lookback=14):
        self.exchange = exchange
        self.lookback = lookback

    async def get_signals(self, symbols: List[str]) -> List[str]:
        signals = []
        for symbol in symbols:
            try:
                price = await get_price(symbol)
                candles = await get_candles(symbol)
                ohlcv = candles
                closes = [x[4] for x in ohlcv]
                if len(closes) < self.lookback:
                    continue
                # RSI
                deltas = np.diff(closes)
                up = deltas[deltas > 0].sum() / self.lookback
                down = -deltas[deltas < 0].sum() / self.lookback
                rs = up / down if down != 0 else 0
                rsi = 100 - 100 / (1 + rs) if down != 0 else 100
                # Bollinger Bands
                ma = np.mean(closes)
                std = np.std(closes)
                lower = ma - 2 * std
                if closes[-1] < lower and rsi < 30:
                    signals.append(symbol)
            except Exception:
                continue
        return signals
