#!/usr/bin/env python3
"""
Position Multiplier - Convert Positions to Higher Growth! 🚀
Works with existing holdings to maximize growth
"""

import os
import json
import time
import logging
from datetime import datetime
from binance.client import Client
from dotenv import load_dotenv


class PositionMultiplier:
    def __init__(self):
        load_dotenv()

        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def get_current_portfolio(self):
        """Get current portfolio with momentum analysis"""
        try:
            account = self.client.get_account()
            portfolio = []

            for balance in account["balances"]:
                free = float(balance["free"])
                locked = float(balance["locked"])
                total = free + locked

                if total > 0.01:
                    if balance["asset"] == "USDT":
                        portfolio.append(
                            {
                                "asset": balance["asset"],
                                "amount": total,
                                "usd_value": total,
                                "momentum": 0,
                                "can_trade": True,
                            }
                        )
                    else:
                        try:
                            symbol = balance["asset"] + "USDT"
                            ticker = self.client.get_ticker(symbol=symbol)
                            price = float(ticker["lastPrice"])
                            momentum = float(ticker["priceChangePercent"])
                            usd_value = total * price

                            portfolio.append(
                                {
                                    "asset": balance["asset"],
                                    "symbol": symbol,
                                    "amount": total,
                                    "price": price,
                                    "usd_value": usd_value,
                                    "momentum": momentum,
                                    "can_trade": free
                                    > 0.001,  # Only if we have free balance
                                }
                            )
                        except:
                            continue

            return sorted(portfolio, key=lambda x: x["usd_value"], reverse=True)

        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            return []

    def find_momentum_opportunities(self):
        """Find current momentum opportunities"""
        try:
            tickers = self.client.get_ticker()

            opportunities = []
            for ticker in tickers:
                if ticker["symbol"].endswith("USDT"):
                    momentum = float(ticker["priceChangePercent"])
                    volume = float(ticker["quoteVolume"])
                    price = float(ticker["lastPrice"])

                    # Look for strong momentum (positive preferred)
                    if momentum > 5 or (momentum > -5 and volume > 50000):
                        opportunities.append(
                            {
                                "symbol": ticker["symbol"],
                                "momentum": momentum,
                                "volume": volume,
                                "price": price,
                                "opportunity_score": momentum + (volume / 100000),
                            }
                        )

            return sorted(
                opportunities, key=lambda x: x["opportunity_score"], reverse=True
            )[:15]

        except Exception as e:
            self.logger.error(f"Error finding opportunities: {e}")
            return []

    def suggest_position_swaps(self, portfolio, opportunities):
        """Suggest position swaps for better growth"""
        swaps = []

        # Find positions that could be improved
        for position in portfolio:
            if (
                position["asset"] != "USDT"
                and position["can_trade"]
                and position["usd_value"] > 5
            ):  # Only meaningful positions

                current_momentum = position["momentum"]

                # Find better opportunities
                for opp in opportunities[:5]:  # Top 5 opportunities
                    if (
                        opp["symbol"] != position.get("symbol")
                        and opp["momentum"] > current_momentum + 3
                    ):  # At least 3% better

                        potential_gain = opp["momentum"] - current_momentum

                        swaps.append(
                            {
                                "sell_asset": position["asset"],
                                "sell_symbol": position.get("symbol"),
                                "sell_amount": position["amount"],
                                "sell_value": position["usd_value"],
                                "current_momentum": current_momentum,
                                "buy_symbol": opp["symbol"],
                                "target_momentum": opp["momentum"],
                                "potential_gain": potential_gain,
                                "reasoning": f"Upgrade from {current_momentum:+.1f}% to {opp['momentum']:+.1f}% ({potential_gain:+.1f}% better)",
                            }
                        )
                        break  # One swap per position

        return sorted(swaps, key=lambda x: x["potential_gain"], reverse=True)

    def execute_position_swap(self, swap):
        """Execute a position swap"""
        try:
            print(
                f"🔄 SWAPPING {swap['sell_asset']} → {swap['buy_symbol'].replace('USDT', '')}"
            )
            print(f"   Value: ${swap['sell_value']:.2f}")
            print(f"   {swap['reasoning']}")

            # Step 1: Sell current position
            print(f"   🔻 Selling {swap['sell_asset']}...")
            sell_order = self.client.order_market_sell(
                symbol=swap["sell_symbol"], quantity=swap["sell_amount"]
            )

            print(f"   ✅ Sold - Order ID: {sell_order['orderId']}")

            # Step 2: Wait briefly for settlement
            time.sleep(2)

            # Step 3: Buy new position
            print(f"   🔺 Buying {swap['buy_symbol']}...")

            # Use 95% of sold value to account for fees
            buy_amount = swap["sell_value"] * 0.95

            buy_order = self.client.order_market_buy(
                symbol=swap["buy_symbol"], quoteOrderQty=buy_amount
            )

            print(f"   ✅ Bought - Order ID: {buy_order['orderId']}")
            print(f"   🚀 SWAP COMPLETE!")

            return True

        except Exception as e:
            print(f"   ❌ SWAP FAILED: {e}")
            return False

    def run_position_multiplication(self):
        """Run the position multiplication session"""
        try:
            print("🚀 POSITION MULTIPLIER")
            print("=" * 50)
            print("💡 Strategy: Swap current positions for higher momentum!")
            print()

            # Get current portfolio
            print("📊 Analyzing current positions...")
            portfolio = self.get_current_portfolio()

            total_value = sum(p["usd_value"] for p in portfolio)
            print(f"💰 Total Portfolio: ${total_value:.2f}")

            print("\n🏦 CURRENT POSITIONS:")
            print("-" * 60)
            for pos in portfolio:
                if pos["asset"] != "USDT":
                    tradeable = "✅" if pos["can_trade"] else "❌"
                    print(
                        f"{pos['asset']:8s} | ${pos['usd_value']:8.2f} | {pos['momentum']:+6.2f}% | {tradeable}"
                    )
                else:
                    print(f"{pos['asset']:8s} | ${pos['usd_value']:8.2f} | Cash")

            # Find momentum opportunities
            print("\n🔍 Finding momentum opportunities...")
            opportunities = self.find_momentum_opportunities()

            print("\n📈 TOP MOMENTUM OPPORTUNITIES:")
            print("-" * 60)
            for i, opp in enumerate(opportunities[:8], 1):
                print(
                    f"{i}. {opp['symbol']:12s} | {opp['momentum']:+6.2f}% | Vol: ${opp['volume']:,.0f}"
                )

            # Suggest swaps
            swaps = self.suggest_position_swaps(portfolio, opportunities)

            if not swaps:
                print("\n✅ Your positions are already optimized!")
                print("💎 No beneficial swaps found - HODL strong!")
                return

            print(f"\n💡 SUGGESTED POSITION SWAPS ({len(swaps)} opportunities):")
            print("-" * 70)

            for i, swap in enumerate(swaps[:5], 1):  # Show top 5
                print(
                    f"{i}. {swap['sell_asset']:8s} → {swap['buy_symbol'].replace('USDT', ''):8s} | "
                    f"${swap['sell_value']:7.2f} | {swap['potential_gain']:+5.1f}% better"
                )
                print(f"   {swap['reasoning']}")

            # Choose swaps to execute
            print(f"\nYou can execute up to {min(len(swaps), 3)} swaps.")

            choice = input("\nHow many swaps to execute? (0-3): ").strip()

            try:
                num_swaps = int(choice)
                if num_swaps < 0 or num_swaps > min(len(swaps), 3):
                    print("❌ Invalid number of swaps")
                    return
            except:
                print("❌ Invalid input")
                return

            if num_swaps == 0:
                print("👋 No swaps executed - keeping current positions")
                return

            # Execute swaps
            executed_swaps = 0

            print(f"\n🚀 EXECUTING {num_swaps} POSITION SWAPS!")
            print("=" * 50)

            for i in range(num_swaps):
                if i < len(swaps):
                    if self.execute_position_swap(swaps[i]):
                        executed_swaps += 1
                        time.sleep(2)  # Rate limiting between swaps

            if executed_swaps > 0:
                print(f"\n🎉 POSITION MULTIPLICATION COMPLETE!")
                print(f"🔄 Executed {executed_swaps} successful swaps!")
                print("📈 YOUR POSITIONS ARE NOW OPTIMIZED FOR GROWTH!")

                # Save record
                trade_record = {
                    "timestamp": datetime.now().isoformat(),
                    "strategy": "Position Multiplier",
                    "swaps_executed": executed_swaps,
                    "swaps": swaps[:executed_swaps],
                }

                filename = (
                    f"position_swaps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                with open(filename, "w") as f:
                    json.dump(trade_record, f, indent=2, default=str)

                print(f"💾 Swap record: {filename}")
            else:
                print("❌ No swaps completed")

        except KeyboardInterrupt:
            print("\n👋 Position multiplication cancelled")
        except Exception as e:
            self.logger.error(f"Position multiplication error: {e}")


def main():
    multiplier = PositionMultiplier()
    multiplier.run_position_multiplication()


if __name__ == "__main__":
    main()
