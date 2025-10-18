#!/usr/bin/env python3
"""
Aggressive Portfolio Multiplier - FORCE THE NUMBERS UP! 🚀
More aggressive rebalancing to maximize total allocation
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv


class AggressivePortfolioMultiplier:
    def __init__(self):
        load_dotenv()

        # Initialize Binance client
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(
                    f'aggressive_multiplier_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Aggressive Configuration
        self.min_trade_usd = 5  # Lower minimum for more trades
        self.consolidation_threshold = 1.0  # Consolidate positions under $1
        self.momentum_threshold = 5  # 5%+ moves get priority

        self.logger.info("🚀 Aggressive Portfolio Multiplier initialized")
        self.logger.info("💥 EXTREME MODE: FORCE NUMBERS UP!")

    def get_portfolio_with_momentum(self) -> Dict:
        """Get portfolio with current momentum analysis"""
        try:
            account = self.client.get_account()
            portfolio = {"tokens": [], "total_value": 0}

            for balance in account["balances"]:
                free = float(balance["free"])
                locked = float(balance["locked"])
                total = free + locked

                if total > 0.001:  # Include even tiny balances
                    if balance["asset"] == "USDT":
                        usd_value = total
                        price = 1.0
                        momentum = 0
                    else:
                        try:
                            symbol = balance["asset"] + "USDT"
                            ticker_data = self.client.get_ticker(symbol=symbol)
                            price = float(ticker_data["lastPrice"])
                            momentum = float(ticker_data["priceChangePercent"])
                            usd_value = total * price
                        except:
                            price = 0
                            momentum = 0
                            usd_value = 0

                    if usd_value > 0.001:
                        portfolio["tokens"].append(
                            {
                                "asset": balance["asset"],
                                "amount": total,
                                "price": price,
                                "usd_value": usd_value,
                                "momentum": momentum,
                                "free": free,
                                "locked": locked,
                                "performance_category": self.categorize_performance(
                                    momentum, usd_value
                                ),
                            }
                        )
                        portfolio["total_value"] += usd_value

            # Sort by value
            portfolio["tokens"].sort(key=lambda x: x["usd_value"], reverse=True)

            return portfolio

        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            return {"tokens": [], "total_value": 0}

    def categorize_performance(self, momentum: float, value: float) -> str:
        """Categorize token performance"""
        if value < self.consolidation_threshold:
            return "DUST"
        elif momentum > 10:
            return "ROCKET"
        elif momentum > 3:
            return "RISING"
        elif momentum > -3:
            return "STABLE"
        elif momentum > -10:
            return "DECLINING"
        else:
            return "FALLING"

    def find_momentum_multipliers(self) -> List[Dict]:
        """Find tokens with extreme momentum potential"""
        try:
            # Get all USDT pairs
            exchange_info = self.client.get_exchange_info()
            usdt_pairs = [
                s["symbol"]
                for s in exchange_info["symbols"]
                if s["status"] == "TRADING" and s["quoteAsset"] == "USDT"
            ]

            # Get tickers in batches to avoid rate limits
            all_tickers = self.client.get_ticker()
            ticker_dict = {t["symbol"]: t for t in all_tickers}

            multipliers = []

            for symbol in usdt_pairs:
                if symbol in ticker_dict:
                    ticker = ticker_dict[symbol]
                    volume_usd = float(ticker["quoteVolume"])
                    price_change = float(ticker["priceChangePercent"])
                    current_price = float(ticker["lastPrice"])

                    # Calculate multiplier potential
                    multiplier_score = 0
                    factors = []

                    # 1. EXTREME momentum bonus
                    if abs(price_change) > 15:
                        multiplier_score += 20
                        factors.append(f"EXTREME momentum: {price_change:+.1f}%")
                    elif abs(price_change) > 10:
                        multiplier_score += 15
                        factors.append(f"HIGH momentum: {price_change:+.1f}%")
                    elif abs(price_change) > 5:
                        multiplier_score += 10
                        factors.append(f"Good momentum: {price_change:+.1f}%")

                    # 2. Volume surge multiplier
                    if volume_usd > 1000000:  # High volume = more momentum
                        multiplier_score += 5
                        factors.append("High volume")
                    elif 100000 < volume_usd < 1000000:
                        multiplier_score += 8
                        factors.append("Medium volume surge")
                    elif 10000 < volume_usd < 100000:
                        multiplier_score += 12
                        factors.append("Low volume breakout")
                    elif volume_usd < 10000:
                        multiplier_score += 15
                        factors.append("Micro cap explosion")

                    # 3. Price level multiplier
                    if current_price < 0.001:
                        multiplier_score += 15
                        factors.append("Ultra micro price")
                    elif current_price < 0.01:
                        multiplier_score += 10
                        factors.append("Micro price")
                    elif current_price < 0.1:
                        multiplier_score += 5
                        factors.append("Low price")

                    # 4. Name-based multiplier (memes, AI, gaming, etc.)
                    token_name = symbol.replace("USDT", "").lower()
                    multiplier_keywords = {
                        "meme": [
                            "doge",
                            "shib",
                            "pepe",
                            "floki",
                            "bonk",
                            "meme",
                            "cat",
                            "frog",
                        ],
                        "ai": ["ai", "gpt", "chat", "bot", "neural", "brain", "mind"],
                        "gaming": ["game", "play", "nft", "meta", "vr", "ar", "pixel"],
                        "defi": ["swap", "farm", "yield", "stake", "lend", "vault"],
                        "anime": [
                            "anime",
                            "manga",
                            "kawaii",
                            "chan",
                            "senpai",
                            "otaku",
                        ],
                    }

                    for category, keywords in multiplier_keywords.items():
                        if any(kw in token_name for kw in keywords):
                            multiplier_score += 8
                            factors.append(f"{category.upper()} narrative")
                            break

                    if multiplier_score > 15:  # Only high-potential multipliers
                        multipliers.append(
                            {
                                "symbol": symbol,
                                "multiplier_score": multiplier_score,
                                "volume_usd": volume_usd,
                                "price_change_24h": price_change,
                                "current_price": current_price,
                                "factors": factors,
                                "reasoning": " + ".join(factors),
                            }
                        )

            # Sort by multiplier score
            multipliers.sort(key=lambda x: x["multiplier_score"], reverse=True)

            self.logger.info(f"🚀 Found {len(multipliers)} momentum multipliers")
            return multipliers[:20]  # Top 20

        except Exception as e:
            self.logger.error(f"Error finding multipliers: {e}")
            return []

    def create_aggressive_rebalancing_plan(
        self, portfolio: Dict, multipliers: List[Dict]
    ) -> List[Dict]:
        """Create aggressive rebalancing plan"""
        try:
            trades = []
            total_value = portfolio["total_value"]

            # 1. CONSOLIDATE DUST (sell tiny positions)
            dust_trades = []
            dust_value = 0

            for token in portfolio["tokens"]:
                if (
                    token["performance_category"] == "DUST"
                    and token["asset"] != "USDT"
                    and token["usd_value"] < self.consolidation_threshold
                ):
                    dust_trades.append(
                        {
                            "action": "SELL",
                            "symbol": token["asset"] + "USDT",
                            "asset": token["asset"],
                            "amount": token["amount"],
                            "usd_value": token["usd_value"],
                            "reasoning": f"Consolidating dust: ${token['usd_value']:.3f}",
                        }
                    )
                    dust_value += token["usd_value"]

            # 2. SELL DECLINING POSITIONS
            declining_trades = []
            declining_value = 0

            for token in portfolio["tokens"]:
                if (
                    token["performance_category"] in ["DECLINING", "FALLING"]
                    and token["asset"] != "USDT"
                    and token["usd_value"] > 5
                ):  # Only sell meaningful positions
                    declining_trades.append(
                        {
                            "action": "SELL",
                            "symbol": token["asset"] + "USDT",
                            "asset": token["asset"],
                            "amount": token["amount"],
                            "usd_value": token["usd_value"],
                            "reasoning": f"Declining momentum: {token['momentum']:+.2f}%",
                        }
                    )
                    declining_value += token["usd_value"]

            # 3. BUY TOP MULTIPLIERS
            available_capital = dust_value + declining_value

            # Add current USDT
            for token in portfolio["tokens"]:
                if token["asset"] == "USDT":
                    available_capital += token["usd_value"]
                    break

            # Distribute among top multipliers
            buy_trades = []
            if available_capital > 10 and multipliers:
                allocation_per_token = min(
                    available_capital / 3, total_value * 0.15
                )  # Max 15% per new position

                for i, multiplier in enumerate(multipliers[:3]):  # Top 3 multipliers
                    if allocation_per_token >= self.min_trade_usd:
                        buy_trades.append(
                            {
                                "action": "BUY",
                                "symbol": multiplier["symbol"],
                                "target_usd": allocation_per_token,
                                "multiplier_score": multiplier["multiplier_score"],
                                "reasoning": f"Score: {multiplier['multiplier_score']:.0f} - {multiplier['reasoning']}",
                            }
                        )

            # Combine all trades
            all_trades = dust_trades + declining_trades + buy_trades

            return all_trades

        except Exception as e:
            self.logger.error(f"Error creating rebalancing plan: {e}")
            return []

    def execute_aggressive_trades(self, trades: List[Dict]) -> bool:
        """Execute aggressive trades"""
        try:
            if not trades:
                print("❌ No trades to execute")
                return False

            executed_count = 0

            print("💥 EXECUTING AGGRESSIVE REBALANCING!")
            print("=" * 50)

            # Execute SELL orders first
            for trade in trades:
                if trade["action"] == "SELL":
                    print(f"🔻 SELLING {trade['asset']}: ${trade['usd_value']:.3f}")
                    print(f"   Reason: {trade['reasoning']}")

                    try:
                        # Handle very small amounts
                        if trade["usd_value"] < 1:
                            # Try to sell all
                            order = self.client.order_market_sell(
                                symbol=trade["symbol"],
                                quantity=f"{trade['amount']:.8f}".rstrip("0").rstrip(
                                    "."
                                ),
                            )
                        else:
                            order = self.client.order_market_sell(
                                symbol=trade["symbol"], quantity=trade["amount"]
                            )

                        print(f"   ✅ SOLD - Order ID: {order['orderId']}")
                        executed_count += 1
                        time.sleep(0.5)  # Rate limiting

                    except Exception as e:
                        print(f"   ❌ SELL FAILED: {e}")
                        continue

            # Wait for settlement
            if executed_count > 0:
                print("⏳ Waiting for settlement...")
                time.sleep(2)

            # Execute BUY orders
            for trade in trades:
                if trade["action"] == "BUY":
                    print(f"🔺 BUYING {trade['symbol']}: ${trade['target_usd']:.2f}")
                    print(f"   Score: {trade['multiplier_score']:.0f}")
                    print(f"   Reason: {trade['reasoning']}")

                    try:
                        order = self.client.order_market_buy(
                            symbol=trade["symbol"], quoteOrderQty=trade["target_usd"]
                        )

                        print(f"   ✅ BOUGHT - Order ID: {order['orderId']}")
                        executed_count += 1
                        time.sleep(0.5)  # Rate limiting

                    except Exception as e:
                        print(f"   ❌ BUY FAILED: {e}")
                        continue

            print(f"\n🎯 EXECUTED {executed_count} TRADES!")
            return executed_count > 0

        except Exception as e:
            self.logger.error(f"Error executing trades: {e}")
            return False

    def run_aggressive_session(self):
        """Run aggressive portfolio multiplication session"""
        try:
            print("💥 AGGRESSIVE PORTFOLIO MULTIPLIER")
            print("=" * 60)
            print("🚀 EXTREME MODE: FORCE THE NUMBERS UP!")
            print(
                "Strategy: Consolidate dust, sell declining, buy momentum multipliers"
            )
            print()

            # Get portfolio with momentum
            portfolio = self.get_portfolio_with_momentum()

            print(f"💰 Current Portfolio Value: ${portfolio['total_value']:.2f}")
            print("\n📊 CURRENT POSITIONS BY PERFORMANCE:")
            print("-" * 50)

            categories = {}
            for token in portfolio["tokens"]:
                cat = token["performance_category"]
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(token)

            for category, tokens in categories.items():
                print(f"\n{category}:")
                for token in tokens:
                    print(
                        f"  {token['asset']:8s} | ${token['usd_value']:8.2f} | {token['momentum']:+6.2f}%"
                    )

            # Find momentum multipliers
            print("\n🔍 Finding momentum multipliers...")
            multipliers = self.find_momentum_multipliers()

            if multipliers:
                print("\n🚀 TOP MOMENTUM MULTIPLIERS:")
                print("-" * 70)
                for i, mult in enumerate(multipliers[:10], 1):
                    print(
                        f"{i:2d}. {mult['symbol']:12s} | Score: {mult['multiplier_score']:3.0f} | "
                        f"24h: {mult['price_change_24h']:+6.2f}% | ${mult['current_price']:.6f}"
                    )
                    print(f"    {mult['reasoning']}")

            # Create rebalancing plan
            print("\n📋 Creating aggressive rebalancing plan...")
            trades = self.create_aggressive_rebalancing_plan(portfolio, multipliers)

            if not trades:
                print("❌ No aggressive trades needed - portfolio already optimized")
                return

            print(f"\n💥 PROPOSED AGGRESSIVE TRADES ({len(trades)} total):")
            print("-" * 60)

            sells = [t for t in trades if t["action"] == "SELL"]
            buys = [t for t in trades if t["action"] == "BUY"]

            total_sell = sum(t["usd_value"] for t in sells)
            total_buy = sum(t["target_usd"] for t in buys)

            for trade in sells:
                print(
                    f"🔻 SELL {trade['asset']:8s} | ${trade['usd_value']:7.2f} | {trade['reasoning']}"
                )

            for trade in buys:
                print(
                    f"🔺 BUY  {trade['symbol']:8s} | ${trade['target_usd']:7.2f} | {trade['reasoning']}"
                )

            print(f"\nCapital freed up: ${total_sell:.2f}")
            print(f"New investments:  ${total_buy:.2f}")

            # Confirmation
            print("\n⚠️  AGGRESSIVE REBALANCING - HIGH RISK/HIGH REWARD!")
            confirm = input("Type 'FORCE NUMBERS UP' to execute: ")

            if confirm != "FORCE NUMBERS UP":
                print("❌ Aggressive session cancelled")
                return

            # Execute
            success = self.execute_aggressive_trades(trades)

            if success:
                print("\n🎉 AGGRESSIVE REBALANCING COMPLETE!")
                print("💥 PORTFOLIO FORCEFULLY OPTIMIZED!")
                print("🚀 NUMBERS SHOULD GO UP AGGRESSIVELY! 🚀")
            else:
                print("❌ Aggressive rebalancing failed")

        except KeyboardInterrupt:
            print("\n👋 Aggressive session cancelled")
        except Exception as e:
            self.logger.error(f"Aggressive session error: {e}")


def main():
    """Main function"""
    multiplier = AggressivePortfolioMultiplier()
    multiplier.run_aggressive_session()


if __name__ == "__main__":
    main()
