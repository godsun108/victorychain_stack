#!/usr/bin/env python3
"""
💎 SINGLE TRADE GAS-OPTIMIZED EXIT CALCULATOR
============================================
Calculates the optimal single exit point considering gas fees
Focuses on making ONE perfect trade with maximum profit after gas costs
"""

import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import json


@dataclass
class GasCalculation:
    """Gas cost calculation for a single trade"""

    entry_gas_gwei: float
    exit_gas_gwei: float
    gas_limit: int = 21000  # Standard transfer
    eth_price_usd: float = 2500.0

    def calculate_total_gas_cost_usd(self) -> float:
        """Calculate total gas cost in USD for entry + exit"""
        entry_cost_eth = (self.entry_gas_gwei * self.gas_limit) / 1e9
        exit_cost_eth = (self.exit_gas_gwei * self.gas_limit) / 1e9
        total_cost_eth = entry_cost_eth + exit_cost_eth
        return total_cost_eth * self.eth_price_usd


@dataclass
class TradeParameters:
    """Single trade parameters"""

    symbol: str
    entry_price: float
    position_size_usd: float
    current_price: float
    volatility: float
    liquidity_score: float
    gas_calculation: GasCalculation


@dataclass
class OptimalExit:
    """Optimal exit calculation result"""

    optimal_exit_price: float
    net_profit_usd: float
    gross_profit_usd: float
    total_gas_cost_usd: float
    roi_percentage: float
    gas_impact_percentage: float
    confidence_score: float
    reasoning: str


class SingleTradeGasOptimizer:
    """
    💎 Optimizes single trade exit considering gas fees
    """

    def __init__(self):
        self.min_profit_threshold = 50.0  # Minimum $50 profit after gas
        self.gas_efficiency_weight = 0.3  # 30% weight to gas efficiency
        self.profit_weight = 0.7  # 70% weight to profit maximization

    def calculate_optimal_exit(self, trade_params: TradeParameters) -> OptimalExit:
        """
        🎯 Calculate the single optimal exit point considering gas fees
        """
        # Calculate current position metrics
        current_gross_profit = (
            trade_params.current_price - trade_params.entry_price
        ) * (trade_params.position_size_usd / trade_params.entry_price)

        # Gas cost analysis
        total_gas_cost = trade_params.gas_calculation.calculate_total_gas_cost_usd()
        current_net_profit = current_gross_profit - total_gas_cost

        # If already profitable after gas, calculate optimal target
        if current_net_profit > self.min_profit_threshold:
            optimal_exit = self._calculate_gas_optimized_target(
                trade_params, total_gas_cost
            )
        else:
            # Calculate minimum viable exit price
            optimal_exit = self._calculate_minimum_viable_exit(
                trade_params, total_gas_cost
            )

        return optimal_exit

    def _calculate_gas_optimized_target(
        self, trade_params: TradeParameters, gas_cost: float
    ) -> OptimalExit:
        """Calculate gas-optimized profit target"""

        # Base profit target (without gas consideration)
        volatility_multiplier = 1 + (
            trade_params.volatility / 100 * 0.5
        )  # Scale with volatility
        base_profit_target = trade_params.entry_price * volatility_multiplier

        # Gas-optimized adjustments
        gas_ratio = gas_cost / trade_params.position_size_usd

        # If gas cost is significant (>2% of position), adjust target higher
        if gas_ratio > 0.02:
            gas_adjustment = 1 + (gas_ratio * 2)  # Multiply gas impact by 2
            optimal_exit_price = base_profit_target * gas_adjustment
            reasoning = f"High gas impact ({gas_ratio:.1%}) - adjusted target higher for profitability"
        else:
            # Normal profit optimization
            liquidity_adjustment = min(
                trade_params.liquidity_score / 10, 1.0
            )  # Scale by liquidity
            optimal_exit_price = base_profit_target * liquidity_adjustment
            reasoning = f"Normal gas conditions - optimizing for profit with liquidity factor {liquidity_adjustment:.2f}"

        # Calculate final metrics
        tokens_held = trade_params.position_size_usd / trade_params.entry_price
        gross_profit = (optimal_exit_price - trade_params.entry_price) * tokens_held
        net_profit = gross_profit - gas_cost
        roi_percentage = (net_profit / trade_params.position_size_usd) * 100
        gas_impact = (gas_cost / gross_profit) * 100 if gross_profit > 0 else 100

        # Confidence based on profit margin over gas costs
        profit_to_gas_ratio = net_profit / gas_cost if gas_cost > 0 else float("inf")
        confidence = min(profit_to_gas_ratio / 10, 1.0)  # Scale confidence

        return OptimalExit(
            optimal_exit_price=optimal_exit_price,
            net_profit_usd=net_profit,
            gross_profit_usd=gross_profit,
            total_gas_cost_usd=gas_cost,
            roi_percentage=roi_percentage,
            gas_impact_percentage=gas_impact,
            confidence_score=confidence,
            reasoning=reasoning,
        )

    def _calculate_minimum_viable_exit(
        self, trade_params: TradeParameters, gas_cost: float
    ) -> OptimalExit:
        """Calculate minimum viable exit to cover gas + minimum profit"""

        tokens_held = trade_params.position_size_usd / trade_params.entry_price

        # Minimum exit price to cover gas + minimum profit
        minimum_net_profit = self.min_profit_threshold
        required_gross_profit = gas_cost + minimum_net_profit
        minimal_exit_price = trade_params.entry_price + (
            required_gross_profit / tokens_held
        )

        # Add safety buffer (10%)
        optimal_exit_price = minimal_exit_price * 1.1

        # Calculate metrics
        gross_profit = (optimal_exit_price - trade_params.entry_price) * tokens_held
        net_profit = gross_profit - gas_cost
        roi_percentage = (net_profit / trade_params.position_size_usd) * 100
        gas_impact = (gas_cost / gross_profit) * 100

        confidence = 0.6  # Medium confidence for breakeven trades
        reasoning = f"Minimum viable exit to cover gas (${gas_cost:.2f}) + target profit (${minimum_net_profit})"

        return OptimalExit(
            optimal_exit_price=optimal_exit_price,
            net_profit_usd=net_profit,
            gross_profit_usd=gross_profit,
            total_gas_cost_usd=gas_cost,
            roi_percentage=roi_percentage,
            gas_impact_percentage=gas_impact,
            confidence_score=confidence,
            reasoning=reasoning,
        )

    def calculate_gas_breakeven_price(self, trade_params: TradeParameters) -> float:
        """Calculate exact breakeven price including gas costs"""
        tokens_held = trade_params.position_size_usd / trade_params.entry_price
        gas_cost = trade_params.gas_calculation.calculate_total_gas_cost_usd()

        # Breakeven price = entry price + (gas cost / tokens held)
        breakeven_price = trade_params.entry_price + (gas_cost / tokens_held)
        return breakeven_price

    def analyze_current_vs_optimal(self, trade_params: TradeParameters) -> Dict:
        """Compare current position vs optimal exit"""

        optimal_exit = self.calculate_optimal_exit(trade_params)
        breakeven_price = self.calculate_gas_breakeven_price(trade_params)

        # Current position analysis
        tokens_held = trade_params.position_size_usd / trade_params.entry_price
        current_gross_profit = (
            trade_params.current_price - trade_params.entry_price
        ) * tokens_held
        gas_cost = trade_params.gas_calculation.calculate_total_gas_cost_usd()
        current_net_profit = current_gross_profit - gas_cost
        current_roi = (current_net_profit / trade_params.position_size_usd) * 100

        # Price targets
        upside_to_optimal = (
            (optimal_exit.optimal_exit_price - trade_params.current_price)
            / trade_params.current_price
        ) * 100
        distance_from_breakeven = (
            (trade_params.current_price - breakeven_price) / breakeven_price
        ) * 100

        # Decision recommendation
        if current_net_profit >= self.min_profit_threshold:
            if upside_to_optimal > 15:  # If more than 15% upside to optimal
                decision = "HOLD - Significant upside to optimal exit"
            else:
                decision = "CONSIDER EXIT - Near optimal target"
        else:
            if distance_from_breakeven > 5:  # If 5% above breakeven
                decision = "HOLD - Above breakeven, target optimal"
            else:
                decision = "RISK ASSESSMENT - Near breakeven"

        return {
            "current_analysis": {
                "current_price": trade_params.current_price,
                "current_net_profit": current_net_profit,
                "current_roi": current_roi,
                "breakeven_price": breakeven_price,
                "distance_from_breakeven_pct": distance_from_breakeven,
            },
            "optimal_target": {
                "optimal_exit_price": optimal_exit.optimal_exit_price,
                "optimal_net_profit": optimal_exit.net_profit_usd,
                "optimal_roi": optimal_exit.roi_percentage,
                "upside_to_optimal_pct": upside_to_optimal,
            },
            "gas_impact": {
                "total_gas_cost": gas_cost,
                "gas_impact_on_profit_pct": optimal_exit.gas_impact_percentage,
                "gas_to_position_ratio": (gas_cost / trade_params.position_size_usd)
                * 100,
            },
            "recommendation": {
                "decision": decision,
                "confidence": optimal_exit.confidence_score,
                "reasoning": optimal_exit.reasoning,
            },
        }


def main():
    """
    💎 Demonstrate single trade gas-optimized exit calculation
    """
    print("💎 SINGLE TRADE GAS-OPTIMIZED EXIT CALCULATOR")
    print("=" * 55)

    # Initialize optimizer
    optimizer = SingleTradeGasOptimizer()

    # Example scenarios for different tokens and gas conditions
    scenarios = [
        {
            "name": "High Value GALA Trade (Low Gas)",
            "params": TradeParameters(
                symbol="GALA",
                entry_price=0.025,
                position_size_usd=5000.0,
                current_price=0.032,
                volatility=75.0,
                liquidity_score=8.2,
                gas_calculation=GasCalculation(
                    entry_gas_gwei=15.0,
                    exit_gas_gwei=18.0,
                    gas_limit=21000,
                    eth_price_usd=2500.0,
                ),
            ),
        },
        {
            "name": "Medium MAGIC Trade (Normal Gas)",
            "params": TradeParameters(
                symbol="MAGIC",
                entry_price=0.68,
                position_size_usd=3000.0,
                current_price=0.75,
                volatility=65.0,
                liquidity_score=7.8,
                gas_calculation=GasCalculation(
                    entry_gas_gwei=25.0,
                    exit_gas_gwei=30.0,
                    gas_limit=21000,
                    eth_price_usd=2500.0,
                ),
            ),
        },
        {
            "name": "Small ENJ Trade (High Gas)",
            "params": TradeParameters(
                symbol="ENJ",
                entry_price=0.28,
                position_size_usd=1000.0,
                current_price=0.31,
                volatility=80.0,
                liquidity_score=7.2,
                gas_calculation=GasCalculation(
                    entry_gas_gwei=45.0,
                    exit_gas_gwei=50.0,
                    gas_limit=21000,
                    eth_price_usd=2500.0,
                ),
            ),
        },
    ]

    # Analyze each scenario
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🎯 SCENARIO {i}: {scenario['name']}")
        print("-" * 50)

        params = scenario["params"]

        # Calculate optimal exit
        optimal_exit = optimizer.calculate_optimal_exit(params)

        # Analyze current vs optimal
        analysis = optimizer.analyze_current_vs_optimal(params)

        # Display results
        print(f"📊 Position Details:")
        print(f"   Symbol: {params.symbol}")
        print(f"   Entry Price: ${params.entry_price:.4f}")
        print(f"   Current Price: ${params.current_price:.4f}")
        print(f"   Position Size: ${params.position_size_usd:,.0f}")
        print(f"   Gas Cost (Total): ${analysis['gas_impact']['total_gas_cost']:.2f}")

        print(f"\n💰 Current Position:")
        print(
            f"   Current Net Profit: ${analysis['current_analysis']['current_net_profit']:.2f}"
        )
        print(f"   Current ROI: {analysis['current_analysis']['current_roi']:.1f}%")
        print(
            f"   Breakeven Price: ${analysis['current_analysis']['breakeven_price']:.4f}"
        )
        print(
            f"   Distance from Breakeven: {analysis['current_analysis']['distance_from_breakeven_pct']:.1f}%"
        )

        print(f"\n🎯 Optimal Exit Strategy:")
        print(f"   Optimal Exit Price: ${optimal_exit.optimal_exit_price:.4f}")
        print(f"   Optimal Net Profit: ${optimal_exit.net_profit_usd:.2f}")
        print(f"   Optimal ROI: {optimal_exit.roi_percentage:.1f}%")
        print(
            f"   Upside to Optimal: {analysis['optimal_target']['upside_to_optimal_pct']:.1f}%"
        )

        print(f"\n⛽ Gas Impact Analysis:")
        print(f"   Gas Cost: ${optimal_exit.total_gas_cost_usd:.2f}")
        print(f"   Gas Impact on Profit: {optimal_exit.gas_impact_percentage:.1f}%")
        print(
            f"   Gas to Position Ratio: {analysis['gas_impact']['gas_to_position_ratio']:.2f}%"
        )

        print(f"\n🔥 RECOMMENDATION:")
        print(f"   Decision: {analysis['recommendation']['decision']}")
        print(f"   Confidence: {analysis['recommendation']['confidence']:.1%}")
        print(f"   Reasoning: {analysis['recommendation']['reasoning']}")

        # Risk assessment
        if optimal_exit.gas_impact_percentage > 10:
            print(
                f"   ⚠️  WARNING: High gas impact ({optimal_exit.gas_impact_percentage:.1f}%) on profits"
            )

        if analysis["gas_impact"]["gas_to_position_ratio"] > 5:
            print(
                f"   ⚠️  WARNING: Gas cost is {analysis['gas_impact']['gas_to_position_ratio']:.1f}% of position size"
            )

    # Summary recommendations
    print(f"\n🎯 SINGLE TRADE OPTIMIZATION SUMMARY")
    print("=" * 55)
    print("💡 Key Insights:")
    print("   1. Gas costs significantly impact small positions (<$2000)")
    print("   2. Optimal exit targets should scale with gas impact")
    print("   3. High gas periods require higher profit targets")
    print("   4. Always calculate breakeven including gas costs")
    print("   5. Position sizing should consider gas efficiency")

    print(f"\n🔧 Optimization Rules:")
    print("   • Minimum position size: $1500 to minimize gas impact")
    print("   • Target gas impact: <5% of total profit")
    print("   • Use Layer 2 for positions <$3000")
    print("   • Time exits during low gas periods when possible")
    print("   • Single exit strategy maximizes gas efficiency")

    # Save analysis results
    results_summary = {
        "calculation_timestamp": datetime.now().isoformat(),
        "scenarios_analyzed": len(scenarios),
        "optimization_rules": {
            "minimum_position_size": 1500,
            "max_gas_impact_percent": 5.0,
            "recommended_layer2_threshold": 3000,
            "single_exit_strategy": True,
        },
        "gas_optimization_insights": [
            "Position sizing directly impacts gas efficiency",
            "Single exit maximizes profit per gas unit spent",
            "Layer 2 solutions recommended for smaller positions",
            "Timing exits during low gas periods saves 20-40%",
        ],
    }

    with open("single_trade_gas_optimization_analysis.json", "w") as f:
        json.dump(results_summary, f, indent=2)

    print(f"\n💾 Analysis saved to: single_trade_gas_optimization_analysis.json")
    print("💎 Single Trade Gas Optimization Complete!")


if __name__ == "__main__":
    main()
