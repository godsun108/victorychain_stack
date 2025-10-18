"""
victory_bot/strategies/strategy_selector.py
Automatically select the best strategy based on current market conditions.
"""

from typing import List, Dict


class StrategySelector:
    def __init__(self, strategies: Dict[str, object]):
        self.strategies = strategies

    def select(self, market_data: Dict) -> List[str]:
        """
        Evaluate market conditions and select the best strategy or combination.
        Example logic:
        - High volatility: use mean reversion or hedging
        - Strong trend: use momentum or breakout
        - Range-bound: use pair trading or mean reversion
        - News event: use event-driven
        """
        signals = set()
        volatility = market_data.get("volatility", 0)
        trend_strength = market_data.get("trend_strength", 0)
        news_event = market_data.get("news_event", False)
        if news_event:
            signals.update(self.strategies["event"].get_signals())
        elif volatility > 0.05 and trend_strength < 0.02:
            signals.update(
                self.strategies["meanrev"].get_signals(market_data["symbols"])
            )
            signals.update(
                self.strategies["hedge"].get_hedge_signals(market_data["symbols"])
            )
        elif trend_strength > 0.03:
            signals.update(self.strategies["mmtf"].get_signals(market_data["symbols"]))
            signals.update(
                self.strategies["breakout"].get_signals(market_data["symbols"])
            )
        elif market_data.get("range_bound", False):
            signals.update(self.strategies["pairs"].get_signals())
        else:
            # Default to ML/AI signals if available
            signals.update(self.strategies["ml"].get_signals(None))
        return list(signals)
