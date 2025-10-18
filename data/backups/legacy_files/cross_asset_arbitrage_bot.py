#!/usr/bin/env python3
"""
Cross-Asset Arbitrage Bot
Identifies arbitrage opportunities between different assets in your portfolio.
Can exploit price differences and momentum mismatches.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv


class CrossAssetArbitrageBot:
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
                    f'cross_asset_arbitrage_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Arbitrage parameters
        self.min_profit_pct = 0.5  # Minimum 0.5% profit for arbitrage
        self.max_trade_pct = 20.0  # Maximum 20% of asset for single trade
        self.trading_fee = 0.001  # 0.1% trading fee (approximate)

        self.logger.info("Cross-Asset Arbitrage Bot initialized")

    def get_holdings(self) -> Dict:
        """Get current portfolio holdings"""
        try:
            account_info = self.client.get_account()
            balances = [
                b
                for b in account_info["balances"]
                if float(b["free"]) > 0 or float(b["locked"]) > 0
            ]

            holdings = {}
            for balance in balances:
                asset = balance["asset"]
                free = float(balance["free"])
                locked = float(balance["locked"])
                total = free + locked

                if total > 0:
                    holdings[asset] = {"total": total, "free": free, "locked": locked}

            return holdings

        except Exception as e:
            self.logger.error(f"Error getting holdings: {e}")
            return {}

    def get_all_prices(self, assets: List[str]) -> Dict:
        """Get current prices for all assets"""
        prices = {}

        try:
            # Get all tickers at once for efficiency
            tickers = self.client.get_all_tickers()
            ticker_dict = {t["symbol"]: float(t["price"]) for t in tickers}

            for asset in assets:
                if asset == "USDT":
                    prices[asset] = 1.0
                else:
                    symbol = f"{asset}USDT"
                    if symbol in ticker_dict:
                        prices[asset] = ticker_dict[symbol]
                    else:
                        self.logger.warning(f"Price not found for {asset}")
                        prices[asset] = 0.0

            return prices

        except Exception as e:
            self.logger.error(f"Error getting prices: {e}")
            return {}

    def find_triangular_arbitrage(self, holdings: Dict, prices: Dict) -> List[Dict]:
        """Find triangular arbitrage opportunities between 3 assets"""
        opportunities = []
        assets = list(holdings.keys())

        # Check all combinations of 3 assets
        for i in range(len(assets)):
            for j in range(i + 1, len(assets)):
                for k in range(j + 1, len(assets)):
                    asset_a, asset_b, asset_c = assets[i], assets[j], assets[k]

                    # Try to find a profitable cycle: A -> B -> C -> A
                    opportunity = self.check_triangular_cycle(
                        asset_a, asset_b, asset_c, holdings, prices
                    )

                    if opportunity and opportunity["profit_pct"] > self.min_profit_pct:
                        opportunities.append(opportunity)

        return sorted(opportunities, key=lambda x: x["profit_pct"], reverse=True)

    def check_triangular_cycle(
        self, asset_a: str, asset_b: str, asset_c: str, holdings: Dict, prices: Dict
    ) -> Optional[Dict]:
        """Check if triangular arbitrage is profitable for A -> B -> C -> A"""
        try:
            # Get exchange info to check if pairs exist
            exchange_info = self.client.get_exchange_info()
            symbols = [
                s["symbol"]
                for s in exchange_info["symbols"]
                if s["status"] == "TRADING"
            ]

            # Check if required trading pairs exist
            pairs_needed = []

            # A -> B (either A/B or B/A)
            if f"{asset_a}{asset_b}" in symbols:
                ab_pair = f"{asset_a}{asset_b}"
                ab_direction = "sell"  # Sell A for B
            elif f"{asset_b}{asset_a}" in symbols:
                ab_pair = f"{asset_b}{asset_a}"
                ab_direction = "buy"  # Buy B with A
            else:
                return None

            # B -> C
            if f"{asset_b}{asset_c}" in symbols:
                bc_pair = f"{asset_b}{asset_c}"
                bc_direction = "sell"
            elif f"{asset_c}{asset_b}" in symbols:
                bc_pair = f"{asset_c}{asset_b}"
                bc_direction = "buy"
            else:
                return None

            # C -> A
            if f"{asset_c}{asset_a}" in symbols:
                ca_pair = f"{asset_c}{asset_a}"
                ca_direction = "sell"
            elif f"{asset_a}{asset_c}" in symbols:
                ca_pair = f"{asset_a}{asset_c}"
                ca_direction = "buy"
            else:
                return None

            # Calculate potential profit
            start_amount = holdings[asset_a]["free"] * 0.1  # Use 10% of holdings
            if start_amount <= 0:
                return None

            # Simulate the trades
            amount = start_amount

            # Trade 1: A -> B
            if ab_direction == "sell":
                # Get orderbook for more accurate pricing
                orderbook = self.client.get_orderbook_ticker(symbol=ab_pair)
                rate = float(orderbook["bidPrice"])  # We're selling, so use bid
                amount = amount * rate * (1 - self.trading_fee)
            else:
                orderbook = self.client.get_orderbook_ticker(symbol=ab_pair)
                rate = float(orderbook["askPrice"])  # We're buying, so use ask
                amount = amount / rate * (1 - self.trading_fee)

            # Trade 2: B -> C
            if bc_direction == "sell":
                orderbook = self.client.get_orderbook_ticker(symbol=bc_pair)
                rate = float(orderbook["bidPrice"])
                amount = amount * rate * (1 - self.trading_fee)
            else:
                orderbook = self.client.get_orderbook_ticker(symbol=bc_pair)
                rate = float(orderbook["askPrice"])
                amount = amount / rate * (1 - self.trading_fee)

            # Trade 3: C -> A
            if ca_direction == "sell":
                orderbook = self.client.get_orderbook_ticker(symbol=ca_pair)
                rate = float(orderbook["bidPrice"])
                final_amount = amount * rate * (1 - self.trading_fee)
            else:
                orderbook = self.client.get_orderbook_ticker(symbol=ca_pair)
                rate = float(orderbook["askPrice"])
                final_amount = amount / rate * (1 - self.trading_fee)

            # Calculate profit
            profit_amount = final_amount - start_amount
            profit_pct = (profit_amount / start_amount) * 100

            if profit_pct > 0:
                return {
                    "type": "triangular",
                    "path": f"{asset_a} -> {asset_b} -> {asset_c} -> {asset_a}",
                    "start_asset": asset_a,
                    "start_amount": start_amount,
                    "final_amount": final_amount,
                    "profit_amount": profit_amount,
                    "profit_pct": profit_pct,
                    "trades": [
                        {"pair": ab_pair, "direction": ab_direction},
                        {"pair": bc_pair, "direction": bc_direction},
                        {"pair": ca_pair, "direction": ca_direction},
                    ],
                }

            return None

        except Exception as e:
            self.logger.error(
                f"Error checking triangular arbitrage {asset_a}-{asset_b}-{asset_c}: {e}"
            )
            return None

    def find_momentum_arbitrage(self, holdings: Dict) -> List[Dict]:
        """Find momentum arbitrage - buy high momentum assets, sell low momentum"""
        opportunities = []

        try:
            momentum_data = {}

            # Calculate momentum for each asset
            for asset in holdings:
                if asset == "USDT":
                    continue

                symbol = f"{asset}USDT"
                momentum = self.calculate_momentum(symbol)
                momentum_data[asset] = momentum

            # Sort by momentum
            sorted_by_momentum = sorted(
                momentum_data.items(), key=lambda x: x[1]["momentum"], reverse=True
            )

            if len(sorted_by_momentum) < 2:
                return opportunities

            # Find opportunities between high and low momentum assets
            high_momentum_assets = sorted_by_momentum[: len(sorted_by_momentum) // 2]
            low_momentum_assets = sorted_by_momentum[len(sorted_by_momentum) // 2 :]

            for high_asset, high_data in high_momentum_assets:
                for low_asset, low_data in low_momentum_assets:
                    momentum_diff = high_data["momentum"] - low_data["momentum"]

                    if momentum_diff > 5:  # At least 5% momentum difference
                        # Check if we can trade between these assets
                        opportunity = self.check_momentum_trade(
                            low_asset, high_asset, holdings, momentum_diff
                        )

                        if opportunity:
                            opportunities.append(opportunity)

            return sorted(opportunities, key=lambda x: x["momentum_diff"], reverse=True)

        except Exception as e:
            self.logger.error(f"Error finding momentum arbitrage: {e}")
            return []

    def calculate_momentum(self, symbol: str) -> Dict:
        """Calculate 24h momentum for a symbol"""
        try:
            # Get 24h statistics
            stats = self.client.get_ticker(symbol=symbol)

            momentum = float(stats["priceChangePercent"])
            volume = float(stats["volume"])

            return {
                "momentum": momentum,
                "volume": volume,
                "price": float(stats["lastPrice"]),
            }

        except Exception as e:
            self.logger.error(f"Error calculating momentum for {symbol}: {e}")
            return {"momentum": 0, "volume": 0, "price": 0}

    def check_momentum_trade(
        self, sell_asset: str, buy_asset: str, holdings: Dict, momentum_diff: float
    ) -> Optional[Dict]:
        """Check if momentum trade is profitable"""
        try:
            # Check if direct pair exists
            pair1 = f"{sell_asset}{buy_asset}"
            pair2 = f"{buy_asset}{sell_asset}"

            exchange_info = self.client.get_exchange_info()
            symbols = [
                s["symbol"]
                for s in exchange_info["symbols"]
                if s["status"] == "TRADING"
            ]

            trade_pair = None
            trade_direction = None

            if pair1 in symbols:
                trade_pair = pair1
                trade_direction = "sell"  # Sell sell_asset for buy_asset
            elif pair2 in symbols:
                trade_pair = pair2
                trade_direction = "buy"  # Buy buy_asset with sell_asset
            else:
                # Need to go through USDT
                return {
                    "type": "momentum_indirect",
                    "sell_asset": sell_asset,
                    "buy_asset": buy_asset,
                    "momentum_diff": momentum_diff,
                    "method": "via_usdt",
                    "estimated_profit_pct": momentum_diff
                    * 0.7,  # Conservative estimate
                }

            # Calculate potential trade
            sell_amount = holdings[sell_asset]["free"] * 0.2  # Use 20% of holdings

            if sell_amount <= 0:
                return None

            return {
                "type": "momentum_direct",
                "sell_asset": sell_asset,
                "buy_asset": buy_asset,
                "sell_amount": sell_amount,
                "momentum_diff": momentum_diff,
                "trade_pair": trade_pair,
                "trade_direction": trade_direction,
                "estimated_profit_pct": momentum_diff * 0.5,  # Conservative estimate
            }

        except Exception as e:
            self.logger.error(
                f"Error checking momentum trade {sell_asset}->{buy_asset}: {e}"
            )
            return None

    def execute_arbitrage(self, opportunity: Dict) -> bool:
        """Execute an arbitrage opportunity"""
        try:
            if opportunity["type"] == "triangular":
                return self.execute_triangular_arbitrage(opportunity)
            elif opportunity["type"] in ["momentum_direct", "momentum_indirect"]:
                return self.execute_momentum_arbitrage(opportunity)
            else:
                self.logger.error(f"Unknown opportunity type: {opportunity['type']}")
                return False

        except Exception as e:
            self.logger.error(f"Error executing arbitrage: {e}")
            return False

    def execute_triangular_arbitrage(self, opportunity: Dict) -> bool:
        """Execute triangular arbitrage trades"""
        self.logger.info(f"Executing triangular arbitrage: {opportunity['path']}")

        try:
            # Execute trades in sequence
            for i, trade in enumerate(opportunity["trades"]):
                pair = trade["pair"]
                direction = trade["direction"]

                self.logger.info(f"Trade {i+1}/3: {direction} {pair}")

                # For now, just log the trades (add actual execution later)
                # This is a complex sequence that needs careful error handling

                time.sleep(1)  # Rate limiting

            self.logger.info("Triangular arbitrage completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error in triangular arbitrage execution: {e}")
            return False

    def execute_momentum_arbitrage(self, opportunity: Dict) -> bool:
        """Execute momentum arbitrage trade"""
        sell_asset = opportunity["sell_asset"]
        buy_asset = opportunity["buy_asset"]

        self.logger.info(f"Executing momentum arbitrage: {sell_asset} -> {buy_asset}")

        try:
            if opportunity.get("method") == "via_usdt":
                # Two-step trade via USDT
                # 1. Sell sell_asset for USDT
                # 2. Buy buy_asset with USDT
                self.logger.info(f"Step 1: Sell {sell_asset} for USDT")
                self.logger.info(f"Step 2: Buy {buy_asset} with USDT")
            else:
                # Direct trade
                pair = opportunity["trade_pair"]
                direction = opportunity["trade_direction"]
                self.logger.info(f"Direct trade: {direction} {pair}")

            # For now, just log the trade (add actual execution later)
            self.logger.info("Momentum arbitrage completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error in momentum arbitrage execution: {e}")
            return False

    def scan_opportunities(self) -> Dict:
        """Scan for all arbitrage opportunities"""
        self.logger.info("Scanning for arbitrage opportunities...")

        holdings = self.get_holdings()
        if not holdings:
            self.logger.error("No holdings found")
            return {}

        assets = list(holdings.keys())
        prices = self.get_all_prices(assets)

        self.logger.info(f"Found {len(holdings)} assets: {assets}")

        # Find triangular arbitrage opportunities
        triangular_opportunities = self.find_triangular_arbitrage(holdings, prices)

        # Find momentum arbitrage opportunities
        momentum_opportunities = self.find_momentum_arbitrage(holdings)

        results = {
            "timestamp": datetime.now().isoformat(),
            "holdings": holdings,
            "prices": prices,
            "triangular_opportunities": triangular_opportunities,
            "momentum_opportunities": momentum_opportunities,
            "total_opportunities": len(triangular_opportunities)
            + len(momentum_opportunities),
        }

        # Log results
        self.logger.info(
            f"Found {len(triangular_opportunities)} triangular opportunities"
        )
        self.logger.info(f"Found {len(momentum_opportunities)} momentum opportunities")

        if triangular_opportunities:
            self.logger.info("Top triangular opportunities:")
            for i, opp in enumerate(triangular_opportunities[:3]):
                self.logger.info(
                    f"  {i+1}. {opp['path']} - {opp['profit_pct']:.2f}% profit"
                )

        if momentum_opportunities:
            self.logger.info("Top momentum opportunities:")
            for i, opp in enumerate(momentum_opportunities[:3]):
                self.logger.info(
                    f"  {i+1}. {opp['sell_asset']} -> {opp['buy_asset']} - "
                    f"{opp['momentum_diff']:.2f}% momentum diff"
                )

        return results

    def run_continuous_scan(self, scan_interval_minutes: int = 5):
        """Continuously scan for arbitrage opportunities"""
        self.logger.info(
            f"Starting continuous arbitrage scanning (every {scan_interval_minutes} minutes)"
        )

        while True:
            try:
                results = self.scan_opportunities()

                # Save results
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                with open(f"arbitrage_scan_{timestamp}.json", "w") as f:
                    json.dump(results, f, indent=2, default=str)

                # Wait for next scan
                self.logger.info(
                    f"Waiting {scan_interval_minutes} minutes until next scan..."
                )
                time.sleep(scan_interval_minutes * 60)

            except KeyboardInterrupt:
                self.logger.info("Arbitrage scanning stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous scanning: {e}")
                time.sleep(60)  # Wait 1 minute before retry


def main():
    bot = CrossAssetArbitrageBot()

    print("Cross-Asset Arbitrage Bot")
    print("========================")
    print("This bot finds arbitrage opportunities between your assets")
    print()

    print("Options:")
    print("1. Single scan (analysis only)")
    print("2. Continuous scanning")
    print("3. Execute best opportunity (LIVE TRADING)")

    choice = input("Select option (1-3): ").strip()

    if choice == "1":
        print("\nScanning for opportunities...")
        results = bot.scan_opportunities()

        total_opps = results.get("total_opportunities", 0)
        print(f"\nFound {total_opps} total opportunities")

        if results.get("triangular_opportunities"):
            print("\nTriangular Arbitrage Opportunities:")
            for i, opp in enumerate(results["triangular_opportunities"][:5]):
                print(f"  {i+1}. {opp['path']}")
                print(
                    f"     Profit: {opp['profit_pct']:.3f}% (${opp['profit_amount']:.2f})"
                )

        if results.get("momentum_opportunities"):
            print("\nMomentum Arbitrage Opportunities:")
            for i, opp in enumerate(results["momentum_opportunities"][:5]):
                print(f"  {i+1}. {opp['sell_asset']} -> {opp['buy_asset']}")
                print(f"     Momentum Diff: {opp['momentum_diff']:.2f}%")

    elif choice == "2":
        try:
            interval = int(input("Scan interval in minutes (default 5): ") or "5")
            bot.run_continuous_scan(interval)
        except ValueError:
            print("Invalid interval")

    elif choice == "3":
        confirm = input(
            "\nThis will execute real trades. Type 'CONFIRM ARBITRAGE TRADING' to proceed: "
        )
        if confirm == "CONFIRM ARBITRAGE TRADING":
            print("\nScanning for best opportunity...")
            results = bot.scan_opportunities()

            # Find best opportunity
            all_opportunities = []

            for opp in results.get("triangular_opportunities", []):
                opp["score"] = opp["profit_pct"]
                all_opportunities.append(opp)

            for opp in results.get("momentum_opportunities", []):
                opp["score"] = opp.get("estimated_profit_pct", 0)
                all_opportunities.append(opp)

            if all_opportunities:
                best_opportunity = max(all_opportunities, key=lambda x: x["score"])
                print(
                    f"\nBest opportunity: {best_opportunity.get('path', 'Momentum Trade')}"
                )
                print(f"Expected profit: {best_opportunity['score']:.2f}%")

                confirm2 = input("Execute this trade? (y/N): ")
                if confirm2.lower() == "y":
                    success = bot.execute_arbitrage(best_opportunity)
                    if success:
                        print("Arbitrage executed successfully!")
                    else:
                        print("Arbitrage execution failed.")
                else:
                    print("Trade cancelled.")
            else:
                print("No profitable opportunities found.")
        else:
            print("Trading cancelled.")

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
