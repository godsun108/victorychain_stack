#!/usr/bin/env python3

"""
🎯 FOCUSED MCP VALIDATION DEMO
==============================
Demonstrates MCP double-check validation with forced trading scenarios
to showcase both blocked and approved trades.
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.open_source.backtrader_strategy import VictoryChainMCPStrategy
import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime
import json


class ForcedTradingMCPStrategy(VictoryChainMCPStrategy):
    """Strategy that forces trading conditions to demonstrate MCP validation"""

    def __init__(self):
        super().__init__()
        self.demo_phase = 0  # Track demo phases
        self.trade_attempts = 0

    def get_mcp_data_sync(self, symbol: str) -> dict:
        """MCP data generator for demonstration with varied responses"""
        import random

        # Cycle through different MCP scenarios
        self.demo_phase = (self.demo_phase + 1) % 8

        if self.demo_phase == 0:
            # Scenario 1: High risk - should block
            return {
                "risk_score": 9.2,
                "ai_signal": "HOLD",
                "confidence": 0.7,
                "gas_efficiency_signal": "OPTIMAL",
                "portfolio_concentration": 0.5,
                "market_regime": "VOLATILE",
                "timestamp": datetime.now().isoformat(),
            }
        elif self.demo_phase == 1:
            # Scenario 2: Low confidence - should block
            return {
                "risk_score": 6.0,
                "ai_signal": "BUY",
                "confidence": 0.3,
                "gas_efficiency_signal": "OPTIMAL",
                "portfolio_concentration": 0.4,
                "market_regime": "TRENDING_UP",
                "timestamp": datetime.now().isoformat(),
            }
        elif self.demo_phase == 2:
            # Scenario 3: Gas unfavorable - should block
            return {
                "risk_score": 5.0,
                "ai_signal": "BUY",
                "confidence": 0.8,
                "gas_efficiency_signal": "AVOID",
                "portfolio_concentration": 0.3,
                "market_regime": "TRENDING_UP",
                "timestamp": datetime.now().isoformat(),
            }
        elif self.demo_phase == 3:
            # Scenario 4: Conflicting AI signal - should block
            return {
                "risk_score": 4.0,
                "ai_signal": "SELL",
                "confidence": 0.9,
                "gas_efficiency_signal": "OPTIMAL",
                "portfolio_concentration": 0.2,
                "market_regime": "TRENDING_DOWN",
                "timestamp": datetime.now().isoformat(),
            }
        elif self.demo_phase == 4:
            # Scenario 5: Perfect conditions - should approve
            return {
                "risk_score": 3.5,
                "ai_signal": "BUY",
                "confidence": 0.85,
                "gas_efficiency_signal": "OPTIMAL",
                "portfolio_concentration": 0.3,
                "market_regime": "TRENDING_UP",
                "timestamp": datetime.now().isoformat(),
            }
        elif self.demo_phase == 5:
            # Scenario 6: Good exit conditions
            return {
                "risk_score": 4.0,
                "ai_signal": "SELL",
                "confidence": 0.7,
                "gas_efficiency_signal": "SUBOPTIMAL",
                "portfolio_concentration": 0.6,
                "market_regime": "SIDEWAYS",
                "timestamp": datetime.now().isoformat(),
            }
        elif self.demo_phase == 6:
            # Scenario 7: Strong conflicting BUY signal (should block exit)
            return {
                "risk_score": 2.0,
                "ai_signal": "BUY",
                "confidence": 0.95,
                "gas_efficiency_signal": "OPTIMAL",
                "portfolio_concentration": 0.2,
                "market_regime": "TRENDING_UP",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            # Scenario 8: Emergency high risk (should approve emergency exit)
            return {
                "risk_score": 9.8,
                "ai_signal": "SELL",
                "confidence": 0.9,
                "gas_efficiency_signal": "AVOID",
                "portfolio_concentration": 0.9,
                "market_regime": "VOLATILE",
                "timestamp": datetime.now().isoformat(),
            }

    def next(self):
        """Modified next() to force trading conditions for demonstration"""

        # Update gas conditions
        self.update_gas_conditions()

        # Skip if we have a pending order
        if self.order:
            return

        # Force RSI conditions for demonstration
        current_rsi = 25.0 if not self.position else 80.0  # Force entry/exit conditions
        current_macd = 0.01
        current_signal = -0.01

        # Update MCP data for each decision
        self.update_mcp_cache()

        # Get MCP analysis
        symbol = "MAGIC"
        mcp_data = self.mcp_cache.get(symbol, {})

        # Entry logic with forced conditions
        if not self.position:
            # Force bullish TA conditions
            ta_bullish = True

            if ta_bullish:
                self.trade_attempts += 1
                self.log(
                    f"🔄 Trade Attempt #{self.trade_attempts} - Checking MCP validation..."
                )

                # MANDATORY MCP DOUBLE-CHECK for BUY decisions
                mcp_valid, mcp_reason = self.validate_mcp_decision("BUY", mcp_data)

                if mcp_valid:
                    # Calculate position size
                    position_multiplier = self.get_position_multiplier(mcp_data)
                    size = int(
                        (self.broker.get_cash() * 0.9 * position_multiplier)
                        / self.data.close[0]
                    )

                    if size > 0:
                        self.order = self.buy(size=size)
                        self.log(
                            f"✅ MCP-APPROVED BUY: Size {size}, Price {self.data.close[0]:.4f}"
                        )
                        self.log(f"🤖 MCP Validation: {mcp_reason}")
                        self.mcp_validation_count["approved"] += 1
                else:
                    self.log(f"❌ MCP BLOCKED BUY: {mcp_reason}")
                    self.mcp_validation_count["blocked"] += 1
                    self.mcp_blocked_trades += 1

        # Exit logic with forced conditions
        else:
            # Calculate current position value
            position_value = self.position.size * self.data.close[0]
            gas_exit = self.gas_optimizer.calculate_optimal_exit(
                entry_price=self.buy_price or self.data.close[0],
                current_price=self.data.close[0],
                position_size=position_value,
                gas_price_gwei=self.current_gas_price,
                eth_price=self.eth_price,
            )

            # Force exit conditions for demonstration
            gas_optimized_exit = True
            emergency_exit = self.demo_phase == 7  # Force emergency on last scenario

            should_exit = gas_optimized_exit or emergency_exit

            if should_exit:
                self.log(f"🔄 Exit Attempt - Checking MCP validation...")

                # MANDATORY MCP DOUBLE-CHECK for SELL decisions
                mcp_valid, mcp_reason = self.validate_mcp_decision("SELL", mcp_data)

                if emergency_exit:
                    # Emergency exits override MCP
                    self.order = self.sell(size=self.position.size)
                    self.log(
                        f"🚨 EMERGENCY SELL (MCP Override): Size {self.position.size}"
                    )
                    self.log(f"🤖 MCP Status: {mcp_reason}")
                    self.mcp_validation_count["emergency_override"] += 1

                elif mcp_valid:
                    # Normal MCP-approved exit
                    self.order = self.sell(size=self.position.size)
                    self.log(f"✅ MCP-APPROVED SELL: Size {self.position.size}")
                    self.log(f"💰 Exit Price: ${self.data.close[0]:.4f}")
                    self.log(f"🤖 MCP Validation: {mcp_reason}")
                    self.mcp_validation_count["approved"] += 1
                    self.gas_optimized_exits += 1

                else:
                    # MCP blocked the exit
                    self.log(f"❌ MCP BLOCKED SELL: {mcp_reason}")
                    self.log(f"🤖 MCP recommends HOLD despite exit signals")
                    self.mcp_validation_count["blocked"] += 1


def run_focused_mcp_demo():
    """Run focused MCP demonstration with forced scenarios"""

    print("=" * 80)
    print("🎯 FOCUSED MCP VALIDATION DEMONSTRATION")
    print("=" * 80)
    print("🤖 Demonstrating MANDATORY MCP double-check in various scenarios:")
    print("   1. High Risk (blocked)")
    print("   2. Low Confidence (blocked)")
    print("   3. Gas Unfavorable (blocked)")
    print("   4. Conflicting AI Signal (blocked)")
    print("   5. Perfect Conditions (approved)")
    print("   6. Normal Exit (approved)")
    print("   7. Strong Conflicting Signal (blocked exit)")
    print("   8. Emergency Override (emergency approved)")
    print("")

    cerebro = bt.Cerebro()

    # Add demo strategy
    cerebro.addstrategy(ForcedTradingMCPStrategy)

    # Create sufficient data for indicators (need at least 26 days for MACD)
    dates = pd.date_range(start="2024-01-01", end="2024-02-15", freq="1D")
    np.random.seed(42)

    # Generate realistic price data
    base_price = 0.30
    n_points = len(dates)
    price_changes = np.random.normal(0, 0.01, n_points)
    prices = base_price * np.exp(np.cumsum(price_changes))

    data = pd.DataFrame(
        {
            "datetime": dates,
            "open": prices * (1 + np.random.normal(0, 0.001, n_points)),
            "high": prices * (1 + np.abs(np.random.normal(0, 0.01, n_points))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.01, n_points))),
            "close": prices,
            "volume": np.random.uniform(50000, 200000, n_points),
        }
    )

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
    cerebro.broker.setcash(1000.0)
    cerebro.broker.setcommission(commission=0.001)

    print(f"💰 Initial Portfolio Value: ${cerebro.broker.getvalue():.2f}")
    print("🚀 Running Focused MCP Scenarios...")
    print("")

    # Run backtest
    results = cerebro.run()
    strat = results[0]

    print("")
    print("=" * 80)
    print("📊 MCP VALIDATION DEMONSTRATION RESULTS")
    print("=" * 80)

    final_value = cerebro.broker.getvalue()
    total_return = (final_value / 1000 - 1) * 100

    print(f"💰 Final Portfolio Value: ${final_value:.2f}")
    print(f"📈 Total Return: {total_return:.2f}%")

    # Detailed MCP Analysis
    if hasattr(strat, "mcp_validation_count"):
        total_validations = sum(strat.mcp_validation_count.values())
        print("")
        print("🤖 MCP VALIDATION SUMMARY:")
        print("-" * 50)

        approved = strat.mcp_validation_count.get("approved", 0)
        blocked = strat.mcp_validation_count.get("blocked", 0)
        emergency = strat.mcp_validation_count.get("emergency_override", 0)

        print(f"✅ Approved Decisions: {approved}")
        print(f"❌ Blocked Decisions: {blocked}")
        print(f"🚨 Emergency Overrides: {emergency}")
        print(f"📋 Total Validations: {total_validations}")

        if total_validations > 0:
            approval_rate = (approved / total_validations) * 100
            protection_rate = (blocked / total_validations) * 100
            emergency_rate = (emergency / total_validations) * 100

            print(f"📊 Approval Rate: {approval_rate:.1f}%")
            print(f"🛡️ Protection Rate: {protection_rate:.1f}%")
            print(f"🚨 Emergency Rate: {emergency_rate:.1f}%")

        print(f'🔄 Total Trade Attempts: {getattr(strat, "trade_attempts", 0)}')
        print(f'🚫 Bad Trades Prevented: {getattr(strat, "mcp_blocked_trades", 0)}')

    print("")
    print("🔍 DEMONSTRATION INSIGHTS:")
    print("-" * 50)
    print("• MCP validates EVERY trade decision before execution")
    print("• High risk, low confidence, and poor gas conditions block trades")
    print("• Emergency stops override MCP for critical protection")
    print("• AI signals and risk scores adapt to prevent bad trades")
    print("• Gas optimization ensures profitable single trades")

    # Save results
    demo_results = {
        "scenario": "Focused MCP Validation Demo",
        "final_value": final_value,
        "total_return_pct": total_return,
        "mcp_validations": (
            strat.mcp_validation_count if hasattr(strat, "mcp_validation_count") else {}
        ),
        "trade_attempts": getattr(strat, "trade_attempts", 0),
        "blocked_trades": getattr(strat, "mcp_blocked_trades", 0),
        "timestamp": datetime.now().isoformat(),
        "strategy_version": "Focused MCP Demo V2.1",
    }

    with open("focused_mcp_demo_results.json", "w") as f:
        json.dump(demo_results, f, indent=2)

    print("")
    print("💾 Demo results saved to: focused_mcp_demo_results.json")
    print("=" * 80)


if __name__ == "__main__":
    run_focused_mcp_demo()
