#!/usr/bin/env python3
"""
Multi-Asset Portfolio Trading Bot
Trades with ALL available assets in the portfolio, not just USDT.
Dynamically rebalances based on momentum analysis.
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
import requests


class MultiAssetTradingBot:
    def __init__(self, config_file="config.toml"):
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
                    f'multi_asset_trading_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Trading parameters
        self.min_trade_value_usdt = 10.0  # Minimum trade value in USDT
        self.rebalance_threshold = (
            10.0  # 10% threshold for rebalancing (more conservative)
        )
        self.stop_loss_pct = 0.15  # 15% stop loss
        self.momentum_period = 24  # Hours for momentum calculation
        self.risk_per_trade = 0.15  # 15% of portfolio per trade max (more conservative)

        # Portfolio state
        self.current_holdings = {}
        self.target_allocations = {}
        self.trading_pairs = []

        # Claude API for AI predictions
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")

        self.logger.info("Multi-Asset Trading Bot initialized")

    def get_portfolio_balance(self) -> Dict:
        """Get current portfolio balance and calculate USDT values"""
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
                            "allocation_pct": 0,  # Will calculate later
                        }
                        total_usdt_value += usdt_value

                    except Exception as e:
                        self.logger.warning(f"Could not get price for {asset}: {e}")
                        portfolio[asset] = {
                            "amount": total,
                            "free": free,
                            "locked": locked,
                            "price": 0,
                            "usdt_value": 0,
                            "allocation_pct": 0,
                        }

            # Calculate allocation percentages
            for asset in portfolio:
                if total_usdt_value > 0:
                    portfolio[asset]["allocation_pct"] = (
                        portfolio[asset]["usdt_value"] / total_usdt_value * 100
                    )

            self.current_holdings = portfolio
            self.logger.info(f"Portfolio value: ${total_usdt_value:.2f}")

            return portfolio

        except Exception as e:
            self.logger.error(f"Error getting portfolio balance: {e}")
            return {}

    def calculate_momentum(self, symbol: str, period_hours: int = 24) -> Dict:
        """Calculate momentum metrics for a trading pair"""
        try:
            # Get historical data
            klines = self.client.get_historical_klines(
                symbol, Client.KLINE_INTERVAL_1HOUR, f"{period_hours} hours ago UTC"
            )

            if len(klines) < 2:
                return {"momentum": 0, "volatility": 0, "trend": "neutral"}

            # Convert to DataFrame
            df = pd.DataFrame(
                klines,
                columns=[
                    "timestamp",
                    "open",
                    "high",
                    "low",
                    "close",
                    "volume",
                    "close_time",
                    "quote_volume",
                    "trades",
                    "taker_buy_base",
                    "taker_buy_quote",
                    "ignored",
                ],
            )

            df["close"] = df["close"].astype(float)
            df["volume"] = df["volume"].astype(float)

            # Calculate momentum indicators
            current_price = df["close"].iloc[-1]
            start_price = df["close"].iloc[0]
            momentum = (current_price - start_price) / start_price * 100

            # Calculate volatility (standard deviation of returns)
            returns = df["close"].pct_change().dropna()
            volatility = returns.std() * 100

            # Calculate trend (simple moving average slope)
            if len(df) >= 12:  # At least 12 hours of data
                recent_avg = df["close"].tail(6).mean()
                older_avg = df["close"].head(6).mean()
                trend = "bullish" if recent_avg > older_avg else "bearish"
            else:
                trend = "neutral"

            # Volume momentum
            recent_volume = df["volume"].tail(6).mean()
            older_volume = df["volume"].head(6).mean()
            volume_momentum = (
                (recent_volume - older_volume) / older_volume * 100
                if older_volume > 0
                else 0
            )

            return {
                "momentum": momentum,
                "volatility": volatility,
                "trend": trend,
                "volume_momentum": volume_momentum,
                "current_price": current_price,
            }

        except Exception as e:
            self.logger.error(f"Error calculating momentum for {symbol}: {e}")
            return {
                "momentum": 0,
                "volatility": 0,
                "trend": "neutral",
                "volume_momentum": 0,
            }

    def get_ai_prediction(self, asset: str, momentum_data: Dict) -> Dict:
        """Get AI prediction for asset using Claude API"""
        if not self.claude_api_key:
            return {"prediction": "neutral", "confidence": 0.5, "target_pct": 0}

        try:
            prompt = f"""
            Analyze {asset} trading opportunity with the following data:
            - 24h Momentum: {momentum_data.get('momentum', 0):.2f}%
            - Volatility: {momentum_data.get('volatility', 0):.2f}%
            - Trend: {momentum_data.get('trend', 'neutral')}
            - Volume Momentum: {momentum_data.get('volume_momentum', 0):.2f}%
            - Current Price: ${momentum_data.get('current_price', 0):.6f}
            
            Provide a JSON response with:
            1. prediction: "bullish", "bearish", or "neutral"
            2. confidence: 0.0 to 1.0
            3. target_pct: recommended portfolio allocation percentage (0-100)
            4. reason: brief explanation
            
            Focus on momentum and volatility patterns for short-term gains.
            """

            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.claude_api_key,
                "anthropic-version": "2023-06-01",
            }

            data = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            }

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["content"][0]["text"]

                # Try to extract JSON from response
                try:
                    # Find JSON in the response
                    import re

                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        prediction = json.loads(json_match.group())
                        return prediction
                except:
                    pass

            # Fallback based on momentum
            if momentum_data.get("momentum", 0) > 5:
                return {
                    "prediction": "bullish",
                    "confidence": 0.7,
                    "target_pct": 15,
                    "reason": "Strong positive momentum",
                }
            elif momentum_data.get("momentum", 0) < -5:
                return {
                    "prediction": "bearish",
                    "confidence": 0.7,
                    "target_pct": 5,
                    "reason": "Strong negative momentum",
                }
            else:
                return {
                    "prediction": "neutral",
                    "confidence": 0.5,
                    "target_pct": 10,
                    "reason": "Neutral momentum",
                }

        except Exception as e:
            self.logger.error(f"Error getting AI prediction for {asset}: {e}")
            return {"prediction": "neutral", "confidence": 0.5, "target_pct": 10}

    def analyze_all_assets(self) -> Dict:
        """Analyze momentum and AI predictions for all assets"""
        portfolio = self.get_portfolio_balance()
        analysis = {}

        for asset in portfolio:
            if asset == "USDT":
                continue

            symbol = f"{asset}USDT"
            self.logger.info(f"Analyzing {symbol}...")

            # Get momentum data
            momentum = self.calculate_momentum(symbol)

            # Get AI prediction
            ai_prediction = self.get_ai_prediction(asset, momentum)

            # Combine data
            analysis[asset] = {
                "current_allocation": portfolio[asset]["allocation_pct"],
                "current_value": portfolio[asset]["usdt_value"],
                "momentum": momentum,
                "ai_prediction": ai_prediction,
                "score": self.calculate_asset_score(momentum, ai_prediction),
            }

            self.logger.info(
                f"{asset}: Score={analysis[asset]['score']:.2f}, "
                f"Momentum={momentum.get('momentum', 0):.2f}%, "
                f"AI={ai_prediction.get('prediction', 'neutral')}"
            )

            time.sleep(0.1)  # Rate limiting

        return analysis

    def calculate_asset_score(self, momentum: Dict, ai_prediction: Dict) -> float:
        """Calculate combined score for asset ranking"""
        momentum_score = momentum.get("momentum", 0) / 10  # Normalize momentum
        volatility_penalty = (
            -momentum.get("volatility", 0) / 20
        )  # Penalize high volatility
        volume_score = momentum.get("volume_momentum", 0) / 20  # Volume momentum bonus

        ai_score = 0
        if ai_prediction.get("prediction") == "bullish":
            ai_score = ai_prediction.get("confidence", 0.5) * 2
        elif ai_prediction.get("prediction") == "bearish":
            ai_score = -ai_prediction.get("confidence", 0.5) * 2

        # Trend bonus
        trend_score = (
            1
            if momentum.get("trend") == "bullish"
            else -1 if momentum.get("trend") == "bearish" else 0
        )

        total_score = (
            momentum_score + volatility_penalty + volume_score + ai_score + trend_score
        )
        return total_score

    def calculate_target_allocations(self, analysis: Dict) -> Dict:
        """Calculate target portfolio allocations based on analysis - BALANCED DIVERSIFICATION"""
        # Sort assets by score
        sorted_assets = sorted(
            analysis.items(), key=lambda x: x[1]["score"], reverse=True
        )

        target_allocations = {}

        # Keep reasonable USDT for liquidity (15%)
        target_allocations["USDT"] = 15.0

        # More balanced allocation - no single asset over 25%
        remaining_allocation = 85.0
        num_assets = len(sorted_assets)

        # Divide assets into tiers for balanced allocation
        positive_score_assets = [
            asset for asset, data in sorted_assets if data["score"] > 0
        ]
        neutral_score_assets = [
            asset for asset, data in sorted_assets if -2 <= data["score"] <= 0
        ]
        negative_score_assets = [
            asset for asset, data in sorted_assets if data["score"] < -2
        ]

        # Tier 1: Top positive assets (max 20% each)
        tier1_allocation = 50.0  # 50% for top performers
        if positive_score_assets:
            allocation_per_asset = min(
                20.0, tier1_allocation / len(positive_score_assets)
            )
            for asset, _ in sorted_assets:
                if asset in positive_score_assets:
                    target_allocations[asset] = allocation_per_asset
                    remaining_allocation -= allocation_per_asset

        # Tier 2: Neutral assets (max 10% each)
        tier2_allocation = min(30.0, remaining_allocation)
        if neutral_score_assets:
            allocation_per_asset = min(
                10.0, tier2_allocation / len(neutral_score_assets)
            )
            for asset, _ in sorted_assets:
                if asset in neutral_score_assets:
                    target_allocations[asset] = allocation_per_asset
                    remaining_allocation -= allocation_per_asset

        # Tier 3: Poor performers (max 5% each)
        if negative_score_assets and remaining_allocation > 0:
            allocation_per_asset = min(
                5.0, remaining_allocation / len(negative_score_assets)
            )
            for asset, _ in sorted_assets:
                if asset in negative_score_assets:
                    target_allocations[asset] = allocation_per_asset
                    remaining_allocation -= allocation_per_asset

        # If we have remaining allocation, distribute evenly among all assets
        if remaining_allocation > 0:
            bonus_per_asset = remaining_allocation / len(sorted_assets)
            for asset, _ in sorted_assets:
                if asset in target_allocations:
                    target_allocations[asset] += bonus_per_asset

        # Ensure no single asset exceeds 25% (safety cap)
        for asset in target_allocations:
            if target_allocations[asset] > 25.0:
                excess = target_allocations[asset] - 25.0
                target_allocations[asset] = 25.0
                # Redistribute excess to USDT
                target_allocations["USDT"] += excess

        # Normalize to ensure total is 100%
        total = sum(target_allocations.values())
        if total > 0:
            for asset in target_allocations:
                target_allocations[asset] = target_allocations[asset] / total * 100

        return target_allocations

    def execute_rebalancing(self, target_allocations: Dict) -> bool:
        """Execute trades to reach target allocations"""
        portfolio = self.current_holdings
        total_portfolio_value = sum(data["usdt_value"] for data in portfolio.values())

        if total_portfolio_value < self.min_trade_value_usdt:
            self.logger.warning(
                f"Portfolio value too small: ${total_portfolio_value:.2f}"
            )
            return False

        trades_executed = []

        for asset, target_pct in target_allocations.items():
            if asset not in portfolio and asset != "USDT":
                continue

            current_pct = portfolio.get(asset, {}).get("allocation_pct", 0)
            target_value = total_portfolio_value * target_pct / 100
            current_value = portfolio.get(asset, {}).get("usdt_value", 0)

            difference_value = target_value - current_value
            difference_pct = abs(difference_value) / total_portfolio_value * 100

            # Only trade if difference is significant
            if difference_pct < self.rebalance_threshold:
                continue

            self.logger.info(
                f"{asset}: Current={current_pct:.1f}%, "
                f"Target={target_pct:.1f}%, "
                f"Difference=${difference_value:.2f}"
            )

            if abs(difference_value) > self.min_trade_value_usdt:
                if difference_value > 0:  # Need to buy
                    success = self.buy_asset(asset, difference_value)
                else:  # Need to sell
                    success = self.sell_asset(asset, abs(difference_value))

                if success:
                    trades_executed.append(
                        {
                            "asset": asset,
                            "action": "buy" if difference_value > 0 else "sell",
                            "value": abs(difference_value),
                        }
                    )

        if trades_executed:
            self.logger.info(f"Executed {len(trades_executed)} rebalancing trades")
            return True
        else:
            self.logger.info("No rebalancing trades needed")
            return False

    def buy_asset(self, asset: str, usdt_value: float) -> bool:
        """Buy asset with USDT"""
        try:
            if asset == "USDT":
                return True  # Already in USDT

            symbol = f"{asset}USDT"

            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])

            # Calculate quantity to buy
            quantity = usdt_value / price

            # Get symbol info for precision
            exchange_info = self.client.get_exchange_info()
            symbol_info = next(
                (s for s in exchange_info["symbols"] if s["symbol"] == symbol), None
            )

            if not symbol_info:
                self.logger.error(f"Symbol info not found for {symbol}")
                return False

            # Get quantity precision
            lot_size_filter = next(
                (f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE"),
                None,
            )
            if lot_size_filter:
                step_size = float(lot_size_filter["stepSize"])
                quantity = round(quantity / step_size) * step_size

            # Get minimum quantity
            min_qty = float(lot_size_filter["minQty"]) if lot_size_filter else 0
            if quantity < min_qty:
                self.logger.warning(
                    f"Quantity {quantity} below minimum {min_qty} for {symbol}"
                )
                return False

            # Check if we have enough USDT
            usdt_balance = self.current_holdings.get("USDT", {}).get("free", 0)
            if usdt_balance < usdt_value:
                self.logger.warning(
                    f"Insufficient USDT balance: {usdt_balance} < {usdt_value}"
                )
                return False

            # Execute buy order
            self.logger.info(f"Buying {quantity} {asset} for ~${usdt_value:.2f}")

            order = self.client.order_market_buy(
                symbol=symbol, quantity=f"{quantity:.8f}".rstrip("0").rstrip(".")
            )

            self.logger.info(f"Buy order executed: {order['orderId']}")
            return True

        except BinanceAPIException as e:
            self.logger.error(f"Binance API error buying {asset}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error buying {asset}: {e}")
            return False

    def sell_asset(self, asset: str, usdt_value: float) -> bool:
        """Sell asset for USDT"""
        try:
            if asset == "USDT":
                return True  # Already in USDT

            symbol = f"{asset}USDT"

            # Get current price
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])

            # Calculate quantity to sell
            quantity = usdt_value / price

            # Check available balance
            available_balance = self.current_holdings.get(asset, {}).get("free", 0)
            if quantity > available_balance:
                quantity = available_balance
                self.logger.warning(f"Selling all available {asset}: {quantity}")

            if quantity <= 0:
                self.logger.warning(f"No {asset} available to sell")
                return False

            # Get symbol info for precision
            exchange_info = self.client.get_exchange_info()
            symbol_info = next(
                (s for s in exchange_info["symbols"] if s["symbol"] == symbol), None
            )

            if not symbol_info:
                self.logger.error(f"Symbol info not found for {symbol}")
                return False

            # Get quantity precision
            lot_size_filter = next(
                (f for f in symbol_info["filters"] if f["filterType"] == "LOT_SIZE"),
                None,
            )
            if lot_size_filter:
                step_size = float(lot_size_filter["stepSize"])
                quantity = round(quantity / step_size) * step_size

            # Get minimum quantity
            min_qty = float(lot_size_filter["minQty"]) if lot_size_filter else 0
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

        except BinanceAPIException as e:
            self.logger.error(f"Binance API error selling {asset}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error selling {asset}: {e}")
            return False

    def run_trading_cycle(self):
        """Execute one complete trading cycle"""
        self.logger.info("=== Starting Trading Cycle ===")

        try:
            # 1. Analyze all assets
            analysis = self.analyze_all_assets()

            if not analysis:
                self.logger.warning("No analysis data available")
                return

            # 2. Calculate target allocations
            target_allocations = self.calculate_target_allocations(analysis)

            self.logger.info("Target Allocations:")
            for asset, pct in sorted(
                target_allocations.items(), key=lambda x: x[1], reverse=True
            ):
                current_pct = self.current_holdings.get(asset, {}).get(
                    "allocation_pct", 0
                )
                self.logger.info(f"{asset}: {current_pct:.1f}% → {pct:.1f}%")

            # 3. Execute rebalancing
            self.execute_rebalancing(target_allocations)

            # 4. Save analysis results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results = {
                "timestamp": timestamp,
                "analysis": analysis,
                "target_allocations": target_allocations,
                "current_holdings": self.current_holdings,
            }

            with open(f"multi_asset_analysis_{timestamp}.json", "w") as f:
                json.dump(results, f, indent=2, default=str)

            self.logger.info("=== Trading Cycle Complete ===")

        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")

    def run_continuous(self, cycle_minutes: int = 60):
        """Run continuous trading with specified cycle interval"""
        self.logger.info(
            f"Starting continuous multi-asset trading (cycle every {cycle_minutes} minutes)"
        )

        while True:
            try:
                self.run_trading_cycle()

                self.logger.info(f"Waiting {cycle_minutes} minutes until next cycle...")
                time.sleep(cycle_minutes * 60)

            except KeyboardInterrupt:
                self.logger.info("Trading stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in continuous trading: {e}")
                self.logger.info("Waiting 5 minutes before retry...")
                time.sleep(300)


def main():
    bot = MultiAssetTradingBot()

    print("Multi-Asset Portfolio Trading Bot")
    print("=================================")
    print("This bot will trade with ALL your assets, not just USDT")
    print("Current portfolio will be rebalanced based on momentum analysis")
    print()

    # Get current portfolio
    portfolio = bot.get_portfolio_balance()
    total_value = sum(data["usdt_value"] for data in portfolio.values())

    print(f"Current Portfolio (${total_value:.2f}):")
    for asset, data in sorted(
        portfolio.items(), key=lambda x: x[1]["usdt_value"], reverse=True
    ):
        print(f"  {asset}: ${data['usdt_value']:.2f} ({data['allocation_pct']:.1f}%)")

    print("\nTrading Mode Options:")
    print("1. Single analysis cycle (no trades)")
    print("2. Single rebalancing cycle (with trades)")
    print("3. Continuous trading (60 minute cycles)")
    print("4. Custom continuous trading")

    choice = input("\nSelect mode (1-4): ").strip()

    if choice == "1":
        print("\nRunning analysis only...")
        analysis = bot.analyze_all_assets()
        target_allocations = bot.calculate_target_allocations(analysis)

        print("\nRecommended Allocations:")
        for asset, pct in sorted(
            target_allocations.items(), key=lambda x: x[1], reverse=True
        ):
            current_pct = portfolio.get(asset, {}).get("allocation_pct", 0)
            print(f"  {asset}: {current_pct:.1f}% → {pct:.1f}%")

    elif choice == "2":
        confirm = input(
            "\nThis will execute real trades. Type 'CONFIRM LIVE TRADING' to proceed: "
        )
        if confirm == "CONFIRM LIVE TRADING":
            print("\nExecuting single rebalancing cycle...")
            bot.run_trading_cycle()
        else:
            print("Trading cancelled.")

    elif choice == "3":
        confirm = input(
            "\nThis will start continuous trading with real money. Type 'CONFIRM LIVE TRADING' to proceed: "
        )
        if confirm == "CONFIRM LIVE TRADING":
            print("\nStarting continuous trading (60 minute cycles)...")
            bot.run_continuous(60)
        else:
            print("Trading cancelled.")

    elif choice == "4":
        try:
            minutes = int(input("Enter cycle interval in minutes: "))
            confirm = input(
                f"\nThis will start continuous trading every {minutes} minutes. Type 'CONFIRM LIVE TRADING' to proceed: "
            )
            if confirm == "CONFIRM LIVE TRADING":
                print(f"\nStarting continuous trading ({minutes} minute cycles)...")
                bot.run_continuous(minutes)
            else:
                print("Trading cancelled.")
        except ValueError:
            print("Invalid interval.")

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
