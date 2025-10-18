"""
victory_bot/strategies/multi_timeframe_momentum.py
Multi-timeframe momentum strategy for trend confirmation and reversal capture.
"""

from typing import List
import numpy as np
from victory_bot.utils.binance_ws import get_price, get_candles


class MultiTimeframeMomentum:
    def __init__(
        self,
        exchange,
        short_tf: str = "1h",
        long_tf: str = "1d",
        lookback: int = 24,
        min_momentum: float = 0.01,
    ):
        self.exchange = exchange
        self.short_tf = short_tf
        self.long_tf = long_tf
        self.lookback = lookback
        self.min_momentum = min_momentum

    async def get_signals(self, symbols: List[str]) -> List[str]:
        signals = []
        for symbol in symbols:
            try:
                price = await get_price(symbol)
                candles = await get_candles(symbol)

                ohlcv_short = candles[self.short_tf]
                ohlcv_long = candles[self.long_tf]

                if len(ohlcv_short) < self.lookback or len(ohlcv_long) < 2:
                    continue
                short_mom = (ohlcv_short[-1][4] - ohlcv_short[0][4]) / ohlcv_short[0][4]
                long_mom = (ohlcv_long[-1][4] - ohlcv_long[0][4]) / ohlcv_long[0][4]
                if short_mom > self.min_momentum and long_mom > self.min_momentum:
                    signals.append(symbol)
            except Exception:
                continue
        return signals
