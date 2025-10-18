#!/usr/bin/env python3
"""
Simple Growth Booster - Use Available USDT for Maximum Growth! 📈
"""

import os
import json
import time
import logging
from datetime import datetime
from binance.client import Client
from dotenv import load_dotenv


class SimpleGrowthBooster:
    def __init__(self):
        load_dotenv()

        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_available_usdt(self):
        """Get available USDT balance"""
        try:
            account = self.client.get_account()
            for balance in account["balances"]:
                if balance["asset"] == "USDT":
                    return float(balance["free"])
            return 0
        except Exception as e:
            self.logger.error(f"Error getting USDT: {e}")
            return 0

    def find_momentum_rockets(self):
        """Find tokens with the highest momentum RIGHT NOW"""
        try:
            tickers = self.client.get_ticker()

            rockets = []
            for ticker in tickers:
                if ticker["symbol"].endswith("USDT"):
                    price_change = float(ticker["priceChangePercent"])
                    volume = float(ticker["quoteVolume"])

                    # Focus on EXTREME momentum
                    if price_change > 15:  # Rising > 15%
                        rockets.append(
                            {
                                "symbol": ticker["symbol"],
                                "momentum": price_change,
                                "volume": volume,
                                "price": float(ticker["lastPrice"]),
                                "rocket_score": price_change + (volume / 10000),
                            }
                        )

            # Sort by rocket score
            rockets.sort(key=lambda x: x["rocket_score"], reverse=True)
            return rockets[:10]

        except Exception as e:
            self.logger.error(f"Error finding rockets: {e}")
            return []

    def buy_growth_token(self, symbol, amount_usd):
        """Buy a high-growth token"""
        try:
            print(f"🚀 BUYING {symbol}: ${amount_usd:.2f}")

            order = self.client.order_market_buy(
                symbol=symbol, quoteOrderQty=amount_usd
            )

            print(f"✅ SUCCESS! Order ID: {order['orderId']}")
            return True

        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False

    def run_growth_boost(self):
        """Run the growth boost session"""
        try:
            print("🚀 SIMPLE GROWTH BOOSTER")
            print("=" * 40)
            print("📈 Strategy: Buy the hottest momentum tokens!")
            print()

            # Check available USDT
            usdt_balance = self.get_available_usdt()
            print(f"💰 Available USDT: ${usdt_balance:.2f}")

            if usdt_balance < 10:
                print("❌ Need at least $10 USDT to boost growth")
                return

            # Find momentum rockets
            print("\n🔍 Finding momentum rockets...")
            rockets = self.find_momentum_rockets()

            if not rockets:
                print("❌ No momentum rockets found")
                return

            print("\n🚀 TOP MOMENTUM ROCKETS:")
            print("-" * 50)
            for i, rocket in enumerate(rockets[:5], 1):
                print(
                    f"{i}. {rocket['symbol']:12s} | {rocket['momentum']:+6.2f}% | "
                    f"Vol: ${rocket['volume']:,.0f}"
                )

            # Choose investment strategy
            print(f"\nAvailable to invest: ${usdt_balance:.2f}")
            print("\n💡 GROWTH STRATEGIES:")
            print("1. 🎯 ALL-IN on #1 rocket (maximum risk/reward)")
            print("2. 🔥 Split between top 2 rockets")
            print("3. 📊 Diversify across top 3 rockets")

            choice = input("\nChoose strategy (1-3): ").strip()

            trades_executed = 0

            if choice == "1":
                # ALL-IN strategy
                top_rocket = rockets[0]
                print(f"\n🎯 GOING ALL-IN ON {top_rocket['symbol']}!")
                print(f"🚀 Momentum: {top_rocket['momentum']:+.2f}%")

                confirm = input("Type 'ALL IN' to confirm: ")
                if confirm == "ALL IN":
                    if self.buy_growth_token(top_rocket["symbol"], usdt_balance * 0.95):
                        trades_executed = 1

            elif choice == "2":
                # Split between top 2
                amount_each = (usdt_balance * 0.95) / 2
                print(f"\n🔥 SPLITTING ${amount_each:.2f} each between top 2 rockets!")

                confirm = input("Type 'SPLIT BUY' to confirm: ")
                if confirm == "SPLIT BUY":
                    for rocket in rockets[:2]:
                        if self.buy_growth_token(rocket["symbol"], amount_each):
                            trades_executed += 1
                            time.sleep(1)

            elif choice == "3":
                # Diversify across top 3
                amount_each = (usdt_balance * 0.95) / 3
                print(
                    f"\n📊 DIVERSIFYING ${amount_each:.2f} each across top 3 rockets!"
                )

                confirm = input("Type 'DIVERSIFY' to confirm: ")
                if confirm == "DIVERSIFY":
                    for rocket in rockets[:3]:
                        if self.buy_growth_token(rocket["symbol"], amount_each):
                            trades_executed += 1
                            time.sleep(1)
            else:
                print("❌ Invalid choice")
                return

            if trades_executed > 0:
                print(f"\n🎉 GROWTH BOOST COMPLETE!")
                print(f"🚀 Executed {trades_executed} momentum trades!")
                print("📈 YOUR NUMBERS SHOULD GO UP!")

                # Save trade record
                trade_record = {
                    "timestamp": datetime.now().isoformat(),
                    "strategy": f"Growth Boost Strategy {choice}",
                    "trades_executed": trades_executed,
                    "rockets_bought": [r["symbol"] for r in rockets[:trades_executed]],
                }

                filename = (
                    f"growth_boost_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                with open(filename, "w") as f:
                    json.dump(trade_record, f, indent=2, default=str)

                print(f"💾 Trade record: {filename}")
            else:
                print("❌ No trades executed")

        except KeyboardInterrupt:
            print("\n👋 Growth boost cancelled")
        except Exception as e:
            self.logger.error(f"Growth boost error: {e}")


def main():
    booster = SimpleGrowthBooster()
    booster.run_growth_boost()


if __name__ == "__main__":
    main()
