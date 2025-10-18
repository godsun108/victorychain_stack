#!/usr/bin/env python3

"""
🎯 ENHANCED MCP VALIDATION DEMO
===============================
Demonstrates the MANDATORY MCP double-check system for all trade decisions.
This demo shows both blocked and approved trades to highlight the protection system.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.open_source.backtrader_strategy import (
    VictoryChainMCPStrategy,
    run_mcp_backtest,
)
import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
import json


def create_demo_data_with_clear_signals():
    """Create demo data with clear buy/sell signals for demonstration"""

    # Generate data with clear trend patterns
    dates = pd.date_range(start="2024-01-01", end="2024-03-01", freq="1h")
    np.random.seed(123)  # Different seed for varied results

    # Create trending data with RSI signals
    base_price = 0.30
    n_points = len(dates)

    # Create price movement with clear patterns
    price_trend = np.linspace(0, 0.1, n_points)  # Upward trend
    volatility = np.random.normal(0, 0.005, n_points)
    prices = base_price * (1 + price_trend + volatility)

    # Add some clear RSI oversold/overbought patterns
    rsi_cycles = np.sin(np.linspace(0, 4 * np.pi, n_points)) * 0.3
    prices = prices * (1 + rsi_cycles * 0.1)

    data = pd.DataFrame(
        {
            "datetime": dates,
            "open": prices * (1 + np.random.normal(0, 0.001, n_points)),
            "high": prices * (1 + np.abs(np.random.normal(0, 0.01, n_points))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.01, n_points))),
            "close": prices,
            "volume": np.random.uniform(50000, 500000, n_points),
        }
    )

    return data


class DemoMCPStrategy(VictoryChainMCPStrategy):
    """Demo version with more permissive MCP for demonstration"""

    def get_mcp_data_sync(self, symbol: str) -> dict:
        """Enhanced MCP data with demonstration logic"""
        try:
            import random

            # Get current RSI for context
            rsi_val = (
                self.rsi[0] if hasattr(self, "rsi") and len(self.rsi) > 0 else 50.0
            )

            # Create more varied MCP responses for demonstration
            if len(self) % 400 < 50:  # Periodically allow trades
                # More permissive period
                risk_score = random.uniform(2.0, 6.0)
                gas_signal = random.choice(["OPTIMAL", "SUBOPTIMAL"])
                ai_signal = (
                    "BUY" if rsi_val < 35 else "SELL" if rsi_val > 65 else "HOLD"
                )
                confidence = random.uniform(0.6, 0.9)
            else:
                # Normal protective behavior
                risk_score = random.uniform(4.0, 9.5)
                gas_signal = random.choice(["OPTIMAL", "SUBOPTIMAL", "AVOID"])

                if rsi_val < 25:
                    ai_signal = random.choice(["BUY", "HOLD"])
                    confidence = random.uniform(0.4, 0.8)
                elif rsi_val > 75:
                    ai_signal = random.choice(["SELL", "HOLD"])
                    confidence = random.uniform(0.3, 0.7)
                else:
                    ai_signal = "HOLD"
                    confidence = random.uniform(0.3, 0.6)

            return {
                "risk_score": min(10.0, max(1.0, risk_score)),
                "technical_indicators": {
                    "rsi": rsi_val,
                    "macd_signal": (
                        "BULLISH"
                        if ai_signal == "BUY"
                        else "BEARISH" if ai_signal == "SELL" else "NEUTRAL"
                    ),
                    "sentiment_score": confidence,
                },
                "ai_signal": ai_signal,
                "confidence": confidence,
                "portfolio_concentration": random.uniform(0.2, 0.7),
                "market_regime": random.choice(["TRENDING_UP", "SIDEWAYS", "VOLATILE"]),
                "gas_efficiency_signal": gas_signal,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            self.log(f"MCP error: {e}")
            return None


def run_enhanced_mcp_demo():
    """Run enhanced MCP demonstration with varied outcomes"""

    print("=" * 80)
    print("🎯 ENHANCED MCP VALIDATION DEMONSTRATION")
    print("=" * 80)
    print("🤖 This demo shows MANDATORY MCP double-check validation in action")
    print("⛽ Single trade gas optimization with AI risk management")
    print("🛡️ Protection mechanisms prevent high-risk trades")
    print("")

    cerebro = bt.Cerebro()

    # Add demo strategy
    cerebro.addstrategy(DemoMCPStrategy)

    # Create demo data with clear signals
    data = create_demo_data_with_clear_signals()

    # Convert to Backtrader format
    data_bt = bt.feeds.PandasData(
        dataname=data,
        datetime="datetime",
        open="open",
        high="high",
        low="low",
        close="close",
        volume="volume",
        openinterest=None,
    )

    cerebro.adddata(data_bt)

    # Set initial cash
    cerebro.broker.setcash(1000.0)

    # Add commission
    cerebro.broker.setcommission(commission=0.001)  # 0.1% commission

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")

    print(f"💰 Initial Portfolio Value: ${cerebro.broker.getvalue():.2f}")
    print("🚀 Starting Enhanced MCP Validation Demo...")
    print("")

    # Run backtest
    results = cerebro.run()
    strat = results[0]

    print("")
    print("=" * 80)
    print("📊 DEMONSTRATION RESULTS")
    print("=" * 80)

    final_value = cerebro.broker.getvalue()
    total_return = (final_value / 1000 - 1) * 100

    print(f"💰 Final Portfolio Value: ${final_value:.2f}")
    print(f"📈 Total Return: {total_return:.2f}%")

    # Detailed MCP Analysis
    if hasattr(strat, "mcp_validation_count"):
        total_validations = sum(strat.mcp_validation_count.values())
        if total_validations > 0:
            print("")
            print("🤖 MCP VALIDATION ANALYSIS:")
            print("-" * 40)

            approved = strat.mcp_validation_count["approved"]
            blocked = strat.mcp_validation_count["blocked"]
            emergency = strat.mcp_validation_count["emergency_override"]

            print(f"✅ Approved Trades: {approved}")
            print(f"❌ Blocked Trades: {blocked}")
            print(f"🚨 Emergency Overrides: {emergency}")
            print(f"📋 Total Validations: {total_validations}")

            if total_validations > 0:
                approval_rate = (approved / total_validations) * 100
                protection_rate = (blocked / total_validations) * 100
                print(f"📊 Approval Rate: {approval_rate:.1f}%")
                print(f"🛡️ Protection Rate: {protection_rate:.1f}%")

            if hasattr(strat, "mcp_blocked_trades"):
                print(
                    f"🚫 Potentially Bad Trades Prevented: {strat.mcp_blocked_trades}"
                )

            if hasattr(strat, "gas_optimized_exits"):
                print(f"⛽ Gas-Optimized Exits: {strat.gas_optimized_exits}")

    # Traditional Analytics
    print("")
    print("📈 PERFORMANCE ANALYTICS:")
    print("-" * 40)

    if hasattr(strat.analyzers.sharpe, "get_analysis"):
        sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio", "N/A")
        print(f"📊 Sharpe Ratio: {sharpe}")

    if hasattr(strat.analyzers.drawdown, "get_analysis"):
        dd = strat.analyzers.drawdown.get_analysis()
        print(f"📉 Max Drawdown: {dd.max.drawdown:.2f}%")

    if hasattr(strat.analyzers.trades, "get_analysis"):
        trades = strat.analyzers.trades.get_analysis()
        print(f"🎯 Total Completed Trades: {trades.total.total}")
        if trades.total.total > 0:
            win_rate = (trades.won.total / trades.total.total) * 100
            print(
                f"🏆 Win Rate: {win_rate:.1f}% ({trades.won.total}/{trades.total.total})"
            )

            if hasattr(trades, "pnl") and hasattr(trades.pnl, "net"):
                avg_trade = trades.pnl.net.average if trades.total.total > 0 else 0
                print(f"💵 Average Trade PnL: ${avg_trade:.2f}")

    # Key Insights
    print("")
    print("🔍 KEY INSIGHTS:")
    print("-" * 40)
    print("• MCP validation provides mandatory double-check for ALL trade decisions")
    print("• Gas optimization ensures minimum $50 profit after transaction costs")
    print("• Emergency stops override MCP for critical position protection")
    print("• AI risk scoring adapts to market conditions and technical indicators")
    print("• Comprehensive tracking enables strategy performance analysis")

    # Save demo results
    demo_results = {
        "final_value": final_value,
        "total_return_pct": total_return,
        "mcp_validations": (
            strat.mcp_validation_count if hasattr(strat, "mcp_validation_count") else {}
        ),
        "trades_count": strat.trades_count if hasattr(strat, "trades_count") else 0,
        "winning_trades": (
            strat.winning_trades if hasattr(strat, "winning_trades") else 0
        ),
        "gas_optimized_exits": (
            strat.gas_optimized_exits if hasattr(strat, "gas_optimized_exits") else 0
        ),
        "timestamp": datetime.now().isoformat(),
        "strategy_version": "Enhanced MCP V2.1",
    }

    with open("enhanced_mcp_demo_results.json", "w") as f:
        json.dump(demo_results, f, indent=2)

    print("")
    print("💾 Demo results saved to: enhanced_mcp_demo_results.json")
    print("=" * 80)


if __name__ == "__main__":
    run_enhanced_mcp_demo()
