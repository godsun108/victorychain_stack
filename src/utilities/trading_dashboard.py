#!/usr/bin/env python3
"""
VictoryChain Trading Performance Dashboard
Real-time monitoring and analytics for all trading strategies
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
from dotenv import load_dotenv

# Optional visualization imports - install with: pip install matplotlib seaborn
try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    VISUALIZATION_AVAILABLE = True
except ImportError:
    plt = None
    sns = None
    VISUALIZATION_AVAILABLE = False
from collections import defaultdict


class TradingDashboard:
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
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        # Performance tracking
        self.performance_history = []
        self.trade_history = []
        self.strategy_metrics = defaultdict(
            lambda: {
                "total_trades": 0,
                "winning_trades": 0,
                "total_profit_usd": 0.0,
                "max_drawdown": 0.0,
                "avg_hold_time": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "sharpe_ratio": 0.0,
            }
        )

    def get_current_portfolio(self) -> Dict:
        """Get current portfolio status"""
        try:
            account = self.client.get_account()

            total_value = 0
            usdt_balance = 0
            assets = {}

            for balance in account["balances"]:
                if float(balance["free"]) > 0 or float(balance["locked"]) > 0:
                    symbol = balance["asset"]
                    free = float(balance["free"])
                    locked = float(balance["locked"])
                    total = free + locked

                    if symbol == "USDT":
                        value = total
                        usdt_balance = total
                    else:
                        try:
                            ticker = self.client.get_symbol_ticker(
                                symbol=f"{symbol}USDT"
                            )
                            price = float(ticker["price"])
                            value = total * price
                        except:
                            value = 0

                    if value > 0.01:
                        assets[symbol] = {
                            "free": free,
                            "locked": locked,
                            "total": total,
                            "value": value,
                            "percentage": 0,  # Will calculate after total
                        }
                        total_value += value

            # Calculate percentages
            for asset in assets.values():
                asset["percentage"] = (
                    (asset["value"] / total_value) * 100 if total_value > 0 else 0
                )

            return {
                "total_value": total_value,
                "usdt_balance": usdt_balance,
                "assets": assets,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            self.logger.error(f"Error getting portfolio: {e}")
            return {"total_value": 0, "usdt_balance": 0, "assets": {}}

    def load_trading_history(self) -> List[Dict]:
        """Load trading history from all bot log files"""
        trade_history = []

        try:
            # Look for all trading log files
            log_files = []
            for filename in os.listdir("."):
                if filename.endswith(".log") and any(
                    bot in filename
                    for bot in [
                        "orchestrator",
                        "smart_gains",
                        "claude",
                        "master",
                        "trading",
                    ]
                ):
                    log_files.append(filename)

            self.logger.info(f"Found {len(log_files)} trading log files")

            # Parse log files for trade information
            for log_file in log_files:
                try:
                    with open(log_file, "r") as f:
                        lines = f.readlines()

                    for line in lines:
                        # Look for trade execution patterns
                        if (
                            "Trade executed successfully" in line
                            or "Position closed" in line
                        ):
                            # Extract relevant information
                            timestamp_str = line.split(" - ")[0]
                            try:
                                timestamp = datetime.strptime(
                                    timestamp_str, "%Y-%m-%d %H:%M:%S,%f"
                                )
                            except:
                                timestamp = datetime.now()

                            trade_info = {
                                "timestamp": timestamp,
                                "log_file": log_file,
                                "details": line.strip(),
                            }
                            trade_history.append(trade_info)

                except Exception as e:
                    self.logger.warning(f"Error reading {log_file}: {e}")

            return sorted(trade_history, key=lambda x: x["timestamp"])

        except Exception as e:
            self.logger.error(f"Error loading trading history: {e}")
            return []

    def load_state_files(self) -> List[Dict]:
        """Load state files from various bots"""
        states = []

        try:
            for filename in os.listdir("."):
                if filename.endswith(".json") and any(
                    x in filename
                    for x in ["state", "orchestrator", "smart_gains", "performance"]
                ):
                    try:
                        with open(filename, "r") as f:
                            data = json.load(f)
                            data["filename"] = filename
                            states.append(data)
                    except Exception as e:
                        self.logger.warning(f"Error loading {filename}: {e}")

            return states

        except Exception as e:
            self.logger.error(f"Error loading state files: {e}")
            return []

    def calculate_performance_metrics(self, portfolio_history: List[Dict]) -> Dict:
        """Calculate comprehensive performance metrics"""
        try:
            if len(portfolio_history) < 2:
                return {}

            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(portfolio_history)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")

            # Calculate returns
            df["return"] = df["total_value"].pct_change()
            df["cumulative_return"] = (1 + df["return"]).cumprod() - 1

            # Performance metrics
            initial_value = df["total_value"].iloc[0]
            current_value = df["total_value"].iloc[-1]
            total_return = (current_value - initial_value) / initial_value * 100

            # Risk metrics
            returns = df["return"].dropna()
            volatility = returns.std() * np.sqrt(
                24
            )  # Annualized volatility (hourly data)
            sharpe_ratio = (
                returns.mean() / returns.std() * np.sqrt(24) if returns.std() > 0 else 0
            )

            # Drawdown analysis
            running_max = df["total_value"].expanding().max()
            drawdown = (df["total_value"] - running_max) / running_max * 100
            max_drawdown = drawdown.min()

            # Win rate analysis (based on hourly returns)
            positive_returns = (returns > 0).sum()
            total_periods = len(returns)
            win_rate = (
                positive_returns / total_periods * 100 if total_periods > 0 else 0
            )

            return {
                "total_return_pct": total_return,
                "current_value": current_value,
                "initial_value": initial_value,
                "volatility_pct": volatility * 100,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown_pct": max_drawdown,
                "win_rate_pct": win_rate,
                "total_periods": total_periods,
                "trading_days": (
                    df["timestamp"].iloc[-1] - df["timestamp"].iloc[0]
                ).days,
            }

        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}

    def analyze_strategy_performance(self) -> Dict:
        """Analyze performance by strategy"""
        try:
            state_files = self.load_state_files()
            strategy_analysis = {}

            for state in state_files:
                if "strategy_performance" in state:
                    for strategy, perf in state["strategy_performance"].items():
                        if strategy not in strategy_analysis:
                            strategy_analysis[strategy] = {
                                "total_trades": 0,
                                "wins": 0,
                                "total_profit": 0,
                                "trade_details": [],
                            }

                        strategy_analysis[strategy]["total_trades"] += perf.get(
                            "trades", 0
                        )
                        strategy_analysis[strategy]["wins"] += perf.get("wins", 0)
                        strategy_analysis[strategy]["total_profit"] += perf.get(
                            "total_profit", 0
                        )

            # Calculate derived metrics
            for strategy, data in strategy_analysis.items():
                if data["total_trades"] > 0:
                    data["win_rate"] = data["wins"] / data["total_trades"] * 100
                    data["avg_profit_per_trade"] = (
                        data["total_profit"] / data["total_trades"]
                    )
                else:
                    data["win_rate"] = 0
                    data["avg_profit_per_trade"] = 0

            return strategy_analysis

        except Exception as e:
            self.logger.error(f"Error analyzing strategy performance: {e}")
            return {}

    def generate_report(self) -> str:
        """Generate comprehensive performance report"""
        try:
            report = []
            report.append("=" * 80)
            report.append("🎯 VICTORYCHAIN TRADING PERFORMANCE DASHBOARD")
            report.append("=" * 80)
            report.append(
                f"📅 Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            report.append("")

            # Current Portfolio Status
            portfolio = self.get_current_portfolio()
            report.append("💰 CURRENT PORTFOLIO STATUS")
            report.append("-" * 40)
            report.append(f"Total Portfolio Value: ${portfolio['total_value']:.2f}")
            report.append(f"USDT Balance: ${portfolio['usdt_balance']:.2f}")
            report.append(f"Number of Assets: {len(portfolio['assets'])}")
            report.append("")

            # Top Holdings
            report.append("📊 TOP HOLDINGS")
            report.append("-" * 40)
            sorted_assets = sorted(
                portfolio["assets"].items(), key=lambda x: x[1]["value"], reverse=True
            )

            for i, (symbol, data) in enumerate(sorted_assets[:10]):
                report.append(
                    f"{i+1:2d}. {symbol:8s}: ${data['value']:8.2f} ({data['percentage']:5.1f}%)"
                )
            report.append("")

            # Strategy Performance
            strategy_perf = self.analyze_strategy_performance()
            if strategy_perf:
                report.append("🚀 STRATEGY PERFORMANCE")
                report.append("-" * 40)

                total_trades = sum(s["total_trades"] for s in strategy_perf.values())
                total_wins = sum(s["wins"] for s in strategy_perf.values())
                total_profit = sum(s["total_profit"] for s in strategy_perf.values())

                overall_win_rate = (
                    total_wins / total_trades * 100 if total_trades > 0 else 0
                )

                report.append(f"Overall Performance:")
                report.append(f"  Total Trades: {total_trades}")
                report.append(f"  Win Rate: {overall_win_rate:.1f}%")
                report.append(f"  Total P&L: ${total_profit:+.2f}")
                report.append("")

                for strategy, data in strategy_perf.items():
                    if data["total_trades"] > 0:
                        report.append(f"{strategy.title()}:")
                        report.append(
                            f"  Trades: {data['total_trades']} | Win Rate: {data['win_rate']:.1f}% | P&L: ${data['total_profit']:+.2f}"
                        )

                report.append("")

            # Recent Trading Activity
            trade_history = self.load_trading_history()
            if trade_history:
                report.append("📈 RECENT TRADING ACTIVITY")
                report.append("-" * 40)

                recent_trades = trade_history[-10:]  # Last 10 trades
                for trade in recent_trades:
                    report.append(
                        f"{trade['timestamp'].strftime('%m-%d %H:%M')}: {trade['details'][:60]}..."
                    )

                report.append("")

            # System Health
            report.append("🔧 SYSTEM HEALTH")
            report.append("-" * 40)

            # Check log files age
            log_files = [f for f in os.listdir(".") if f.endswith(".log")]
            if log_files:
                newest_log = max(log_files, key=lambda f: os.path.getmtime(f))
                log_age = datetime.now() - datetime.fromtimestamp(
                    os.path.getmtime(newest_log)
                )
                report.append(f"Latest Log File: {newest_log}")
                report.append(f"Last Activity: {log_age} ago")
            else:
                report.append("⚠️  No log files found")

            # Check API connectivity
            try:
                server_time = self.client.get_server_time()
                report.append("✅ Binance API: Connected")
            except:
                report.append("❌ Binance API: Connection Error")

            report.append("")
            report.append("=" * 80)

            return "\n".join(report)

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}"

    def save_performance_snapshot(self):
        """Save current performance snapshot"""
        try:
            portfolio = self.get_current_portfolio()
            strategy_perf = self.analyze_strategy_performance()

            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "portfolio": portfolio,
                "strategy_performance": strategy_perf,
                "trade_count": len(self.load_trading_history()),
            }

            filename = (
                f"performance_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(filename, "w") as f:
                json.dump(snapshot, f, indent=2, default=str)

            self.logger.info(f"Performance snapshot saved: {filename}")

        except Exception as e:
            self.logger.error(f"Error saving performance snapshot: {e}")

    def monitor_live(self, interval_minutes: int = 15):
        """Live monitoring with periodic updates"""
        try:
            self.logger.info(
                f"🔄 Starting live monitoring (updates every {interval_minutes} minutes)"
            )

            while True:
                try:
                    # Generate and display report
                    report = self.generate_report()

                    # Clear screen and display
                    os.system("clear" if os.name == "posix" else "cls")
                    print(report)

                    # Save snapshot
                    self.save_performance_snapshot()

                    # Wait for next update
                    time.sleep(interval_minutes * 60)

                except KeyboardInterrupt:
                    self.logger.info("Live monitoring stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in live monitoring: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying

        except Exception as e:
            self.logger.error(f"Error starting live monitoring: {e}")


def main():
    """Main dashboard function"""
    try:
        dashboard = TradingDashboard()

        print("🎯 VictoryChain Trading Performance Dashboard")
        print("=" * 50)
        print("Options:")
        print("1. Generate Performance Report")
        print("2. Start Live Monitoring")
        print("3. Save Performance Snapshot")
        print("4. View Current Portfolio")
        print()

        choice = input("Select option (1-4): ").strip()

        if choice == "1":
            print("\n📊 GENERATING PERFORMANCE REPORT...")
            report = dashboard.generate_report()
            print(report)

            # Save to file
            filename = (
                f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            with open(filename, "w") as f:
                f.write(report)
            print(f"\n💾 Report saved to: {filename}")

        elif choice == "2":
            interval = input("Update interval in minutes (default 15): ").strip()
            try:
                interval = int(interval) if interval else 15
            except:
                interval = 15

            dashboard.monitor_live(interval)

        elif choice == "3":
            dashboard.save_performance_snapshot()
            print("✅ Performance snapshot saved")

        elif choice == "4":
            portfolio = dashboard.get_current_portfolio()
            print(f"\n💰 Current Portfolio: ${portfolio['total_value']:.2f}")
            print(f"💵 USDT Balance: ${portfolio['usdt_balance']:.2f}")
            print(f"📊 Assets: {len(portfolio['assets'])}")

            print("\n🏆 Top Holdings:")
            sorted_assets = sorted(
                portfolio["assets"].items(), key=lambda x: x[1]["value"], reverse=True
            )

            for i, (symbol, data) in enumerate(sorted_assets[:10]):
                print(
                    f"  {i+1:2d}. {symbol:8s}: ${data['value']:8.2f} ({data['percentage']:5.1f}%)"
                )

        else:
            print("Invalid option")

    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
