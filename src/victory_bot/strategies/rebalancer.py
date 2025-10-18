"""
victory_bot/strategies/rebalancer.py
Automated portfolio rebalancing logic for Victory Trading Bot.
"""

from typing import Dict


class Rebalancer:
    def __init__(self, rebalance_threshold=0.10):
        self.rebalance_threshold = rebalance_threshold  # 10% drift by default

    def needs_rebalance(
        self, current_alloc: Dict[str, float], target_alloc: Dict[str, float]
    ) -> bool:
        """Return True if any asset drifts more than threshold from target."""
        for symbol, target in target_alloc.items():
            current = current_alloc.get(symbol, 0)
            if target == 0:
                continue
            drift = abs(current - target) / target
            if drift > self.rebalance_threshold:
                return True
        return False

    def get_rebalance_trades(
        self, current_alloc: Dict[str, float], target_alloc: Dict[str, float]
    ) -> Dict[str, float]:
        """Return dict of {symbol: trade_amount} to bring portfolio back to target allocation."""
        trades = {}
        for symbol, target in target_alloc.items():
            current = current_alloc.get(symbol, 0)
            trade = target - current
            if abs(trade) > 1:  # Only rebalance if >$1 difference
                trades[symbol] = trade
        return trades
