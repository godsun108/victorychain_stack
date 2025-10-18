#!/usr/bin/env python3
"""
Direct Auto Trader - Starts immediately with optimal settings for your LOKA position
"""

import os
import json
import time
import logging
from datetime import datetime
from binance.client import Client
from dotenv import load_dotenv


class DirectAutoTrader:
    def __init__(self):
        load_dotenv()

        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(message)s",
            handlers=[
                logging.FileHandler(
                    f'direct_auto_trader_{datetime.now().strftime("%Y%m%d")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Optimized for your LOKA position
        self.config = {
            "loka_profit_target": 15.0,  # Take profits at +15% for LOKA
            "loka_trailing_stop": 8.0,  # Trailing stop at 8% below peak
            "trend_follow_threshold": 10.0,  # Follow strong trends
            "max_new_position": 50.0,  # Max $50 in new positions
            "check_interval": 180,  # Check every 3 minutes
        }

        self.running = True
        self.peak_loka_value = self.get_loka_current_value()

        print("🚀 DIRECT AUTO TRADER - OPTIMIZED FOR LOKA")
        print("=" * 50)
        print(f"🎯 LOKA Profit Target: +{self.config['loka_profit_target']}%")
        print(f"🛑 LOKA Trailing Stop: -{self.config['loka_trailing_stop']}%")
        print(f"⏰ Check Interval: {self.config['check_interval']}s")
        print(f"💎 Current LOKA Value: ${self.peak_loka_value:.2f}")
        print("🔥 STARTING AUTOMATED TRADING...")
        print()

    def get_loka_current_value(self) -> float:
        """Get current LOKA position value"""
        try:
            account = self.client.get_account()
            for balance in account["balances"]:
                if balance["asset"] == "LOKA":
                    amount = float(balance["free"]) + float(balance["locked"])
                    if amount > 0:
                        ticker = self.client.get_symbol_ticker(symbol="LOKAUSDT")
                        price = float(ticker["price"])
                        return amount * price
            return 0
        except:
            return 0

    def get_loka_performance(self) -> dict:
        """Get LOKA performance metrics"""
        try:
            ticker = self.client.get_ticker(symbol="LOKAUSDT")
            return {
                "current_price": float(ticker["lastPrice"]),
                "change_24h": float(ticker["priceChangePercent"]),
                "volume": float(ticker["quoteVolume"]),
            }
        except:
            return {"current_price": 0, "change_24h": 0, "volume": 0}

    def check_loka_signals(self) -> list:
        """Check LOKA for trading signals"""
        actions = []

        try:
            current_value = self.get_loka_current_value()
            perf = self.get_loka_performance()

            # Update peak value
            if current_value > self.peak_loka_value:
                self.peak_loka_value = current_value
                self.logger.info(f"🎯 New LOKA peak: ${current_value:.2f}")

            # Profit taking - if up 15%+ today, sell 25%
            if perf["change_24h"] >= self.config["loka_profit_target"]:
                actions.append(
                    {
                        "action": "sell_partial_loka",
                        "percentage": 25,
                        "reason": f'Profit taking: +{perf["change_24h"]:.1f}%',
                    }
                )

            # Trailing stop - if down 8% from peak, sell 50%
            drawdown = (
                (self.peak_loka_value - current_value) / self.peak_loka_value
            ) * 100
            if drawdown >= self.config["loka_trailing_stop"]:
                actions.append(
                    {
                        "action": "sell_partial_loka",
                        "percentage": 50,
                        "reason": f"Trailing stop: -{drawdown:.1f}% from peak",
                    }
                )

            return actions

        except Exception as e:
            self.logger.error(f"Error checking LOKA signals: {e}")
            return []

    def find_trend_opportunities(self) -> list:
        """Find new trending opportunities"""
        actions = []

        try:
            # Get USDT balance
            account = self.client.get_account()
            usdt_balance = 0
            for balance in account["balances"]:
                if balance["asset"] == "USDT":
                    usdt_balance = float(balance["free"])
                    break

            if usdt_balance < 10:
                return actions

            # Get top movers
            tickers = self.client.get_ticker()
            hot_tokens = []

            for ticker in tickers:
                if (
                    ticker["symbol"].endswith("USDT")
                    and ticker["symbol"] != "USDCUSDT"
                    and ticker["symbol"] != "LOKAUSDT"
                ):  # Don't buy more LOKA

                    try:
                        change = float(ticker["priceChangePercent"])
                        volume = float(ticker["quoteVolume"])

                        if (
                            change >= self.config["trend_follow_threshold"]
                            and volume > 5000
                        ):
                            hot_tokens.append(
                                {
                                    "symbol": ticker["symbol"],
                                    "change": change,
                                    "volume": volume,
                                }
                            )
                    except:
                        continue

            # Sort by performance
            hot_tokens.sort(key=lambda x: x["change"], reverse=True)

            # Consider top performer
            if hot_tokens:
                top_token = hot_tokens[0]
                asset = top_token["symbol"].replace("USDT", "")

                # Small position in trending token
                position_size = min(
                    self.config["max_new_position"],
                    usdt_balance * 0.2,  # Max 20% of USDT
                )

                if position_size >= 10:
                    actions.append(
                        {
                            "action": "buy_trend_token",
                            "asset": asset,
                            "amount": position_size,
                            "reason": f'Hot trend: {asset} +{top_token["change"]:.1f}%',
                        }
                    )

            return actions

        except Exception as e:
            self.logger.error(f"Error finding trends: {e}")
            return []

    def execute_action(self, action: dict) -> bool:
        """Execute a trading action"""
        try:
            if action["action"] == "sell_partial_loka":
                # Sell percentage of LOKA
                account = self.client.get_account()
                loka_balance = 0
                for balance in account["balances"]:
                    if balance["asset"] == "LOKA":
                        loka_balance = float(balance["free"])
                        break

                if loka_balance > 0:
                    sell_amount = loka_balance * (action["percentage"] / 100)
                    sell_amount = round(sell_amount, 6)

                    self.logger.info(f"🔥 {action['reason']}")
                    self.logger.info(
                        f"💰 Selling {sell_amount} LOKA ({action['percentage']}%)"
                    )

                    order = self.client.order_market_sell(
                        symbol="LOKAUSDT", quantity=sell_amount
                    )

                    self.logger.info(f"✅ LOKA sold! Order: {order['orderId']}")
                    return True

            elif action["action"] == "buy_trend_token":
                # Buy trending token
                asset = action["asset"]
                amount = action["amount"]

                self.logger.info(f"🚀 {action['reason']}")
                self.logger.info(f"💎 Buying {asset} with ${amount:.2f}")

                order = self.client.order_market_buy(
                    symbol=asset + "USDT", quoteOrderQty=round(amount, 2)
                )

                self.logger.info(f"✅ {asset} bought! Order: {order['orderId']}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error executing {action['action']}: {e}")
            return False

    def run_auto_trading(self):
        """Run the automated trading loop"""
        self.logger.info("🤖 DIRECT AUTO TRADER STARTED!")

        try:
            while self.running:
                # Check all signals
                all_actions = []

                # LOKA signals (priority)
                loka_actions = self.check_loka_signals()
                all_actions.extend(loka_actions)

                # Trend opportunities (if no LOKA actions)
                if not loka_actions:
                    trend_actions = self.find_trend_opportunities()
                    all_actions.extend(trend_actions)

                # Execute actions
                for action in all_actions[:2]:  # Max 2 actions per cycle
                    success = self.execute_action(action)
                    if success:
                        time.sleep(2)  # Rate limiting

                # Status update
                loka_value = self.get_loka_current_value()
                loka_perf = self.get_loka_performance()

                self.logger.info(
                    f"📊 LOKA: ${loka_value:.2f} ({loka_perf['change_24h']:+.1f}%) | "
                    f"Peak: ${self.peak_loka_value:.2f}"
                )

                # Sleep until next check
                self.logger.info(
                    f"😴 Next check in {self.config['check_interval']}s..."
                )
                time.sleep(self.config["check_interval"])

        except KeyboardInterrupt:
            self.logger.info("🛑 Manual stop requested")
        except Exception as e:
            self.logger.error(f"Auto trading error: {e}")
        finally:
            self.running = False
            self.logger.info("🏁 Direct auto trader stopped")


def main():
    """Start direct auto trading"""
    trader = DirectAutoTrader()
    trader.run_auto_trading()


if __name__ == "__main__":
    main()
