"""
victory_bot/strategies/pair_trading.py
Pair/spread trading strategy for market-neutral opportunities.
"""

from typing import List, Tuple
import numpy as np
from victory_bot.utils.binance_ws import get_price, get_candles


class PairTrading:
    def __init__(self, exchange, pairs: List[Tuple[str, str]]):
        self.exchange = exchange
        self.pairs = pairs

    async def get_signals(self) -> List[Tuple[str, str]]:
        signals = []
        for a, b in self.pairs:
            try:
                price_a, price_b = await get_price(a), await get_price(b)
                candles_a, candles_b = await get_candles(a), await get_candles(b)
                spread = np.array([x[4] for x in candles_a]) - np.array(
                    [x[4] for x in candles_b]
                )
                zscore = (
                    (spread[-1] - spread.mean()) / spread.std()
                    if spread.std() > 0
                    else 0
                )
                if abs(zscore) > 2:
                    signals.append((a, b))
            except Exception:
                continue
        return signals
