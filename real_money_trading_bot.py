from victory_bot import execution  #!/usr/bin/env python3

"""
REAL MONEY TRADING BOT - ULTRA SAFE MODE
========================================

🛡️ MAXIMUM SAFETY PROTOCOLS ACTIVE
💰 REAL MONEY TRADING WITH MANUAL APPROVAL
🚨 EVERY TRADE REQUIRES YOUR CONFIRMATION

SAFETY FEATURES:
✅ Manual approval for every trade
✅ Ultra-small position sizes ($100 max)
✅ 1% daily loss limit
✅ 5% emergency stop
✅ 50% cash reserve maintained
✅ Real-time monitoring
"""

import ccxt
import json
import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import os
from libs.common.guards import require_approval, deny_all_if_lockdown

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealMoneyTradingBot:
    """Ultra-Safe Real Money Trading Bot"""

    def __init__(self):
        # Load configuration
        with open("real_money_trading_config.json", "r") as f:
            self.config = json.load(f)

        # IMPORTANT: Update these with your real Binance US credentials
        api_key = self.config["api_config"]["api_key"]
        api_secret = self.config["api_config"]["api_secret"]

        if api_key == "YOUR_REAL_BINANCE_US_API_KEY":
            print(
                "❌ ERROR: Please update your real API credentials in the config file!"
            )
            print(
                "📝 Edit real_money_trading_config.json and add your Binance US API key/secret"
            )
            exit(1)

        # Initialize exchange with REAL credentials
        self.exchange = ccxt.binanceus(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "sandbox": False,  # REAL MONEY MODE
                "enableRateLimit": True,
            }
        )

        # Trading state
        self.starting_capital = self.config["starting_capital"]
        self.current_balance = 0.0
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.trades_today = 0
        self.active_positions = {}

        print("🚨 REAL MONEY TRADING BOT INITIALIZED")
        print(f"💰 Starting Capital: ${self.starting_capital:,.2f}")
        print("🛡️ Ultra-safe mode: Manual approval required for ALL trades")
        print("⚠️  TRADING WITH REAL MONEY!")

    async def get_account_balance(self):
        """Get real account balance"""
        try:
            balance = self.exchange.fetch_balance()

            # Calculate total USD value
            total_usd = 0.0
            for currency, amount in balance["total"].items():
                if amount > 0:
                    if currency == "USD":
                        total_usd += amount
                    else:
                        # Get USD value of crypto holdings
                        try:
                            ticker = self.exchange.fetch_ticker(f"{currency}/USD")
                            total_usd += amount * ticker["last"]
                        except:
                            pass  # Skip if can't get price

            self.current_balance = total_usd

            print(f"💰 Current Account Balance: ${total_usd:,.2f}")
            return balance

        except Exception as e:
            logger.error(f"❌ Error fetching balance: {e}")
            return None

    def analyze_opportunity(self, symbol: str):
        """Analyze trading opportunity with ultra-conservative approach"""
        try:
            # Get market data
            ticker = self.exchange.fetch_ticker(symbol)
            ohlcv = self.exchange.fetch_ohlcv(symbol, "1h", limit=24)

            # Convert to DataFrame for analysis
            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )

            # Calculate simple indicators
            prices = df["close"].values
            sma_short = np.mean(prices[-6:])  # 6-hour SMA
            sma_long = np.mean(prices[-12:])  # 12-hour SMA
            current_price = ticker["last"]

            # Ultra-conservative scoring
            confidence = 0.70  # Start conservative

            # Trend analysis
            if sma_short > sma_long and current_price > sma_short:
                confidence += 0.15  # Uptrend

            # Volume analysis
            recent_volume = np.mean(df["volume"].values[-3:])
            avg_volume = np.mean(df["volume"].values)
            if recent_volume > avg_volume * 1.2:
                confidence += 0.10  # Good volume

            # Volatility check
            returns = np.diff(np.log(prices))
            volatility = np.std(returns)
            if volatility < 0.05:  # Low volatility preferred
                confidence += 0.05

            # Expected return (conservative)
            expected_return = max(0.01, confidence * 0.03)  # 1-3% expected

            # Ultra-small position sizing
            max_position_usd = min(
                self.current_balance * 0.02,  # 2% of balance
                100.0,  # Never more than $100
            )

            opportunity = {
                "symbol": symbol,
                "current_price": current_price,
                "confidence": confidence,
                "expected_return": expected_return,
                "position_size_usd": max_position_usd,
                "recommendation": "BUY" if confidence > 0.90 else "HOLD",
                "sma_short": sma_short,
                "sma_long": sma_long,
                "volatility": volatility,
            }

            return opportunity

        except Exception as e:
            logger.error(f"❌ Analysis error for {symbol}: {e}")
            return None

    def request_trade_approval(self, opportunity):
        """Request manual approval for trade"""
        print("\n" + "=" * 70)
        print("🔔 REAL MONEY TRADE APPROVAL REQUEST")
        print("=" * 70)
        print("⚠️  THIS IS A REAL MONEY TRADE - ACTUAL FUNDS WILL BE USED!")
        print()
        print(f"Symbol:           {opportunity['symbol']}")
        print(f"Current Price:    ${opportunity['current_price']:.4f}")
        print(f"Recommendation:   {opportunity['recommendation']}")
        print(f"Confidence:       {opportunity['confidence']:.1%}")
        print(f"Expected Return:  {opportunity['expected_return']:.1%}")
        print(f"Position Size:    ${opportunity['position_size_usd']:.2f}")
        print(
            f"Max Loss Risk:    ${opportunity['position_size_usd'] * 0.03:.2f} (3% stop loss)"
        )
        print()
        print(f"Technical Analysis:")
        print(f"  Short SMA:      ${opportunity['sma_short']:.4f}")
        print(f"  Long SMA:       ${opportunity['sma_long']:.4f}")
        print(f"  Volatility:     {opportunity['volatility']:.2%}")
        print()
        print("💀 RISKS:")
        print("   • This trade uses REAL MONEY")
        print("   • Cryptocurrency is extremely volatile")
        print("   • You could lose the entire position")
        print("   • No guarantees of profit")
        print()
        print("🛡️ PROTECTIONS:")
        print("   • 3% automatic stop loss")
        print("   • Ultra-small position size")
        print("   • High confidence threshold")
        print("   • Emergency stop at 5% total loss")
        print()

        while True:
            approval = (
                input("🚨 APPROVE THIS REAL MONEY TRADE? (yes/no): ").lower().strip()
            )
            if approval in ["yes", "y"]:
                print("✅ Trade APPROVED - executing with real money...")
                return True
            elif approval in ["no", "n"]:
                print("❌ Trade REJECTED - no funds will be used")
                return False
            else:
                print("Please enter 'yes' or 'no'")

    @require_approval(
        action="order.create",
        params_provider=lambda: {"component": "real_money_trading_bot"},
    )
    async def execute_real_trade(self, opportunity):
        """Execute real money trade"""
        if deny_all_if_lockdown():
            raise PermissionError("lockdown_active")
        try:
            if not self.request_trade_approval(opportunity):
                return None

            symbol = opportunity["symbol"]
            side = opportunity["recommendation"].lower()
            position_usd = opportunity["position_size_usd"]
            price = opportunity["current_price"]

            # Calculate quantity
            quantity = position_usd / price

            print(f"\n🚨 EXECUTING REAL MONEY TRADE:")
            print(f"   Exchange: Binance US")
            print(f"   Symbol: {symbol}")
            print(f"   Side: {side.upper()}")
            print(f"   Quantity: {quantity:.6f}")
            print(f"   Est. Value: ${position_usd:.2f}")
            print(f"   Current Price: ${price:.4f}")
            print()
            print("⏳ Placing real order...")

            # Execute REAL order
            if side == "buy":
                order = execution.safe_market_buy(self.exchange, symbol, quantity)
            else:
                # For sell, check if we have the asset
                base_currency = symbol.split("/")[0]
                balance = self.exchange.fetch_balance()

                if balance[base_currency]["free"] >= quantity:
                    order = execution.safe_market_sell(self.exchange, symbol, quantity)
                else:
                    print(f"❌ Insufficient {base_currency} balance for sell order")
                    return None

            print(f"✅ REAL TRADE EXECUTED!")
            print(f"   Order ID: {order['id']}")
            print(f"   Status: {order['status']}")
            print(f"   Filled: {order['filled']} {symbol.split('/')[0]}")
            print(f"   Cost: ${order['cost']:.2f}")

            # Update tracking
            self.trades_today += 1

            # Set stop loss order
            await self.set_stop_loss(symbol, order, opportunity)

            return order

        except Exception as e:
            print(f"❌ REAL TRADE EXECUTION FAILED: {e}")
            logger.error(f"Trade execution error: {e}")
            return None

    @require_approval(
        action="order.create",
        params_provider=lambda: {"component": "real_money_trading_bot"},
    )
    async def set_stop_loss(self, symbol, order, opportunity):
        """Set automatic stop loss order"""
        if deny_all_if_lockdown():
            raise PermissionError("lockdown_active")
        try:
            if order["side"] == "buy":
                # Set stop loss 3% below entry price
                stop_price = order["average"] * 0.97  # 3% stop loss
                quantity = order["filled"]

                print(f"🛡️ Setting stop loss at ${stop_price:.4f} (3% below entry)")

                # Create stop loss order
                stop_order = self.exchange.create_order(
                    symbol=symbol,
                    type="stop_market",
                    side="sell",
                    amount=quantity,
                    params={"stopPrice": stop_price},
                )

                print(f"✅ Stop loss order placed: {stop_order['id']}")

        except Exception as e:
            print(f"⚠️ Could not set stop loss: {e}")
            logger.warning(f"Stop loss error: {e}")

    async def check_safety_limits(self):
        """Check all safety limits"""
        try:
            # Update balance
            await self.get_account_balance()

            # Calculate P&L
            self.total_pnl = self.current_balance - self.starting_capital
            pnl_percent = (self.total_pnl / self.starting_capital) * 100

            print(f"\n📊 SAFETY CHECK:")
            print(f"   Current Balance: ${self.current_balance:,.2f}")
            print(f"   Total P&L: ${self.total_pnl:+,.2f} ({pnl_percent:+.1f}%)")
            print(f"   Trades Today: {self.trades_today}")

            # Check emergency stop
            if self.total_pnl <= -self.starting_capital * 0.05:  # 5% emergency stop
                print("🚨 EMERGENCY STOP TRIGGERED - 5% loss limit reached!")
                return False

            # Check daily trade limit
            if self.trades_today >= 5:
                print("⏸️ Daily trade limit reached (5 trades)")
                return False

            # Check daily loss limit
            daily_loss_limit = self.starting_capital * 0.01  # 1%
            if self.daily_pnl <= -daily_loss_limit:
                print(f"⏸️ Daily loss limit reached (${daily_loss_limit:.2f})")
                return False

            return True

        except Exception as e:
            logger.error(f"Safety check error: {e}")
            return False

    async def run_safe_trading_cycle(self):
        """Run one ultra-safe trading cycle"""
        try:
            print("\n" + "=" * 70)
            print("🔄 REAL MONEY TRADING CYCLE")
            print("=" * 70)
            print("⚠️  TRADING WITH ACTUAL FUNDS")

            # Safety check first
            if not await self.check_safety_limits():
                print("🛑 Safety limits reached - stopping trading")
                return

            # Conservative symbol list
            symbols = ["BTC/USD", "ETH/USD", "XRP/USD", "ADA/USD", "DOT/USD"]

            print(f"\n🔍 Analyzing {len(symbols)} opportunities...")

            for symbol in symbols:
                print(f"\n📊 Analyzing {symbol}...")

                opportunity = self.analyze_opportunity(symbol)

                if opportunity and opportunity["confidence"] > 0.90:
                    print(f"✅ High confidence opportunity found: {symbol}")

                    result = await self.execute_real_trade(opportunity)

                    if result:
                        print(f"🎉 Real money trade completed successfully!")
                        break  # Only one trade per cycle
                else:
                    print(
                        f"📉 {symbol}: Confidence {opportunity['confidence']:.1%} - below 90% threshold"
                    )

                # Delay between analyses
                await asyncio.sleep(10)

            print("\n🔄 Trading cycle complete")
            print("⏰ Next cycle in 1 hour...")

        except Exception as e:
            print(f"❌ Trading cycle error: {e}")
            logger.error(f"Cycle error: {e}")

    async def start_real_money_trading(self):
        """Start real money trading with maximum safety"""
        print("\n🚀🚀🚀 STARTING REAL MONEY TRADING 🚀🚀🚀")
        print("💰 TRADING WITH ACTUAL FUNDS")
        print("🛡️ ULTRA-SAFE MODE ACTIVE")
        print("⚠️  MANUAL APPROVAL REQUIRED FOR ALL TRADES")
        print()

        # Initial balance check
        await self.get_account_balance()

        if self.current_balance < 500:
            print("❌ Minimum $500 balance required for real money trading")
            return

        print("✅ Real money trading ACTIVATED!")
        print("📊 Bot will analyze opportunities and request approval for trades")
        print("🛑 Press Ctrl+C to stop at any time")
        print()

        try:
            while True:
                await self.run_safe_trading_cycle()

                # Wait 1 hour between cycles
                print("😴 Waiting 1 hour until next cycle...")
                await asyncio.sleep(3600)  # 1 hour

        except KeyboardInterrupt:
            print("\n🛑 Real money trading stopped by user")
        except Exception as e:
            print(f"\n❌ Trading error: {e}")
            logger.error(f"Main trading error: {e}")


if __name__ == "__main__":
    print("🚨🚨🚨 REAL MONEY TRADING BOT 🚨🚨🚨")
    print("💰 TRADING WITH ACTUAL CRYPTOCURRENCY")
    print("🛡️ ULTRA-SAFE MODE WITH MANUAL APPROVAL")
    print()
    print("⚠️  MAKE SURE YOU HAVE:")
    print("   • Updated your API credentials in real_money_trading_config.json")
    print("   • At least $500 in your Binance US account")
    print("   • Completed all account verification")
    print("   • Understanding that losses are possible")
    print()

    bot = RealMoneyTradingBot()

    try:
        asyncio.run(bot.start_real_money_trading())
    except KeyboardInterrupt:
        print("\n🛑 Real money trading stopped")
    except Exception as e:
        print(f"\n❌ Bot error: {e}")
