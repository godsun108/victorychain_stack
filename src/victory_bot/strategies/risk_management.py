"""
victory_bot/strategies/risk_management.py
Risk management logic: stop-loss, trailing stop, take-profit, drawdown protection.
"""

from typing import Dict


class RiskManager:
    def __init__(
        self,
        stop_loss_pct=0.05,
        take_profit_pct=0.10,
        trailing_stop_pct=0.03,
        max_drawdown_pct=0.20,
    ):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.high_watermark = {}
        self.equity_curve = []

    def check_stop_loss(self, entry_price: float, current_price: float) -> bool:
        return current_price <= entry_price * (1 - self.stop_loss_pct)

    def check_take_profit(self, entry_price: float, current_price: float) -> bool:
        return current_price >= entry_price * (1 + self.take_profit_pct)

    def check_trailing_stop(self, symbol: str, current_price: float) -> bool:
        hwm = self.high_watermark.get(symbol, current_price)
        if current_price > hwm:
            self.high_watermark[symbol] = current_price
            return False
        return current_price <= hwm * (1 - self.trailing_stop_pct)

    def update_equity(self, equity: float):
        self.equity_curve.append(equity)
        if len(self.equity_curve) > 1:
            peak = max(self.equity_curve)
            drawdown = (peak - equity) / peak
            return drawdown >= self.max_drawdown_pct
        return False
