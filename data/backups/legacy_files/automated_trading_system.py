#!/usr/bin/env python3
"""
Automated Trading System - Follow and Trade Automatically
Monitors portfolio, follows trends, and executes trades automatically
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv


class AutomatedTradingSystem:
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
                    f'automated_trading_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Trading parameters
        self.config = {
            "monitoring_interval": 300,  # 5 minutes
            "profit_target": 10.0,  # 10% profit target
            "stop_loss": -5.0,  # 5% stop loss
            "trend_follow_threshold": 5.0,  # Follow trends > 5%
            "min_trade_amount": 10.0,  # Minimum $10 trades
            "max_portfolio_allocation": 0.8,  # Max 80% in one asset
            "rebalance_threshold": 15.0,  # Rebalance if imbalance > 15%
        }

        # State tracking
        self.running = False
        self.last_portfolio = {}
        self.trade_history = []
        self.performance_metrics = {}

        self.logger.info("🤖 Automated Trading System initialized")
        self.logger.info(f"⚙️ Config: {self.config}")

    def get_portfolio_snapshot(self) -> Dict:
        """Get current portfolio snapshot"""
        try:
            account = self.client.get_account()
            portfolio = {}
            total_value = 0

            for balance in account["balances"]:
                free = float(balance["free"])
                locked = float(balance["locked"])
                total_amount = free + locked

                if total_amount > 0.01:
                    if balance["asset"] == "USDT":
                        usd_value = total_amount
                        portfolio[balance["asset"]] = {
                            "amount": total_amount,
                            "free": free,
                            "locked": locked,
                            "price": 1.0,
                            "usd_value": usd_value,
                        }
                        total_value += usd_value
                    else:
                        try:
                            ticker = self.client.get_symbol_ticker(
                                symbol=balance["asset"] + "USDT"
                            )
                            price = float(ticker["price"])
                            usd_value = total_amount * price

                            if usd_value > 0.5:
                                portfolio[balance["asset"]] = {
                                    "amount": total_amount,
                                    "free": free,
                                    "locked": locked,
                                    "price": price,
                                    "usd_value": usd_value,
                                }
                                total_value += usd_value
                        except:
                            continue

            return {
                "portfolio": portfolio,
                "total_value": total_value,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            return {"portfolio": {}, "total_value": 0, "timestamp": datetime.now()}

    def analyze_market_trends(self) -> Dict:
        """Analyze market trends for key assets"""
        try:
            # Get trending tokens
            tickers = self.client.get_ticker()

            # Filter USDT pairs and analyze
            usdt_pairs = []
            for ticker in tickers:
                if ticker["symbol"].endswith("USDT") and ticker["symbol"] != "USDCUSDT":
                    try:
                        volume = float(ticker["quoteVolume"])
                        change = float(ticker["priceChangePercent"])
                        price = float(ticker["lastPrice"])

                        if volume > 1000:  # Only liquid assets
                            usdt_pairs.append(
                                {
                                    "symbol": ticker["symbol"],
                                    "price": price,
                                    "change_24h": change,
                                    "volume": volume,
                                    "trend_score": abs(change)
                                    + (volume / 100000),  # Combined score
                                }
                            )
                    except:
                        continue

            # Sort by trend score
            usdt_pairs.sort(key=lambda x: x["trend_score"], reverse=True)

            # Categorize trends
            hot_trends = [p for p in usdt_pairs[:20] if p["change_24h"] > 5]
            cold_trends = [p for p in usdt_pairs if p["change_24h"] < -5]

            return {
                "hot_trends": hot_trends[:10],
                "cold_trends": cold_trends[:10],
                "top_movers": usdt_pairs[:20],
                "analysis_time": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return {"hot_trends": [], "cold_trends": [], "top_movers": []}

    def execute_trade(
        self, action: str, asset: str, amount: float, trade_type: str = "market"
    ) -> Optional[Dict]:
        """Execute a trade"""
        try:
            symbol = asset + "USDT" if asset != "USDT" else None

            if not symbol:
                return None

            if amount < self.config["min_trade_amount"]:
                self.logger.warning(f"Trade amount ${amount:.2f} below minimum")
                return None

            self.logger.info(f"🔄 EXECUTING {action.upper()}: {asset} ${amount:.2f}")

            if action.lower() == "buy":
                order = self.client.order_market_buy(
                    symbol=symbol,
                    quoteOrderQty=round(
                        amount * 0.99, 2
                    ),  # 99% to avoid precision issues
                )
            elif action.lower() == "sell":
                # Get current holdings
                account = self.client.get_account()
                asset_balance = 0

                for balance in account["balances"]:
                    if balance["asset"] == asset:
                        asset_balance = float(balance["free"])
                        break

                if asset_balance <= 0:
                    self.logger.warning(f"No {asset} balance to sell")
                    return None

                # Calculate sell quantity
                current_price = self.get_current_price(symbol)
                sell_quantity = min(asset_balance, amount / current_price)

                # Round to proper precision
                sell_quantity = round(sell_quantity, 8)

                order = self.client.order_market_sell(
                    symbol=symbol, quantity=sell_quantity
                )
            else:
                self.logger.error(f"Unknown action: {action}")
                return None

            self.logger.info(
                f"✅ {action.upper()} executed! Order ID: {order['orderId']}"
            )

            # Record trade
            trade_record = {
                "timestamp": datetime.now().isoformat(),
                "action": action,
                "asset": asset,
                "amount": amount,
                "order": order,
                "trade_type": trade_type,
            }

            self.trade_history.append(trade_record)
            return trade_record

        except Exception as e:
            self.logger.error(f"Error executing {action} for {asset}: {e}")
            return None

    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker["price"])
        except:
            return 0.0

    def check_profit_loss_targets(self, portfolio: Dict) -> List[Dict]:
        """Check if any positions hit profit/loss targets"""
        actions = []

        try:
            for asset, data in portfolio.items():
                if (
                    asset == "USDT"
                    or data["usd_value"] < self.config["min_trade_amount"]
                ):
                    continue

                # Get recent performance
                symbol = asset + "USDT"
                try:
                    ticker = self.client.get_ticker(symbol=symbol)
                    change_24h = float(ticker["priceChangePercent"])

                    # Profit target hit
                    if change_24h >= self.config["profit_target"]:
                        actions.append(
                            {
                                "action": "sell",
                                "asset": asset,
                                "amount": data["usd_value"] * 0.5,  # Sell 50%
                                "reason": f"Profit target hit: {change_24h:+.2f}%",
                                "priority": "high",
                            }
                        )

                    # Stop loss hit
                    elif change_24h <= self.config["stop_loss"]:
                        actions.append(
                            {
                                "action": "sell",
                                "asset": asset,
                                "amount": data["usd_value"] * 0.8,  # Sell 80%
                                "reason": f"Stop loss triggered: {change_24h:+.2f}%",
                                "priority": "urgent",
                            }
                        )

                except:
                    continue

            return actions

        except Exception as e:
            self.logger.error(f"Error checking P&L targets: {e}")
            return []

    def follow_trends(self, portfolio: Dict, market_trends: Dict) -> List[Dict]:
        """Generate trend-following actions"""
        actions = []

        try:
            hot_trends = market_trends.get("hot_trends", [])
            portfolio_assets = set(portfolio.keys())

            # Available USDT for trades
            usdt_available = portfolio.get("USDT", {}).get("usd_value", 0)

            if usdt_available < self.config["min_trade_amount"]:
                return actions

            # Follow hot trends not in portfolio
            for trend in hot_trends[:5]:  # Top 5 hot trends
                asset = trend["symbol"].replace("USDT", "")

                if (
                    asset not in portfolio_assets
                    and trend["change_24h"] >= self.config["trend_follow_threshold"]
                    and trend["volume"] > 10000
                ):

                    # Calculate position size (5-10% of available USDT)
                    position_size = min(
                        usdt_available * 0.1,  # 10% max
                        usdt_available
                        * (trend["change_24h"] / 100),  # Proportional to trend
                    )

                    if position_size >= self.config["min_trade_amount"]:
                        actions.append(
                            {
                                "action": "buy",
                                "asset": asset,
                                "amount": position_size,
                                "reason": f'Following hot trend: {trend["change_24h"]:+.2f}%',
                                "priority": "medium",
                            }
                        )
                        usdt_available -= position_size

            return actions

        except Exception as e:
            self.logger.error(f"Error following trends: {e}")
            return []

    def rebalance_portfolio(self, portfolio: Dict) -> List[Dict]:
        """Rebalance portfolio if needed"""
        actions = []

        try:
            total_value = sum(data["usd_value"] for data in portfolio.values())

            # Check for over-allocation
            for asset, data in portfolio.items():
                if asset == "USDT":
                    continue

                allocation_pct = (data["usd_value"] / total_value) * 100

                # If over-allocated, sell some
                if allocation_pct > self.config["max_portfolio_allocation"] * 100:
                    excess_amount = data["usd_value"] - (
                        total_value * self.config["max_portfolio_allocation"]
                    )

                    if excess_amount > self.config["min_trade_amount"]:
                        actions.append(
                            {
                                "action": "sell",
                                "asset": asset,
                                "amount": excess_amount,
                                "reason": f"Rebalancing: {allocation_pct:.1f}% allocation too high",
                                "priority": "low",
                            }
                        )

            return actions

        except Exception as e:
            self.logger.error(f"Error rebalancing: {e}")
            return []

    def execute_automated_cycle(self):
        """Execute one automated trading cycle"""
        try:
            self.logger.info("🔄 Starting automated trading cycle...")

            # Get current portfolio
            portfolio_data = self.get_portfolio_snapshot()
            portfolio = portfolio_data["portfolio"]
            total_value = portfolio_data["total_value"]

            self.logger.info(f"💼 Portfolio value: ${total_value:.2f}")

            # Analyze market trends
            market_trends = self.analyze_market_trends()

            # Generate trading actions
            all_actions = []

            # 1. Check profit/loss targets
            pl_actions = self.check_profit_loss_targets(portfolio)
            all_actions.extend(pl_actions)

            # 2. Follow trends
            trend_actions = self.follow_trends(portfolio, market_trends)
            all_actions.extend(trend_actions)

            # 3. Rebalance if needed
            rebalance_actions = self.rebalance_portfolio(portfolio)
            all_actions.extend(rebalance_actions)

            # Sort actions by priority
            priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
            all_actions.sort(key=lambda x: priority_order.get(x["priority"], 4))

            # Execute actions
            executed_trades = []
            for action in all_actions[:5]:  # Limit to 5 actions per cycle
                self.logger.info(f"🎯 {action['reason']}")

                trade_result = self.execute_trade(
                    action["action"], action["asset"], action["amount"]
                )

                if trade_result:
                    executed_trades.append(trade_result)
                    time.sleep(1)  # Rate limiting

            # Log cycle summary
            self.logger.info(
                f"📊 Cycle complete: {len(executed_trades)} trades executed"
            )

            # Update performance metrics
            self.performance_metrics[datetime.now().isoformat()] = {
                "portfolio_value": total_value,
                "trades_executed": len(executed_trades),
                "actions_considered": len(all_actions),
            }

            # Save state
            self.save_trading_state()

        except Exception as e:
            self.logger.error(f"Error in automated cycle: {e}")

    def save_trading_state(self):
        """Save current trading state"""
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "config": self.config,
                "trade_history": self.trade_history[-50:],  # Last 50 trades
                "performance_metrics": self.performance_metrics,
            }

            filename = (
                f"automated_trading_state_{datetime.now().strftime('%Y%m%d')}.json"
            )
            with open(filename, "w") as f:
                json.dump(state, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

    def start_automated_trading(self):
        """Start the automated trading system"""
        self.running = True
        self.logger.info("🚀 AUTOMATED TRADING SYSTEM STARTED!")
        self.logger.info(
            f"⏰ Monitoring every {self.config['monitoring_interval']} seconds"
        )

        try:
            while self.running:
                self.execute_automated_cycle()

                self.logger.info(
                    f"😴 Sleeping for {self.config['monitoring_interval']} seconds..."
                )
                time.sleep(self.config["monitoring_interval"])

        except KeyboardInterrupt:
            self.logger.info("🛑 Manual stop requested")
        except Exception as e:
            self.logger.error(f"Automated trading error: {e}")
        finally:
            self.running = False
            self.logger.info("🏁 Automated trading stopped")

    def stop_automated_trading(self):
        """Stop the automated trading system"""
        self.running = False
        self.logger.info("🛑 Stop signal sent to automated trading system")


def main():
    """Main automated trading function"""
    trader = AutomatedTradingSystem()

    print("🤖 AUTOMATED TRADING SYSTEM")
    print("=" * 50)
    print("This system will:")
    print("• Monitor your portfolio every 5 minutes")
    print("• Execute profit-taking at +10%")
    print("• Stop-loss at -5%")
    print("• Follow hot market trends")
    print("• Rebalance when needed")
    print("• Trade automatically 24/7")
    print()

    confirm = input("🚀 Type 'START AUTOMATED TRADING' to begin: ")
    if confirm != "START AUTOMATED TRADING":
        print("❌ Automated trading cancelled")
        return

    print("\n🔥 Starting automated trading system...")
    print("Press Ctrl+C to stop")
    print()

    trader.start_automated_trading()


if __name__ == "__main__":
    main()
