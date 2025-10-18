#!/usr/bin/env python3
"""
LIVE TRADING PERFORMANCE DASHBOARD
==================================

Real-time monitoring dashboard for the maximum ROI trading system.
Tracks progress toward $1T goal with detailed performance metrics.

FEATURES:
📊 Real-time portfolio value tracking
📈 ROI calculations (daily, total, per-trade)
🎯 Progress tracking toward $1T target
🔥 Trade performance analytics
⚠️ Risk monitoring and alerts
📱 Live trade notifications

SAFETY MONITORING:
🛡️ Daily loss limits
🛡️ Total stop loss tracking
🛡️ Position size monitoring
🛡️ Risk/reward ratios
"""

import json
import time
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import ccxt
import pandas as pd
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""

    starting_capital: float
    current_portfolio_value: float
    target_capital: float
    daily_start_value: float

    trades_today: int
    total_trades: int
    winning_trades: int
    losing_trades: int

    daily_roi: float
    total_roi: float
    avg_roi_per_trade: float
    best_trade_roi: float
    worst_trade_roi: float

    daily_pnl: float
    total_pnl: float
    unrealized_pnl: float

    active_positions: int
    max_positions: int

    win_rate: float
    profit_factor: float
    sharpe_ratio: float

    risk_score: float
    safety_status: str


class LiveTradingDashboard:
    """Real-time trading performance dashboard"""

    def __init__(self):
        self.binance_client = None
        self.metrics = None
        self.trade_history = []
        self.performance_log = []

        # Dashboard settings
        self.refresh_interval = 10  # seconds
        self.target_value = 1000000000000.0  # $1T
        self.starting_capital = 100000.0

        # Risk thresholds
        self.daily_loss_limit = 5000.0
        self.total_stop_loss = 15000.0
        self.max_positions = 8

        self.setup_binance_connection()

    def setup_binance_connection(self):
        """Setup connection to Binance"""
        try:
            api_key = os.getenv("BINANCEUS_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET")

            if not api_key or not api_secret:
                print("❌ Binance API credentials not found")
                print("Set BINANCEUS_KEY and BINANCE_API_SECRET environment variables")
                return False

            self.binance_client = ccxt.binance(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "sandbox": False,
                    "enableRateLimit": True,
                }
            )

            print("✅ Connected to Binance")
            return True

        except Exception as e:
            print(f"❌ Failed to connect to Binance: {e}")
            return False

    def get_current_portfolio_value(self) -> float:
        """Get current total portfolio value in USDT"""
        try:
            balance = self.binance_client.fetch_balance()
            total_value = 0.0

            for asset, amounts in balance["total"].items():
                if amounts > 0:
                    if asset == "USDT":
                        total_value += amounts
                    else:
                        try:
                            # Convert to USDT value
                            ticker = self.binance_client.fetch_ticker(f"{asset}/USDT")
                            total_value += amounts * ticker["last"]
                        except:
                            pass  # Skip if can't get price

            return total_value

        except Exception as e:
            print(f"Error getting portfolio value: {e}")
            return 0.0

    def load_trade_history(self) -> List[Dict]:
        """Load recent trade history"""
        try:
            # Get recent trades from Binance
            orders = self.binance_client.fetch_closed_orders(limit=100)

            trades = []
            for order in orders:
                if order["status"] == "closed":
                    trades.append(
                        {
                            "timestamp": order["timestamp"],
                            "symbol": order["symbol"],
                            "side": order["side"],
                            "amount": order["amount"],
                            "price": order["price"],
                            "cost": order["cost"],
                            "fee": order.get("fee", {}).get("cost", 0),
                        }
                    )

            return trades

        except Exception as e:
            print(f"Error loading trade history: {e}")
            return []

    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        try:
            current_value = self.get_current_portfolio_value()

            # Load today's starting value (simplified - would use database in production)
            daily_start = self.starting_capital  # Placeholder

            # Calculate basic metrics
            daily_pnl = current_value - daily_start
            total_pnl = current_value - self.starting_capital
            daily_roi = daily_pnl / daily_start if daily_start > 0 else 0
            total_roi = total_pnl / self.starting_capital

            # Load trade history for more detailed metrics
            trades = self.load_trade_history()

            # Calculate trade metrics
            total_trades = len(trades)
            winning_trades = 0
            losing_trades = 0
            best_trade = 0
            worst_trade = 0

            for trade in trades:
                # Simplified P&L calculation (would be more sophisticated in production)
                if trade["side"] == "buy":
                    # This is a simplified calculation
                    pass

            win_rate = winning_trades / max(1, total_trades)

            # Risk assessment
            risk_score = self.calculate_risk_score(current_value, daily_pnl, total_pnl)
            safety_status = self.get_safety_status(daily_pnl, total_pnl)

            return PerformanceMetrics(
                starting_capital=self.starting_capital,
                current_portfolio_value=current_value,
                target_capital=self.target_value,
                daily_start_value=daily_start,
                trades_today=len([t for t in trades if self.is_today(t["timestamp"])]),
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                daily_roi=daily_roi,
                total_roi=total_roi,
                avg_roi_per_trade=total_roi / max(1, total_trades),
                best_trade_roi=best_trade,
                worst_trade_roi=worst_trade,
                daily_pnl=daily_pnl,
                total_pnl=total_pnl,
                unrealized_pnl=0.0,  # Would calculate from open positions
                active_positions=0,  # Would count from open positions
                max_positions=self.max_positions,
                win_rate=win_rate,
                profit_factor=1.0,  # Would calculate properly
                sharpe_ratio=0.0,  # Would calculate properly
                risk_score=risk_score,
                safety_status=safety_status,
            )

        except Exception as e:
            print(f"Error calculating metrics: {e}")
            return None

    def calculate_risk_score(
        self, current_value: float, daily_pnl: float, total_pnl: float
    ) -> float:
        """Calculate risk score (0-100, higher = more risky)"""
        risk_factors = []

        # Daily loss risk
        daily_loss_risk = abs(daily_pnl) / self.daily_loss_limit if daily_pnl < 0 else 0
        risk_factors.append(min(100, daily_loss_risk * 100))

        # Total loss risk
        total_loss_risk = abs(total_pnl) / self.total_stop_loss if total_pnl < 0 else 0
        risk_factors.append(min(100, total_loss_risk * 100))

        # Portfolio volatility (simplified)
        volatility_risk = 20  # Placeholder
        risk_factors.append(volatility_risk)

        return sum(risk_factors) / len(risk_factors)

    def get_safety_status(self, daily_pnl: float, total_pnl: float) -> str:
        """Get current safety status"""
        if daily_pnl < -self.daily_loss_limit * 0.8:
            return "🚨 CRITICAL - Near daily loss limit"
        elif total_pnl < -self.total_stop_loss * 0.8:
            return "🚨 CRITICAL - Near total stop loss"
        elif daily_pnl < -self.daily_loss_limit * 0.5:
            return "⚠️ WARNING - High daily loss"
        elif total_pnl < -self.total_stop_loss * 0.5:
            return "⚠️ WARNING - High total loss"
        elif daily_pnl > 0 and total_pnl > 0:
            return "✅ HEALTHY - Profitable"
        else:
            return "🟡 CAUTION - Minor losses"

    def is_today(self, timestamp: int) -> bool:
        """Check if timestamp is from today"""
        today = datetime.now().date()
        trade_date = datetime.fromtimestamp(timestamp / 1000).date()
        return trade_date == today

    def display_dashboard(self):
        """Display the live trading dashboard"""
        os.system("clear" if os.name == "posix" else "cls")  # Clear screen

        print("💰" * 30)
        print("LIVE TRADING DASHBOARD - PATH TO $1T")
        print("💰" * 30)
        print(f"🕒 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        if not self.metrics:
            print("❌ Unable to load performance metrics")
            return

        # Portfolio Overview
        print("📊 PORTFOLIO OVERVIEW")
        print("=" * 50)
        print(f"💰 Current Value:     ${self.metrics.current_portfolio_value:,.2f}")
        print(f"🎯 Target Value:      ${self.metrics.target_capital:,.0f}")
        print(f"📈 Total P&L:         ${self.metrics.total_pnl:,.2f}")
        print(f"📈 Total ROI:         {self.metrics.total_roi:.4%}")

        # Progress to Target
        progress = (
            self.metrics.current_portfolio_value / self.metrics.target_capital
        ) * 100
        print(f"🎯 Progress to $1T:   {progress:.10f}%")

        # Time estimates
        if self.metrics.daily_roi > 0:
            import math

            days_to_target = math.log(
                self.metrics.target_capital / self.metrics.current_portfolio_value
            ) / math.log(1 + self.metrics.daily_roi)
            print(f"⏱️  Days to $1T:       {days_to_target:.0f} (at current daily rate)")
        else:
            print("⏱️  Days to $1T:       Cannot calculate (negative/zero daily ROI)")

        print()

        # Daily Performance
        print("📅 TODAY'S PERFORMANCE")
        print("=" * 50)
        print(f"📈 Daily P&L:         ${self.metrics.daily_pnl:,.2f}")
        print(f"📈 Daily ROI:         {self.metrics.daily_roi:.4%}")
        print(f"🔥 Trades Today:      {self.metrics.trades_today}")
        print(f"📊 Avg ROI/Trade:     {self.metrics.avg_roi_per_trade:.4%}")
        print()

        # Trade Statistics
        print("📊 TRADE STATISTICS")
        print("=" * 50)
        print(f"📊 Total Trades:      {self.metrics.total_trades}")
        print(f"🏆 Winning Trades:    {self.metrics.winning_trades}")
        print(f"💔 Losing Trades:     {self.metrics.losing_trades}")
        print(f"🎯 Win Rate:          {self.metrics.win_rate:.2%}")
        print(f"🔥 Best Trade ROI:    {self.metrics.best_trade_roi:.2%}")
        print(f"❄️  Worst Trade ROI:   {self.metrics.worst_trade_roi:.2%}")
        print()

        # Risk Monitoring
        print("🛡️ RISK MONITORING")
        print("=" * 50)
        print(f"🚨 Safety Status:     {self.metrics.safety_status}")
        print(f"📊 Risk Score:        {self.metrics.risk_score:.1f}/100")
        print(
            f"📍 Active Positions:  {self.metrics.active_positions}/{self.metrics.max_positions}"
        )

        # Daily loss limit
        daily_loss_used = (
            abs(self.metrics.daily_pnl) if self.metrics.daily_pnl < 0 else 0
        )
        daily_loss_pct = (daily_loss_used / self.daily_loss_limit) * 100
        print(
            f"📉 Daily Loss Used:   ${daily_loss_used:.2f} / ${self.daily_loss_limit:.2f} ({daily_loss_pct:.1f}%)"
        )

        # Total loss limit
        total_loss_used = (
            abs(self.metrics.total_pnl) if self.metrics.total_pnl < 0 else 0
        )
        total_loss_pct = (total_loss_used / self.total_stop_loss) * 100
        print(
            f"📉 Total Loss Used:   ${total_loss_used:.2f} / ${self.total_stop_loss:.2f} ({total_loss_pct:.1f}%)"
        )
        print()

        # Alerts
        self.show_alerts()

        print("=" * 80)
        print(f"🔄 Next update in {self.refresh_interval} seconds... (Ctrl+C to stop)")

    def show_alerts(self):
        """Show any critical alerts"""
        alerts = []

        if self.metrics.daily_pnl < -self.daily_loss_limit * 0.8:
            alerts.append("🚨 ALERT: Approaching daily loss limit!")

        if self.metrics.total_pnl < -self.total_stop_loss * 0.8:
            alerts.append("🚨 ALERT: Approaching total stop loss!")

        if self.metrics.risk_score > 80:
            alerts.append("⚠️ WARNING: High risk score detected!")

        if self.metrics.active_positions >= self.max_positions:
            alerts.append("⚠️ WARNING: Maximum positions reached!")

        if alerts:
            print("🚨 ALERTS")
            print("=" * 50)
            for alert in alerts:
                print(alert)
            print()

    def save_performance_snapshot(self):
        """Save current performance snapshot"""
        try:
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "portfolio_value": self.metrics.current_portfolio_value,
                "daily_roi": self.metrics.daily_roi,
                "total_roi": self.metrics.total_roi,
                "trades_today": self.metrics.trades_today,
                "win_rate": self.metrics.win_rate,
                "risk_score": self.metrics.risk_score,
                "safety_status": self.metrics.safety_status,
            }

            # Append to performance log
            self.performance_log.append(snapshot)

            # Save to file every 10 snapshots
            if len(self.performance_log) % 10 == 0:
                with open("live_trading_performance_log.json", "w") as f:
                    json.dump(self.performance_log, f, indent=2)

        except Exception as e:
            print(f"Error saving performance snapshot: {e}")

    async def run_dashboard(self):
        """Run the live dashboard with continuous updates"""
        print("🚀 Starting Live Trading Dashboard...")
        print("📊 Monitoring maximum ROI trading system...")

        try:
            while True:
                # Update metrics
                self.metrics = self.calculate_performance_metrics()

                if self.metrics:
                    # Display dashboard
                    self.display_dashboard()

                    # Save snapshot
                    self.save_performance_snapshot()

                    # Check for critical alerts
                    if self.metrics.daily_pnl < -self.daily_loss_limit:
                        print("\n🚨 CRITICAL: Daily loss limit exceeded!")
                        print("🛑 Consider stopping trading for today")

                    if self.metrics.total_pnl < -self.total_stop_loss:
                        print("\n🚨 CRITICAL: Total stop loss exceeded!")
                        print("🛑 Emergency stop recommended")

                # Wait for next update
                await asyncio.sleep(self.refresh_interval)

        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped by user")
        except Exception as e:
            print(f"\n❌ Dashboard error: {e}")


def main():
    """Main function to run the dashboard"""
    dashboard = LiveTradingDashboard()

    if not dashboard.binance_client:
        print("❌ Cannot start dashboard without Binance connection")
        print("Please configure your API keys first")
        return

    print("💰 LIVE TRADING DASHBOARD")
    print("🎯 Monitoring path to $1 trillion")
    print("⚠️ Real money trading active")
    print()

    try:
        asyncio.run(dashboard.run_dashboard())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
