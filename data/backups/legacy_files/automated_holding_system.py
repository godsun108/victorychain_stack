#!/usr/bin/env python3
"""
Automated Holding System - Smart Hold Strategy
Continuously monitors and holds profitable positions automatically
Only trades when exceptional opportunities arise
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import threading


class AutomatedHoldingSystem:
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
                    f'automated_holding_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Holding system parameters
        self.config = {
            "monitoring_interval": 900,  # 15 minutes
            "profit_threshold": 5.0,  # Hold if above 5% profit
            "extreme_profit_take": 50.0,  # Take profits at 50%+
            "stop_loss_threshold": -25.0,  # Stop loss at -25%
            "momentum_buy_threshold": 120.0,  # Buy if momentum score > 120 (more realistic)
            "max_new_position_pct": 0.1,  # Max 10% of portfolio in new position
            "exceptional_opportunity_score": 150.0,  # Exceptional opportunity threshold (lowered)
            "comprehensive_scan_interval": 18000,  # Full market scan every 5 hours
            "hold_duration_hours": 24,  # Hold winners for at least 24h
            "min_volume_threshold": 50000,  # Minimum 24h volume for trading
        }

        # State tracking
        self.running = False
        self.position_history = {}
        self.last_trades = {}
        self.holding_stats = {
            "positions_held": 0,
            "profits_taken": 0,
            "stops_triggered": 0,
            "opportunities_found": 0,
            "total_monitoring_cycles": 0,
        }

        # Comprehensive scanning state
        self.last_comprehensive_scan = datetime.now() - timedelta(
            hours=6
        )  # Force initial scan
        self.market_opportunities = []
        self.comprehensive_scan_results = {}

        self.logger.info("💎 Automated Holding System initialized")
        self.logger.info(f"⚙️ Config: {self.config}")
        self.logger.info(
            "🎯 Strategy: HOLD winners, PROTECT portfolio, FIND exceptional opportunities"
        )

    def get_portfolio_with_performance(self) -> Dict:
        """Get portfolio with detailed performance tracking"""
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
                        portfolio["USDT"] = {
                            "amount": total_amount,
                            "free": free,
                            "price": 1.0,
                            "usd_value": total_amount,
                            "daily_change": 0,
                            "weekly_change": 0,
                            "momentum_score": 0,
                            "hold_score": 100,  # Always hold USDT
                        }
                        total_value += total_amount
                    else:
                        try:
                            symbol = balance["asset"] + "USDT"

                            # Get current ticker
                            ticker = self.client.get_ticker(symbol=symbol)
                            price = float(ticker["lastPrice"])
                            daily_change = float(ticker["priceChangePercent"])
                            volume_24h = float(ticker["quoteVolume"])
                            usd_value = total_amount * price

                            if usd_value > 0.5:
                                # Get weekly performance
                                weekly_change = self.get_weekly_performance(symbol)

                                # Calculate hold score
                                hold_score = self.calculate_hold_score(
                                    daily_change,
                                    weekly_change,
                                    volume_24h,
                                    usd_value,
                                    total_value,
                                )

                                portfolio[balance["asset"]] = {
                                    "amount": total_amount,
                                    "free": free,
                                    "price": price,
                                    "usd_value": usd_value,
                                    "daily_change": daily_change,
                                    "weekly_change": weekly_change,
                                    "volume_24h": volume_24h,
                                    "hold_score": hold_score,
                                    "momentum_score": self.get_momentum_score(symbol),
                                }
                                total_value += usd_value
                        except Exception as e:
                            self.logger.warning(
                                f"Could not analyze {balance['asset']}: {e}"
                            )
                            continue

            return {
                "positions": portfolio,
                "total_value": total_value,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            return {"positions": {}, "total_value": 0, "timestamp": datetime.now()}

    def get_weekly_performance(self, symbol: str) -> float:
        """Get 7-day performance for a symbol"""
        try:
            klines = self.client.get_klines(symbol=symbol, interval="1d", limit=8)
            if len(klines) >= 8:
                week_ago_price = float(klines[0][1])  # Open price 7 days ago
                current_price = float(klines[-1][4])  # Latest close price
                return ((current_price - week_ago_price) / week_ago_price) * 100
            return 0
        except:
            return 0

    def calculate_hold_score(
        self,
        daily_change: float,
        weekly_change: float,
        volume: float,
        position_value: float,
        total_portfolio: float,
    ) -> float:
        """Calculate hold score (0-100, higher = stronger hold)"""

        score = 50  # Base score

        # Profit factor (strong positive influence)
        if daily_change > 0:
            score += min(daily_change * 2, 30)  # Up to +30 for daily gains
        else:
            score += max(daily_change * 1.5, -25)  # Down to -25 for daily losses

        # Weekly trend factor
        if weekly_change > 0:
            score += min(weekly_change * 1.5, 25)  # Up to +25 for weekly gains
        else:
            score += max(weekly_change * 1, -20)  # Down to -20 for weekly losses

        # Position size factor (larger positions get slight hold bias)
        position_pct = (position_value / total_portfolio) * 100
        if position_pct > 50:  # Major position
            score += 10
        elif position_pct > 20:  # Significant position
            score += 5

        # Volume factor (liquidity consideration)
        if volume > 100000:
            score += 5  # High volume = easier to trade later
        elif volume < 10000:
            score -= 5  # Low volume = harder to exit

        # Extreme conditions
        if daily_change > self.config["extreme_profit_take"]:
            score -= 30  # Take profits on extreme gains
        elif daily_change < self.config["stop_loss_threshold"]:
            score -= 50  # Strong sell signal on major losses

        return max(0, min(100, score))

    def get_momentum_score(self, symbol: str) -> float:
        """Get momentum score for potential opportunities"""
        try:
            # Get recent data
            klines = self.client.get_klines(symbol=symbol, interval="1h", limit=48)
            if not klines:
                return 0

            # Calculate momentum indicators
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]

            # Price momentum
            price_momentum = ((closes[-1] - closes[-24]) / closes[-24]) * 100

            # Volume momentum
            recent_volume = sum(volumes[-12:]) / 12
            older_volume = sum(volumes[-24:-12]) / 12
            volume_momentum = (
                ((recent_volume - older_volume) / older_volume) * 100
                if older_volume > 0
                else 0
            )

            # Volatility
            price_changes = [
                (closes[i] - closes[i - 1]) / closes[i - 1]
                for i in range(1, len(closes))
            ]
            volatility = np.std(price_changes) * 100

            # Combined score
            momentum_score = (
                price_momentum * 0.5 + volume_momentum * 0.3 + volatility * 0.2
            )

            return momentum_score

        except:
            return 0

    def make_holding_decisions(self, portfolio_data: Dict) -> Dict:
        """Make holding decisions for all positions"""
        decisions = {}
        portfolio = portfolio_data["positions"]

        for asset, data in portfolio.items():
            if asset == "USDT":
                continue

            hold_score = data["hold_score"]
            daily_change = data["daily_change"]
            weekly_change = data["weekly_change"]
            usd_value = data["usd_value"]

            # Decision logic
            if hold_score >= 70:
                decision = "STRONG_HOLD"
                reason = f"Strong hold signal (score: {hold_score:.0f})"
                action = None
            elif hold_score >= 50:
                decision = "HOLD"
                reason = f"Hold position (score: {hold_score:.0f})"
                action = None
            elif hold_score >= 30:
                decision = "MONITOR"
                reason = f"Monitor closely (score: {hold_score:.0f})"
                action = None
            else:
                decision = "CONSIDER_SELL"
                reason = f"Weak hold signal (score: {hold_score:.0f})"
                action = "evaluate_sell"

            # Override for extreme conditions
            if daily_change >= self.config["extreme_profit_take"]:
                decision = "TAKE_PROFITS"
                reason = f"Extreme profits: {daily_change:+.1f}%"
                action = "sell_partial"
            elif daily_change <= self.config["stop_loss_threshold"]:
                decision = "STOP_LOSS"
                reason = f"Stop loss triggered: {daily_change:+.1f}%"
                action = "sell_major"

            decisions[asset] = {
                "decision": decision,
                "reason": reason,
                "action": action,
                "hold_score": hold_score,
                "daily_change": daily_change,
                "weekly_change": weekly_change,
                "usd_value": usd_value,
            }

        return decisions

    def find_exceptional_opportunities(self) -> List[Dict]:
        """Find only exceptional momentum opportunities"""
        try:
            self.logger.info("🔍 Scanning for EXCEPTIONAL opportunities...")

            # Get top volume tokens
            tickers = self.client.get_ticker()
            high_volume_tokens = []

            for ticker in tickers:
                if ticker["symbol"].endswith("USDT") and ticker["symbol"] != "USDCUSDT":
                    try:
                        volume = float(ticker["quoteVolume"])
                        if volume > 50000:  # Only high-volume tokens
                            high_volume_tokens.append(ticker["symbol"])
                    except:
                        continue

            # Sort by volume and take top 50
            volume_data = [
                (
                    symbol,
                    float(
                        next(t["quoteVolume"] for t in tickers if t["symbol"] == symbol)
                    ),
                )
                for symbol in high_volume_tokens
            ]
            volume_data.sort(key=lambda x: x[1], reverse=True)
            top_symbols = [symbol for symbol, _ in volume_data[:50]]

            exceptional_opportunities = []

            for symbol in top_symbols:
                try:
                    momentum_score = self.get_momentum_score(symbol)

                    # Only consider exceptional scores
                    if momentum_score >= self.config["exceptional_opportunity_score"]:
                        ticker_data = next(t for t in tickers if t["symbol"] == symbol)

                        exceptional_opportunities.append(
                            {
                                "symbol": symbol,
                                "token": symbol.replace("USDT", ""),
                                "momentum_score": momentum_score,
                                "daily_change": float(
                                    ticker_data["priceChangePercent"]
                                ),
                                "volume_24h": float(ticker_data["quoteVolume"]),
                                "price": float(ticker_data["lastPrice"]),
                            }
                        )

                except Exception as e:
                    continue

                time.sleep(0.1)  # Rate limiting

            exceptional_opportunities.sort(
                key=lambda x: x["momentum_score"], reverse=True
            )

            if exceptional_opportunities:
                self.logger.info(
                    f"🎯 Found {len(exceptional_opportunities)} EXCEPTIONAL opportunities!"
                )
            else:
                self.logger.info(
                    "📊 No exceptional opportunities found - continuing to HOLD"
                )

            return exceptional_opportunities[:5]  # Top 5 only

        except Exception as e:
            self.logger.error(f"Error finding opportunities: {e}")
            return []

    def execute_automated_action(
        self, asset: str, action: str, position_data: Dict
    ) -> bool:
        """Execute automated trading action"""
        try:
            symbol = asset + "USDT"

            if action == "sell_partial":
                # Sell 30% of position
                sell_percentage = 0.3
                sell_amount = position_data["amount"] * sell_percentage
                formatted_qty = self.format_quantity(sell_amount, symbol)

                self.logger.info(
                    f"🔥 AUTO PROFIT-TAKING: Selling {sell_percentage*100}% of {asset}"
                )
                self.logger.info(
                    f"   Raw amount: {sell_amount:.8f}, Formatted: {formatted_qty:.8f}"
                )

                order = self.client.order_market_sell(
                    symbol=symbol, quantity=formatted_qty
                )

                self.logger.info(
                    f"✅ Sold {formatted_qty:.8f} {asset} - Order: {order['orderId']}"
                )
                self.holding_stats["profits_taken"] += 1
                return True

            elif action == "sell_major":
                # Sell 80% of position
                sell_percentage = 0.8
                sell_amount = position_data["amount"] * sell_percentage
                formatted_qty = self.format_quantity(sell_amount, symbol)

                self.logger.info(
                    f"🛑 AUTO STOP-LOSS: Selling {sell_percentage*100}% of {asset}"
                )
                self.logger.info(
                    f"   Raw amount: {sell_amount:.8f}, Formatted: {formatted_qty:.8f}"
                )

                order = self.client.order_market_sell(
                    symbol=symbol, quantity=formatted_qty
                )

                self.logger.info(
                    f"✅ Sold {formatted_qty:.8f} {asset} - Order: {order['orderId']}"
                )
                self.holding_stats["stops_triggered"] += 1
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error executing {action} for {asset}: {e}")
            return False

    def get_lot_size_precision(self, symbol: str) -> Dict:
        """Get LOT_SIZE filter information for precise quantity formatting"""
        try:
            info = self.client.get_symbol_info(symbol)
            for f in info["filters"]:
                if f["filterType"] == "LOT_SIZE":
                    return {
                        "minQty": float(f["minQty"]),
                        "maxQty": float(f["maxQty"]),
                        "stepSize": float(f["stepSize"]),
                    }
            return {"minQty": 0.00000001, "maxQty": 1000000000, "stepSize": 0.00000001}
        except:
            return {"minQty": 0.00000001, "maxQty": 1000000000, "stepSize": 0.00000001}

    def format_quantity(self, quantity: float, symbol: str) -> float:
        """Format quantity according to LOT_SIZE requirements"""
        lot_info = self.get_lot_size_precision(symbol)
        step_size = lot_info["stepSize"]
        min_qty = lot_info["minQty"]

        # Round to step size precision
        if step_size >= 1:
            # For step sizes like 0.1, 1.0, etc.
            precision = 0
            while step_size < 1:
                step_size *= 10
                precision += 1
            formatted_qty = (
                round(quantity / lot_info["stepSize"]) * lot_info["stepSize"]
            )
            formatted_qty = round(formatted_qty, precision)
        else:
            # For very small step sizes
            precision = len(str(step_size).split(".")[-1])
            formatted_qty = (
                round(quantity / lot_info["stepSize"]) * lot_info["stepSize"]
            )
            formatted_qty = round(formatted_qty, precision)

        # Ensure minimum quantity
        if formatted_qty < min_qty:
            formatted_qty = min_qty

        return formatted_qty

    def run_holding_cycle(self):
        """Execute one automated holding cycle"""
        try:
            self.logger.info("💎 Running automated holding cycle...")

            # Get portfolio with performance
            portfolio_data = self.get_portfolio_with_performance()
            portfolio = portfolio_data["positions"]
            total_value = portfolio_data["total_value"]

            self.logger.info(f"💼 Portfolio value: ${total_value:.2f}")

            # Make holding decisions
            holding_decisions = self.make_holding_decisions(portfolio_data)

            # Log holding status
            hold_count = 0
            for asset, decision in holding_decisions.items():
                status_emoji = {
                    "STRONG_HOLD": "💎",
                    "HOLD": "🟢",
                    "MONITOR": "🟡",
                    "CONSIDER_SELL": "🟠",
                    "TAKE_PROFITS": "🔥",
                    "STOP_LOSS": "🛑",
                }.get(decision["decision"], "📊")

                self.logger.info(
                    f"{status_emoji} {asset}: {decision['decision']} - {decision['reason']}"
                )

                if decision["decision"] in ["STRONG_HOLD", "HOLD"]:
                    hold_count += 1
                    self.holding_stats["positions_held"] += 1

                # Execute automated actions if needed
                if decision["action"]:
                    self.execute_automated_action(
                        asset, decision["action"], portfolio[asset]
                    )

            self.logger.info(
                f"💎 Holding {hold_count}/{len(holding_decisions)} positions"
            )

            # Check for exceptional opportunities (only if we have USDT)
            usdt_available = portfolio.get("USDT", {}).get("amount", 0)

            if usdt_available > 20:  # Only if we have meaningful USDT
                exceptional_opportunities = self.find_exceptional_opportunities()

                if exceptional_opportunities:
                    best_opportunity = exceptional_opportunities[0]
                    max_buy_amount = min(
                        usdt_available * 0.8,  # Use 80% of USDT
                        total_value
                        * self.config["max_new_position_pct"],  # Max 10% of portfolio
                    )

                    if max_buy_amount >= 20:
                        self.logger.info(
                            f"🎯 EXCEPTIONAL OPPORTUNITY: {best_opportunity['token']}"
                        )
                        self.logger.info(
                            f"📊 Momentum Score: {best_opportunity['momentum_score']:.1f}"
                        )
                        self.logger.info(f"💰 Auto-buying with ${max_buy_amount:.2f}")

                        try:
                            order = self.client.order_market_buy(
                                symbol=best_opportunity["symbol"],
                                quoteOrderQty=round(max_buy_amount, 2),
                            )

                            self.logger.info(
                                f"✅ EXCEPTIONAL BUY executed! Order: {order['orderId']}"
                            )
                            self.holding_stats["opportunities_found"] += 1

                        except Exception as e:
                            self.logger.error(
                                f"Failed to buy {best_opportunity['token']}: {e}"
                            )

            # Update stats
            self.holding_stats["total_monitoring_cycles"] += 1

            # Save state
            self.save_holding_state()

            self.logger.info("💎 Holding cycle completed")

        except Exception as e:
            self.logger.error(f"Error in holding cycle: {e}")

    def save_holding_state(self):
        """Save current holding state"""
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "config": self.config,
                "holding_stats": self.holding_stats,
                "last_portfolio_value": getattr(self, "last_portfolio_value", 0),
            }

            filename = (
                f"automated_holding_state_{datetime.now().strftime('%Y%m%d')}.json"
            )
            with open(filename, "w") as f:
                json.dump(state, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving state: {e}")

    def start_automated_holding(self):
        """Start the automated holding system"""
        self.running = True
        self.logger.info("💎 AUTOMATED HOLDING SYSTEM STARTED!")
        self.logger.info(
            f"⏰ Monitoring every {self.config['monitoring_interval']} seconds"
        )
        self.logger.info(
            "🎯 Strategy: HOLD winners, PROTECT positions, FIND exceptional opportunities"
        )

        try:
            while self.running:
                self.run_holding_cycle()

                self.logger.info(
                    f"😴 Next cycle in {self.config['monitoring_interval']} seconds..."
                )
                time.sleep(self.config["monitoring_interval"])

        except KeyboardInterrupt:
            self.logger.info("🛑 Manual stop requested")
        except Exception as e:
            self.logger.error(f"Automated holding error: {e}")
        finally:
            self.running = False
            self.logger.info("🏁 Automated holding system stopped")

            # Final stats
            self.logger.info("📊 FINAL STATISTICS:")
            self.logger.info(
                f"  Monitoring cycles: {self.holding_stats['total_monitoring_cycles']}"
            )
            self.logger.info(
                f"  Positions held: {self.holding_stats['positions_held']}"
            )
            self.logger.info(f"  Profits taken: {self.holding_stats['profits_taken']}")
            self.logger.info(
                f"  Stops triggered: {self.holding_stats['stops_triggered']}"
            )
            self.logger.info(
                f"  Opportunities found: {self.holding_stats['opportunities_found']}"
            )

    def run_comprehensive_market_scan(self) -> Dict:
        """Run comprehensive market scan every 5 hours"""
        try:
            self.logger.info("🔍 Running COMPREHENSIVE 5-hour market scan...")

            # Import the enhanced analyzer
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "enhanced_analyzer", "enhanced_momentum_analyzer.py"
            )
            enhanced_analyzer = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(enhanced_analyzer)

            # Create analyzer instance
            analyzer = enhanced_analyzer.EnhancedMomentumAnalyzer()

            # Get comprehensive market data
            market_data = analyzer.get_comprehensive_market_data()
            portfolio_data = analyzer.get_current_portfolio()
            insights = analyzer.generate_ai_style_insights(market_data, portfolio_data)

            # Log key insights
            overview = insights["market_overview"]
            self.logger.info(
                f"📊 Market Sentiment: {overview['sentiment']} (Strength: {overview['strength']:.0f}/100)"
            )
            self.logger.info(f"🎯 Risk Level: {overview['risk_level']}")
            self.logger.info(f"💡 Key Insight: {overview['key_observation']}")

            # Log top opportunities
            top_opportunities = insights["top_opportunities"][:3]
            for i, opp in enumerate(top_opportunities, 1):
                self.logger.info(
                    f"🔥 Top Opportunity #{i}: {opp['token']} (Score: {opp['opportunity_score']:.0f})"
                )

            # Update system state with market insights
            self.comprehensive_scan_results = {
                "timestamp": datetime.now(),
                "market_data": market_data,
                "insights": insights,
                "buy_candidates": insights["trading_recommendations"]["buy"],
                "hold_recommendations": insights["trading_recommendations"]["hold"],
                "market_strength": overview["strength"],
                "risk_level": overview["risk_level"],
            }

            # Save scan results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_scan_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(self.comprehensive_scan_results, f, indent=2, default=str)

            self.logger.info(f"💾 Comprehensive scan saved: {filename}")

            return self.comprehensive_scan_results

        except Exception as e:
            self.logger.error(f"Error in comprehensive market scan: {e}")
            return {}

    def should_run_comprehensive_scan(self) -> bool:
        """Check if it's time for comprehensive market scan"""
        time_since_last = datetime.now() - self.last_comprehensive_scan
        return (
            time_since_last.total_seconds()
            >= self.config["comprehensive_scan_interval"]
        )

    def find_exceptional_opportunities_enhanced(self) -> List[Dict]:
        """Enhanced opportunity finding using comprehensive market data"""
        try:
            # Use recent comprehensive scan if available
            if (
                self.comprehensive_scan_results
                and (
                    datetime.now()
                    - self.comprehensive_scan_results.get(
                        "timestamp", datetime.now() - timedelta(hours=6)
                    )
                ).total_seconds()
                < 3600
            ):

                self.logger.info("🎯 Using recent comprehensive scan data...")

                # Get buy candidates from AI analysis
                buy_candidates = self.comprehensive_scan_results.get(
                    "buy_candidates", []
                )
                market_strength = self.comprehensive_scan_results.get(
                    "market_strength", 50
                )

                exceptional_opportunities = []

                for candidate in buy_candidates[:5]:  # Top 5 candidates
                    token = candidate["token"]
                    symbol = token + "USDT"

                    try:
                        # Get current ticker data
                        ticker = self.client.get_ticker(symbol=symbol)

                        opportunity = {
                            "symbol": symbol,
                            "token": token,
                            "momentum_score": candidate.get("momentum_score", 0),
                            "opportunity_score": candidate.get("opportunity_score", 0),
                            "daily_change": float(ticker["priceChangePercent"]),
                            "volume_24h": float(ticker["quoteVolume"]),
                            "price": float(ticker["lastPrice"]),
                            "ai_recommended": True,
                            "market_strength": market_strength,
                        }

                        # Only include if meets minimum criteria
                        if (
                            opportunity["volume_24h"]
                            > self.config["min_volume_threshold"]
                            and opportunity["daily_change"] > -5
                        ):  # Not heavily down
                            exceptional_opportunities.append(opportunity)

                    except Exception as e:
                        self.logger.warning(f"Error getting data for {token}: {e}")
                        continue

                if exceptional_opportunities:
                    self.logger.info(
                        f"🎯 Found {len(exceptional_opportunities)} AI-recommended opportunities!"
                    )
                else:
                    self.logger.info("📊 No AI-recommended opportunities meet criteria")

                return exceptional_opportunities

            else:
                # Fall back to original method
                return self.find_exceptional_opportunities()

        except Exception as e:
            self.logger.error(f"Error in enhanced opportunity finding: {e}")
            return []

    # ...existing code...


def main():
    """Main automated holding function"""
    holding_system = AutomatedHoldingSystem()

    print("💎 AUTOMATED HOLDING SYSTEM")
    print("=" * 50)
    print("🎯 SMART HOLDING STRATEGY:")
    print("• HOLD all profitable positions")
    print("• MONITOR portfolio health 24/7")
    print("• PROTECT against major losses")
    print("• FIND exceptional opportunities (score > 300)")
    print("• AUTO profit-taking at +50%")
    print("• AUTO stop-loss at -25%")
    print(f"• CHECK every {holding_system.config['monitoring_interval']//60} minutes")
    print()
    print("🚀 This system will run continuously and make smart holding decisions!")
    print("💎 Your current winners will be protected and held!")
    print()

    confirm = input("💎 Type 'START AUTOMATED HOLDING' to begin: ")
    if confirm != "START AUTOMATED HOLDING":
        print("❌ Automated holding cancelled")
        return

    print("\n🔥 Starting automated holding system...")
    print("Press Ctrl+C to stop")
    print()

    holding_system.start_automated_holding()


if __name__ == "__main__":
    main()
