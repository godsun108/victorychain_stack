#!/usr/bin/env python3
"""
Balanced Multi-Asset Trading Bot
Properly diversifies across all assets instead of concentrating in one token.
Maximum 20% allocation per asset for risk management.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv


class BalancedTradingBot:
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
                    f'balanced_trading_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Conservative trading parameters
        self.min_trade_value_usdt = 15.0  # Minimum trade value
        self.rebalance_threshold = 8.0  # 8% threshold for rebalancing
        self.max_asset_allocation = 20.0  # Maximum 20% per asset
        self.min_asset_allocation = 3.0  # Minimum 3% per asset
        self.usdt_reserve = 15.0  # Keep 15% in USDT

        self.logger.info("Balanced Trading Bot initialized")

    def get_portfolio_balance(self) -> Dict:
        """Get current portfolio balance"""
        try:
            account_info = self.client.get_account()
            balances = [
                b
                for b in account_info["balances"]
                if float(b["free"]) > 0 or float(b["locked"]) > 0
            ]

            portfolio = {}
            total_usdt_value = 0

            for balance in balances:
                asset = balance["asset"]
                free = float(balance["free"])
                locked = float(balance["locked"])
                total = free + locked

                if total > 0:
                    try:
                        if asset == "USDT":
                            usdt_value = total
                            price = 1.0
                        else:
                            ticker = self.client.get_symbol_ticker(
                                symbol=f"{asset}USDT"
                            )
                            price = float(ticker["price"])
                            usdt_value = total * price

                        portfolio[asset] = {
                            "amount": total,
                            "free": free,
                            "locked": locked,
                            "price": price,
                            "usdt_value": usdt_value,
                            "allocation_pct": 0,
                        }
                        total_usdt_value += usdt_value

                    except Exception as e:
                        self.logger.warning(f"Could not get price for {asset}: {e}")

            # Calculate allocation percentages
            for asset in portfolio:
                if total_usdt_value > 0:
                    portfolio[asset]["allocation_pct"] = (
                        portfolio[asset]["usdt_value"] / total_usdt_value * 100
                    )

            self.logger.info(f"Portfolio value: ${total_usdt_value:.2f}")
            return portfolio

        except Exception as e:
            self.logger.error(f"Error getting portfolio balance: {e}")
            return {}

    def calculate_momentum_score(self, symbol: str) -> float:
        """Calculate simple momentum score for ranking"""
        try:
            # Get 24h statistics
            stats = self.client.get_ticker(symbol=symbol)
            momentum = float(stats["priceChangePercent"])
            volume = float(stats["volume"])

            # Simple scoring: momentum + volume factor
            volume_factor = min(1.0, volume / 100000)  # Cap volume factor at 1.0
            score = momentum + (volume_factor * 2)  # Volume bonus up to 2 points

            return score

        except Exception as e:
            self.logger.error(f"Error calculating momentum for {symbol}: {e}")
            return 0.0

    def calculate_balanced_allocations(self, portfolio: Dict) -> Dict:
        """Calculate balanced target allocations with proper diversification"""
        assets = [asset for asset in portfolio.keys() if asset != "USDT"]

        if not assets:
            return {"USDT": 100.0}

        # Get momentum scores for all assets
        asset_scores = {}
        for asset in assets:
            symbol = f"{asset}USDT"
            score = self.calculate_momentum_score(symbol)
            asset_scores[asset] = score
            self.logger.info(f"{asset}: Momentum score = {score:.2f}")

        # Sort assets by score
        sorted_assets = sorted(asset_scores.items(), key=lambda x: x[1], reverse=True)

        # Calculate balanced allocations
        target_allocations = {}

        # Reserve USDT
        target_allocations["USDT"] = self.usdt_reserve
        remaining_allocation = 100.0 - self.usdt_reserve

        # Categorize assets by performance
        num_assets = len(sorted_assets)
        top_tier_count = max(1, num_assets // 3)  # Top 1/3
        mid_tier_count = max(1, num_assets // 3)  # Middle 1/3
        low_tier_count = num_assets - top_tier_count - mid_tier_count  # Remaining

        # Allocate by tiers with caps
        allocation_used = 0

        # Top tier: 15% max each
        top_allocation_per_asset = min(
            15.0, remaining_allocation * 0.6 / top_tier_count
        )
        for i in range(top_tier_count):
            asset, score = sorted_assets[i]
            allocation = min(self.max_asset_allocation, top_allocation_per_asset)
            target_allocations[asset] = allocation
            allocation_used += allocation
            self.logger.info(
                f"Top tier - {asset}: {allocation:.1f}% (score: {score:.2f})"
            )

        # Middle tier: 10% max each
        remaining_after_top = remaining_allocation - allocation_used
        if mid_tier_count > 0 and remaining_after_top > 0:
            mid_allocation_per_asset = min(
                10.0, remaining_after_top * 0.7 / mid_tier_count
            )
            for i in range(top_tier_count, top_tier_count + mid_tier_count):
                asset, score = sorted_assets[i]
                allocation = min(self.max_asset_allocation, mid_allocation_per_asset)
                target_allocations[asset] = allocation
                allocation_used += allocation
                self.logger.info(
                    f"Mid tier - {asset}: {allocation:.1f}% (score: {score:.2f})"
                )

        # Low tier: 5% max each
        remaining_after_mid = remaining_allocation - allocation_used
        if low_tier_count > 0 and remaining_after_mid > 0:
            low_allocation_per_asset = min(5.0, remaining_after_mid / low_tier_count)
            for i in range(top_tier_count + mid_tier_count, num_assets):
                asset, score = sorted_assets[i]
                allocation = max(self.min_asset_allocation, low_allocation_per_asset)
                target_allocations[asset] = allocation
                allocation_used += allocation
                self.logger.info(
                    f"Low tier - {asset}: {allocation:.1f}% (score: {score:.2f})"
                )

        # Redistribute any remaining allocation to USDT
        remaining_final = remaining_allocation - allocation_used
        if remaining_final > 0:
            target_allocations["USDT"] += remaining_final

        # Normalize to 100%
        total = sum(target_allocations.values())
        if total > 0:
            for asset in target_allocations:
                target_allocations[asset] = target_allocations[asset] / total * 100

        return target_allocations

    def execute_rebalancing(
        self, current_portfolio: Dict, target_allocations: Dict
    ) -> bool:
        """Execute trades to reach target allocations"""
        total_portfolio_value = sum(
            data["usdt_value"] for data in current_portfolio.values()
        )

        if total_portfolio_value < 50.0:  # Safety check
            self.logger.warning(
                f"Portfolio value too small: ${total_portfolio_value:.2f}"
            )
            return False

        trades_executed = []

        # First, sell assets that are over-allocated
        for asset, target_pct in target_allocations.items():
            if asset not in current_portfolio:
                continue

            current_pct = current_portfolio[asset]["allocation_pct"]
            difference_pct = current_pct - target_pct

            # Only sell if significantly over-allocated
            if difference_pct > self.rebalance_threshold:
                sell_value = total_portfolio_value * difference_pct / 100

                if sell_value > self.min_trade_value_usdt:
                    success = self.sell_asset(asset, sell_value, current_portfolio)
                    if success:
                        trades_executed.append(
                            {
                                "action": "sell",
                                "asset": asset,
                                "value": sell_value,
                                "reason": f"Over-allocated: {current_pct:.1f}% → {target_pct:.1f}%",
                            }
                        )

        # Wait a moment for balances to update
        time.sleep(2)

        # Refresh portfolio after sells
        updated_portfolio = self.get_portfolio_balance()

        # Then, buy assets that are under-allocated
        for asset, target_pct in target_allocations.items():
            if asset == "USDT":
                continue

            current_pct = updated_portfolio.get(asset, {}).get("allocation_pct", 0)
            difference_pct = target_pct - current_pct

            # Only buy if significantly under-allocated
            if difference_pct > self.rebalance_threshold:
                buy_value = total_portfolio_value * difference_pct / 100

                if buy_value > self.min_trade_value_usdt:
                    success = self.buy_asset(asset, buy_value, updated_portfolio)
                    if success:
                        trades_executed.append(
                            {
                                "action": "buy",
                                "asset": asset,
                                "value": buy_value,
                                "reason": f"Under-allocated: {current_pct:.1f}% → {target_pct:.1f}%",
                            }
                        )

        # Log results
        if trades_executed:
            self.logger.info(f"Executed {len(trades_executed)} rebalancing trades:")
            for trade in trades_executed:
                self.logger.info(
                    f"  {trade['action'].upper()} {trade['asset']}: ${trade['value']:.2f} - {trade['reason']}"
                )
            return True
        else:
            self.logger.info("No significant rebalancing needed")
            return False

    def sell_asset(self, asset: str, usdt_value: float, portfolio: Dict) -> bool:
        """Sell asset for USDT"""
        try:
            if asset == "USDT":
                return True

            symbol = f"{asset}USDT"

            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])

            # Calculate quantity to sell
            quantity = usdt_value / price
            available_balance = portfolio.get(asset, {}).get("free", 0)

            if quantity > available_balance:
                quantity = available_balance * 0.99  # Sell 99% to avoid rounding issues
                self.logger.warning(f"Selling available {asset}: {quantity}")

            if quantity <= 0:
                self.logger.warning(f"No {asset} available to sell")
                return False

            # Get precision info
            exchange_info = self.client.get_exchange_info()
            symbol_info = next(
                (s for s in exchange_info["symbols"] if s["symbol"] == symbol), None
            )

            if symbol_info:
                lot_size_filter = next(
                    (
                        f
                        for f in symbol_info["filters"]
                        if f["filterType"] == "LOT_SIZE"
                    ),
                    None,
                )
                if lot_size_filter:
                    step_size = float(lot_size_filter["stepSize"])
                    quantity = round(quantity / step_size) * step_size
                    min_qty = float(lot_size_filter["minQty"])

                    if quantity < min_qty:
                        self.logger.warning(
                            f"Quantity {quantity} below minimum {min_qty} for {symbol}"
                        )
                        return False

            # Execute sell order
            self.logger.info(f"Selling {quantity} {asset} for ~${usdt_value:.2f}")

            order = self.client.order_market_sell(
                symbol=symbol, quantity=f"{quantity:.8f}".rstrip("0").rstrip(".")
            )

            self.logger.info(f"Sell order executed: {order['orderId']}")
            return True

        except Exception as e:
            self.logger.error(f"Error selling {asset}: {e}")
            return False

    def buy_asset(self, asset: str, usdt_value: float, portfolio: Dict) -> bool:
        """Buy asset with USDT"""
        try:
            if asset == "USDT":
                return True

            symbol = f"{asset}USDT"

            # Check USDT balance
            usdt_balance = portfolio.get("USDT", {}).get("free", 0)
            if usdt_balance < usdt_value:
                usdt_value = usdt_balance * 0.95  # Use 95% of available USDT
                self.logger.warning(f"Limited USDT available: using ${usdt_value:.2f}")

            if usdt_value < self.min_trade_value_usdt:
                self.logger.warning(f"Insufficient USDT for {asset}: ${usdt_value:.2f}")
                return False

            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])

            # Calculate quantity to buy
            quantity = usdt_value / price

            # Get precision info
            exchange_info = self.client.get_exchange_info()
            symbol_info = next(
                (s for s in exchange_info["symbols"] if s["symbol"] == symbol), None
            )

            if symbol_info:
                lot_size_filter = next(
                    (
                        f
                        for f in symbol_info["filters"]
                        if f["filterType"] == "LOT_SIZE"
                    ),
                    None,
                )
                if lot_size_filter:
                    step_size = float(lot_size_filter["stepSize"])
                    quantity = round(quantity / step_size) * step_size
                    min_qty = float(lot_size_filter["minQty"])

                    if quantity < min_qty:
                        self.logger.warning(
                            f"Quantity {quantity} below minimum {min_qty} for {symbol}"
                        )
                        return False

            # Execute buy order
            self.logger.info(f"Buying {quantity} {asset} for ~${usdt_value:.2f}")

            order = self.client.order_market_buy(
                symbol=symbol, quantity=f"{quantity:.8f}".rstrip("0").rstrip(".")
            )

            self.logger.info(f"Buy order executed: {order['orderId']}")
            return True

        except Exception as e:
            self.logger.error(f"Error buying {asset}: {e}")
            return False

    def run_balanced_rebalancing(self):
        """Run one balanced rebalancing cycle"""
        self.logger.info("=== Starting Balanced Rebalancing ===")

        try:
            # Get current portfolio
            portfolio = self.get_portfolio_balance()
            if not portfolio:
                self.logger.error("Could not get portfolio data")
                return

            total_value = sum(data["usdt_value"] for data in portfolio.values())
            self.logger.info(f"Current portfolio value: ${total_value:.2f}")

            # Show current allocations
            self.logger.info("Current Allocations:")
            sorted_holdings = sorted(
                portfolio.items(), key=lambda x: x[1]["usdt_value"], reverse=True
            )
            for asset, data in sorted_holdings:
                self.logger.info(
                    f"  {asset}: {data['allocation_pct']:.1f}% (${data['usdt_value']:.2f})"
                )

            # Calculate balanced target allocations
            target_allocations = self.calculate_balanced_allocations(portfolio)

            self.logger.info("\nTarget Allocations (Balanced):")
            for asset, pct in sorted(
                target_allocations.items(), key=lambda x: x[1], reverse=True
            ):
                current_pct = portfolio.get(asset, {}).get("allocation_pct", 0)
                self.logger.info(f"  {asset}: {current_pct:.1f}% → {pct:.1f}%")

            # Execute rebalancing
            success = self.execute_rebalancing(portfolio, target_allocations)

            if success:
                self.logger.info("✅ Balanced rebalancing completed successfully")

                # Show final portfolio
                time.sleep(3)
                final_portfolio = self.get_portfolio_balance()
                final_value = sum(
                    data["usdt_value"] for data in final_portfolio.values()
                )
                self.logger.info(f"\nFinal portfolio value: ${final_value:.2f}")

                self.logger.info("Final Allocations:")
                final_sorted = sorted(
                    final_portfolio.items(),
                    key=lambda x: x[1]["usdt_value"],
                    reverse=True,
                )
                for asset, data in final_sorted[:8]:  # Show top 8
                    self.logger.info(
                        f"  {asset}: {data['allocation_pct']:.1f}% (${data['usdt_value']:.2f})"
                    )

            else:
                self.logger.info("No trades executed - portfolio already balanced")

            self.logger.info("=== Balanced Rebalancing Complete ===")

        except Exception as e:
            self.logger.error(f"Error in balanced rebalancing: {e}")


def main():
    bot = BalancedTradingBot()

    print("🎯 Balanced Multi-Asset Trading Bot")
    print("===================================")
    print("This bot creates a BALANCED diversified portfolio")
    print("• Maximum 20% allocation per asset")
    print("• Proper risk distribution across all holdings")
    print("• Conservative rebalancing approach")
    print()

    # Show current portfolio
    portfolio = bot.get_portfolio_balance()
    total_value = sum(data["usdt_value"] for data in portfolio.values())

    print(f"Current Portfolio (${total_value:.2f}):")
    sorted_holdings = sorted(
        portfolio.items(), key=lambda x: x[1]["usdt_value"], reverse=True
    )
    for asset, data in sorted_holdings:
        print(f"  {asset}: {data['allocation_pct']:.1f}% (${data['usdt_value']:.2f})")

    print("\nOptions:")
    print("1. Show balanced allocation plan (no trades)")
    print("2. Execute balanced rebalancing (LIVE TRADING)")

    choice = input("Select option (1-2): ").strip()

    if choice == "1":
        print("\nCalculating balanced allocations...")
        target_allocations = bot.calculate_balanced_allocations(portfolio)

        print("\n🎯 Recommended Balanced Allocations:")
        for asset, pct in sorted(
            target_allocations.items(), key=lambda x: x[1], reverse=True
        ):
            current_pct = portfolio.get(asset, {}).get("allocation_pct", 0)
            change = pct - current_pct
            arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
            print(f"  {asset}: {current_pct:.1f}% {arrow} {pct:.1f}% ({change:+.1f}%)")

    elif choice == "2":
        confirm = input(
            "\nThis will execute balanced rebalancing trades. Type 'CONFIRM BALANCED TRADING' to proceed: "
        )
        if confirm == "CONFIRM BALANCED TRADING":
            print("\nExecuting balanced rebalancing...")
            bot.run_balanced_rebalancing()
        else:
            print("Trading cancelled.")

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
