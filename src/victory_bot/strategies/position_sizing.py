"""
victory_bot/strategies/position_sizing.py
Adaptive position sizing based on volatility (ATR) and liquidity.
"""

from typing import Dict
import numpy as np


class PositionSizer:
    def __init__(self, min_size_usd=15, max_size_usd=10000, risk_per_trade=0.01):
        self.min_size_usd = min_size_usd
        self.max_size_usd = max_size_usd
        self.risk_per_trade = risk_per_trade

    def get_position_size(
        self, symbol: str, account_equity: float, atr: float, liquidity: float
    ) -> float:
        """
        Calculate position size based on account equity, ATR (volatility), and liquidity.
        - Lower size for high volatility or low liquidity.
        - Never below min or above max size.
        """
        if atr <= 0 or liquidity <= 0:
            return self.min_size_usd
        # Risk-based sizing: risk_per_trade * equity / ATR
        size = self.risk_per_trade * account_equity / atr
        # Cap by liquidity (e.g., max 5% of book depth)
        size = min(size, liquidity * 0.05)
        # Clamp to min/max
        size = max(self.min_size_usd, min(size, self.max_size_usd))
        return size
