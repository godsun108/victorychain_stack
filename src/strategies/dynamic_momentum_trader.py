#!/usr/bin/env python3
"""
VictoryChain Dynamic Momentum Trading Strategy
==============================================

Advanced momentum trading with dynamic stop losses and position sizing.
Features:
- Tracks highest momentum token continuously
- Implements tight, trailing stop losses
- Increases allocation on consistent gains
- Resets stop loss when profit targets hit
- Capitalizes on momentum trajectories
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
from binance.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config/.env")


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
    momentum_check_interval: int = 300  # Check momentum every 5 minutes


class DynamicMomentumTrader:
    def __init__(self, config_path: str = "config/.env"):
        """Initialize the dynamic momentum trader"""
        # Initialize Binance client
        api_key = os.getenv("BINANCEUS_KEY")
        api_secret = os.getenv("BINANCEUS_SECRET")

        if not api_key or not api_secret:
            raise ValueError(
                "Binance API credentials not found in environment variables"
            )

        self.client = Client(
            api_key, api_secret, testnet=False
        )  # Set testnet=True for testing
        self.config = TradingConfig()
        self.current_position: Optional[PositionState] = None
        self.trading_history: List[Dict] = []
        self.is_running = False

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

        # Load trading history if exists
        self.load_trading_history()

    def load_trading_history(self):
        """Load previous trading history"""
        try:
            if os.path.exists("dynamic_momentum_history.json"):
                with open("dynamic_momentum_history.json", "r") as f:
                    self.trading_history = json.load(f)
                self.logger.info(
                    f"Loaded {len(self.trading_history)} historical trades"
                )
        except Exception as e:
            self.logger.error(f"Error loading trading history: {e}")

    def save_trading_history(self):
        """Save trading history to file"""
        try:
            with open("dynamic_momentum_history.json", "w") as f:
                json.dump(self.trading_history, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error saving trading history: {e}")

    async def get_highest_momentum_token(self) -> Tuple[str, float]:
        """Get the current highest momentum token"""
        try:
            tokens = [
                "BTC",
                "ETH",
                "BNB",
                "XRP",
                "ADA",
                "DOGE",
                "SOL",
                "DOT",
                "AVAX",
                "MATIC",
                "LINK",
                "UNI",
                "LTC",
                "BCH",
                "ALGO",
                "VET",
                "ICP",
                "FTM",
                "ATOM",
                "NEAR",
                "MANA",
                "SAND",
                "AXS",
                "GALA",
                "ENJ",
                "CHZ",
                "BAT",
                "ZIL",
                "ONE",
                "MAGIC",
            ]

            best_token = None
            best_momentum = 0

            for token in tokens:
                try:
                    # Get 24hr ticker statistics
                    ticker = self.client.get_ticker(symbol=f"{token}USDT")

                    if ticker:
                        price_change_pct = float(ticker["priceChangePercent"])
                        volume = float(ticker["volume"])
                        count = float(ticker["count"])

                        # Calculate momentum score
                        momentum = (
                            price_change_pct + (count / 1000) + (volume / 1000000)
                        )

                        if (
                            momentum > best_momentum
                            and momentum > self.config.min_momentum_threshold
                        ):
                            best_momentum = momentum
                            best_token = token

                except Exception as e:
                    self.logger.debug(f"Error analyzing {token}: {e}")
                    continue

            return best_token or "BTC", best_momentum

        except Exception as e:
            self.logger.error(f"Error getting highest momentum token: {e}")
            return "BTC", 0

    async def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=f"{symbol}USDT")
            if ticker and "price" in ticker:
                return float(ticker["price"])
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
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
        """Execute a trade (mock implementation for demo)"""
        try:
            # Get account balance (demo mode - using mock data)
            usdt_balance = 10000.0  # Mock balance for demo

            trade_amount = usdt_balance * allocation_pct
            quantity = trade_amount / price

            trade_record = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "symbol": symbol,
                "price": price,
                "quantity": quantity,
                "allocation_pct": allocation_pct,
                "usdt_amount": trade_amount,
            }

            self.trading_history.append(trade_record)
            self.save_trading_history()

            self.logger.info(
                f"🔄 {action} {symbol}: {quantity:.4f} @ ${price:.4f} ({allocation_pct*100:.1f}% allocation)"
            )

        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")

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

            # Record the trade result
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
                f"📈 Updated stop loss for {self.current_position.symbol}: ${new_stop:.4f} (profit: {self.current_position.profit_pct*100:.2f}%)"
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
                    f"🎯 Profit target hit! Increasing allocation: {self.current_position.allocation_pct*100:.1f}% → {new_allocation*100:.1f}%"
                )
                self.current_position.allocation_pct = new_allocation

    async def trading_loop(self):
        """Main trading loop"""
        self.logger.info("🚀 Starting Dynamic Momentum Trading Loop")
        self.is_running = True

        while self.is_running:
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
                        or self.current_position.momentum_score > highest_momentum * 1.5
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

                        # Record trade result
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
                            "exit_reason": "momentum_shift",
                        }

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
                                f"🎯 Entered position: {highest_token} @ ${entry_price:.4f} (momentum: {highest_momentum:.2f})"
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
                await asyncio.sleep(60)  # Wait 1 minute on error

    def print_status(self):
        """Print current trading status"""
        print("\n" + "=" * 80)
        print("🚀 DYNAMIC MOMENTUM TRADER STATUS")
        print("=" * 80)

        if self.current_position:
            print(f"📈 Current Position: {self.current_position.symbol}")
            print(f"   Entry Price: ${self.current_position.entry_price:.4f}")
            print(f"   Current Price: ${self.current_position.current_price:.4f}")
            print(f"   Profit/Loss: {self.current_position.profit_pct*100:.2f}%")
            print(f"   Stop Loss: ${self.current_position.stop_loss:.4f}")
            print(f"   Allocation: {self.current_position.allocation_pct*100:.1f}%")
            print(f"   Consecutive Gains: {self.current_position.consecutive_gains}")
            print(f"   Max Profit: {self.current_position.max_profit_reached*100:.2f}%")
            print(
                f"   Duration: {(datetime.now() - self.current_position.trade_start_time).total_seconds()/3600:.1f} hours"
            )
        else:
            print("💤 No current position - scanning for momentum...")

        print(f"\n📊 Trading History: {len(self.trading_history)} trades")
        if self.trading_history:
            recent_trades = self.trading_history[-5:]
            print("   Recent trades:")
            for trade in recent_trades:
                print(
                    f"   • {trade['action']} {trade['symbol']} @ ${trade['price']:.4f}"
                )

        print("=" * 80)

    def stop_trading(self):
        """Stop the trading loop"""
        self.is_running = False
        self.logger.info("🛑 Stopping trading loop...")


async def main():
    """Main function to run the dynamic momentum trader"""
    trader = DynamicMomentumTrader()

    try:
        # Print initial status
        trader.print_status()

        # Start trading loop
        await trader.trading_loop()

    except KeyboardInterrupt:
        print("\n🛑 Trading stopped by user")
        trader.stop_trading()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Final status
        trader.print_status()


if __name__ == "__main__":
    asyncio.run(main())
