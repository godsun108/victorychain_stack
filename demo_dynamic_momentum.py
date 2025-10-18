#!/usr/bin/env python3
"""
VictoryChain Dynamic Momentum Trading Strategy - DEMO VERSION
============================================================

This demo shows how the dynamic momentum trading strategy works
without requiring actual API access.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import asyncio
import random


@dataclass
class PositionState:
    """Track position state and stop loss levels"""

    symbol: str
    entry_price: float
    current_price: float
    stop_loss: float
    allocation_pct: float
    profit_pct: float
    momentum_score: float
    consecutive_gains: int
    max_profit_reached: float
    trade_start_time: datetime
    last_stop_update: datetime


@dataclass
class TradingConfig:
    """Trading configuration parameters"""

    initial_stop_loss_pct: float = 0.22  # 22% initial stop loss
    tight_stop_loss_pct: float = 0.05  # 5% tight stop when profitable
    profit_target_pct: float = 0.15  # 15% profit target to reset stops
    min_momentum_threshold: float = 10.0  # Minimum momentum to trade
    max_allocation_pct: float = 0.50  # Maximum 50% allocation
    initial_allocation_pct: float = 0.10  # Start with 10% allocation
    allocation_increase_step: float = 0.05  # Increase 5% per gain
    momentum_check_interval: int = 30  # Check momentum every 30 seconds for demo


class DynamicMomentumTraderDemo:
    def __init__(self):
        """Initialize the demo trader"""
        self.config = TradingConfig()
        self.current_position: Optional[PositionState] = None
        self.trading_history: List[Dict] = []
        self.is_running = False
        self.demo_prices = {}
        self.portfolio_value = 10000.0  # Start with $10k demo portfolio

        # Setup logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        # Initialize demo data
        self.init_demo_data()

    def init_demo_data(self):
        """Initialize demo price data"""
        # Demo tokens with simulated prices
        self.demo_prices = {
            "BTC": {"price": 45000.0, "momentum": 8.5, "trend": 0.001},
            "ETH": {"price": 2800.0, "momentum": 12.3, "trend": 0.002},
            "NEAR": {
                "price": 3.45,
                "momentum": 38.07,
                "trend": 0.005,
            },  # From our analysis
            "GALA": {"price": 0.045, "momentum": 33.83, "trend": 0.008},
            "DOT": {"price": 7.80, "momentum": 31.00, "trend": 0.003},
            "VET": {"price": 0.035, "momentum": 29.31, "trend": 0.004},
            "DOGE": {"price": 0.078, "momentum": 27.72, "trend": 0.002},
        }

    async def get_highest_momentum_token(self) -> Tuple[str, float]:
        """Get the current highest momentum token (demo)"""
        best_token = None
        best_momentum = 0

        for token, data in self.demo_prices.items():
            # Add some randomness to momentum
            current_momentum = data["momentum"] + random.uniform(-2, 2)
            data["momentum"] = current_momentum  # Update for next check

            if (
                current_momentum > best_momentum
                and current_momentum > self.config.min_momentum_threshold
            ):
                best_momentum = current_momentum
                best_token = token

        return best_token or "BTC", best_momentum

    async def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol (demo)"""
        if symbol in self.demo_prices:
            # Simulate price movement
            data = self.demo_prices[symbol]
            trend = data["trend"]
            volatility = random.uniform(-0.02, 0.02)  # 2% max volatility

            price_change = trend + volatility
            new_price = data["price"] * (1 + price_change)
            data["price"] = new_price

            return new_price
        return 0.0

    def calculate_stop_loss(
        self, entry_price: float, current_price: float, profit_pct: float
    ) -> float:
        """Calculate dynamic stop loss based on current profit"""
        if profit_pct <= 0:
            # Use initial stop loss if not profitable
            return entry_price * (1 - self.config.initial_stop_loss_pct)

        # If profitable, use trailing stop
        if profit_pct >= self.config.profit_target_pct:
            # Tight stop after hitting profit target
            return current_price * (1 - self.config.tight_stop_loss_pct)
        else:
            # Progressive tightening as profit increases
            stop_pct = self.config.initial_stop_loss_pct - (profit_pct * 0.5)
            stop_pct = max(stop_pct, self.config.tight_stop_loss_pct)
            return current_price * (1 - stop_pct)

    def calculate_allocation(self, consecutive_gains: int, max_profit: float) -> float:
        """Calculate position allocation based on performance"""
        base_allocation = self.config.initial_allocation_pct

        # Increase allocation for consecutive gains
        gain_bonus = consecutive_gains * self.config.allocation_increase_step

        # Bonus for high profits achieved
        profit_bonus = min(max_profit * 0.1, 0.2)  # Max 20% bonus

        total_allocation = base_allocation + gain_bonus + profit_bonus
        return min(total_allocation, self.config.max_allocation_pct)

    async def execute_trade(
        self, action: str, symbol: str, allocation_pct: float, price: float
    ):
        """Execute a trade (demo)"""
        trade_amount = self.portfolio_value * allocation_pct
        quantity = trade_amount / price

        if action == "BUY":
            self.portfolio_value -= trade_amount  # Reduce cash
        elif action == "SELL" and self.current_position:
            # Calculate P&L
            pnl = quantity * (price - self.current_position.entry_price)
            self.portfolio_value += trade_amount + pnl

        trade_record = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "symbol": symbol,
            "price": price,
            "quantity": quantity,
            "allocation_pct": allocation_pct,
            "trade_amount": trade_amount,
            "portfolio_value": self.portfolio_value,
        }

        self.trading_history.append(trade_record)

        self.logger.info(
            f"🔄 {action} {symbol}: {quantity:.4f} @ ${price:.4f} "
            f"({allocation_pct*100:.1f}% allocation, Portfolio: ${self.portfolio_value:.2f})"
        )

    async def check_stop_loss(self) -> bool:
        """Check if stop loss should be triggered"""
        if not self.current_position:
            return False

        current_price = await self.get_current_price(self.current_position.symbol)
        if current_price <= 0:
            return False

        # Update current price and profit
        self.current_position.current_price = current_price
        self.current_position.profit_pct = (
            current_price - self.current_position.entry_price
        ) / self.current_position.entry_price

        # Check stop loss
        if current_price <= self.current_position.stop_loss:
            self.logger.warning(
                f"🛑 Stop loss triggered for {self.current_position.symbol} at ${current_price:.4f}"
            )
            await self.execute_trade(
                "SELL",
                self.current_position.symbol,
                self.current_position.allocation_pct,
                current_price,
            )

            trade_result = {
                "symbol": self.current_position.symbol,
                "entry_price": self.current_position.entry_price,
                "exit_price": current_price,
                "profit_pct": self.current_position.profit_pct,
                "duration_minutes": (
                    datetime.now() - self.current_position.trade_start_time
                ).total_seconds()
                / 60,
                "max_profit": self.current_position.max_profit_reached,
                "exit_reason": "stop_loss",
            }

            self.current_position = None
            return True

        return False

    async def update_position(self):
        """Update position state and stop loss"""
        if not self.current_position:
            return

        current_price = await self.get_current_price(self.current_position.symbol)
        if current_price <= 0:
            return

        old_profit = self.current_position.profit_pct
        self.current_position.current_price = current_price
        self.current_position.profit_pct = (
            current_price - self.current_position.entry_price
        ) / self.current_position.entry_price

        # Update max profit reached
        if self.current_position.profit_pct > self.current_position.max_profit_reached:
            self.current_position.max_profit_reached = self.current_position.profit_pct

        # Check for consecutive gains
        if (
            self.current_position.profit_pct > old_profit
            and self.current_position.profit_pct > 0
        ):
            if old_profit <= 0:  # First time profitable
                self.current_position.consecutive_gains += 1

        # Update stop loss
        old_stop = self.current_position.stop_loss
        new_stop = self.calculate_stop_loss(
            self.current_position.entry_price,
            current_price,
            self.current_position.profit_pct,
        )

        # Only move stop loss up (trailing stop)
        if new_stop > old_stop:
            self.current_position.stop_loss = new_stop
            self.current_position.last_stop_update = datetime.now()
            self.logger.info(
                f"📈 Updated stop loss for {self.current_position.symbol}: "
                f"${new_stop:.4f} (profit: {self.current_position.profit_pct*100:.2f}%)"
            )

        # Check if profit target hit - reset and tighten
        if self.current_position.profit_pct >= self.config.profit_target_pct:
            self.current_position.consecutive_gains += 1
            new_allocation = self.calculate_allocation(
                self.current_position.consecutive_gains,
                self.current_position.max_profit_reached,
            )

            if new_allocation > self.current_position.allocation_pct:
                self.logger.info(
                    f"🎯 Profit target hit! Increasing allocation: "
                    f"{self.current_position.allocation_pct*100:.1f}% → {new_allocation*100:.1f}%"
                )
                self.current_position.allocation_pct = new_allocation

    async def trading_loop(self, duration_minutes: int = 5):
        """Main trading loop (demo version)"""
        self.logger.info("🚀 Starting Dynamic Momentum Trading Demo")
        self.is_running = True

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        while self.is_running and datetime.now() < end_time:
            try:
                # Check if we have a position
                if self.current_position:
                    # Update position and check stop loss
                    await self.update_position()
                    if await self.check_stop_loss():
                        continue  # Position was closed, start fresh

                    # Check if still highest momentum
                    highest_token, highest_momentum = (
                        await self.get_highest_momentum_token()
                    )

                    # If momentum dropped significantly or new leader emerged
                    if (
                        highest_token != self.current_position.symbol
                        or self.current_position.momentum_score > highest_momentum * 1.3
                    ):

                        self.logger.info(
                            f"🔄 Momentum shift detected: {self.current_position.symbol} → {highest_token}"
                        )

                        # Close current position
                        current_price = await self.get_current_price(
                            self.current_position.symbol
                        )
                        await self.execute_trade(
                            "SELL",
                            self.current_position.symbol,
                            self.current_position.allocation_pct,
                            current_price,
                        )

                        self.current_position = None

                else:
                    # No position - look for highest momentum token
                    highest_token, highest_momentum = (
                        await self.get_highest_momentum_token()
                    )

                    if highest_momentum > self.config.min_momentum_threshold:
                        # Enter new position
                        entry_price = await self.get_current_price(highest_token)
                        if entry_price > 0:
                            initial_allocation = self.config.initial_allocation_pct
                            stop_loss = entry_price * (
                                1 - self.config.initial_stop_loss_pct
                            )

                            self.current_position = PositionState(
                                symbol=highest_token,
                                entry_price=entry_price,
                                current_price=entry_price,
                                stop_loss=stop_loss,
                                allocation_pct=initial_allocation,
                                profit_pct=0.0,
                                momentum_score=highest_momentum,
                                consecutive_gains=0,
                                max_profit_reached=0.0,
                                trade_start_time=datetime.now(),
                                last_stop_update=datetime.now(),
                            )

                            await self.execute_trade(
                                "BUY", highest_token, initial_allocation, entry_price
                            )
                            self.logger.info(
                                f"🎯 Entered position: {highest_token} @ ${entry_price:.4f} "
                                f"(momentum: {highest_momentum:.2f})"
                            )

                # Print status
                if self.current_position:
                    self.logger.info(
                        f"📊 {self.current_position.symbol}: ${self.current_position.current_price:.4f} "
                        f"(P&L: {self.current_position.profit_pct*100:.2f}%, "
                        f"Stop: ${self.current_position.stop_loss:.4f}, "
                        f"Allocation: {self.current_position.allocation_pct*100:.1f}%)"
                    )

                # Wait before next iteration
                await asyncio.sleep(self.config.momentum_check_interval)

            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(10)  # Wait 10 seconds on error

        self.logger.info("🏁 Demo trading session completed!")

    def print_final_summary(self):
        """Print final trading summary"""
        print("\n" + "=" * 80)
        print("🏆 DYNAMIC MOMENTUM TRADING SUMMARY")
        print("=" * 80)

        total_trades = len(self.trading_history)
        winning_trades = 0
        total_pnl = 0

        for i in range(0, len(self.trading_history), 2):  # Process buy/sell pairs
            if i + 1 < len(self.trading_history):
                buy_trade = self.trading_history[i]
                sell_trade = self.trading_history[i + 1]

                if buy_trade["action"] == "BUY" and sell_trade["action"] == "SELL":
                    pnl_pct = (
                        (sell_trade["price"] - buy_trade["price"])
                        / buy_trade["price"]
                        * 100
                    )
                    if pnl_pct > 0:
                        winning_trades += 1
                    total_pnl += pnl_pct

        completed_trades = total_trades // 2
        win_rate = (
            (winning_trades / completed_trades * 100) if completed_trades > 0 else 0
        )
        avg_pnl = total_pnl / completed_trades if completed_trades > 0 else 0

        print(f"📈 Total Trades: {total_trades}")
        print(f"📊 Completed Trade Pairs: {completed_trades}")
        print(f"🎯 Win Rate: {win_rate:.1f}%")
        print(f"💰 Average P&L per trade: {avg_pnl:.2f}%")
        print(f"💼 Final Portfolio Value: ${self.portfolio_value:.2f}")
        print(f"📈 Total Return: {(self.portfolio_value - 10000) / 10000 * 100:.2f}%")

        if self.current_position:
            print(f"\n🔄 Current Position: {self.current_position.symbol}")
            print(f"   Unrealized P&L: {self.current_position.profit_pct*100:.2f}%")

        print("\n💡 Key Strategy Features Demonstrated:")
        print(f"   ✅ Dynamic stop loss (22% → 5% as profit increases)")
        print(f"   ✅ Position sizing based on performance")
        print(f"   ✅ Momentum-based token selection")
        print(f"   ✅ Trailing stops that lock in profits")
        print(f"   ✅ Auto-rebalancing when momentum shifts")

        print("=" * 80)


async def main():
    """Run the demo"""
    print("🚀 DYNAMIC MOMENTUM TRADING DEMO")
    print("=" * 50)
    print("This demo shows your strategy in action:")
    print("• 22% initial stop loss (like your example)")
    print("• Tight 5% stop when profitable")
    print("• Dynamic allocation increase on gains")
    print("• Momentum-based token switching")
    print("• Trailing stops that capture profits")
    print("=" * 50)

    trader = DynamicMomentumTraderDemo()

    try:
        # Run demo for 2 minutes with faster updates
        await trader.trading_loop(duration_minutes=2)

    except KeyboardInterrupt:
        print("\n🛑 Demo stopped by user")
        trader.is_running = False

    # Print final summary
    trader.print_final_summary()


if __name__ == "__main__":
    asyncio.run(main())
