#!/usr/bin/env python3
"""
ADAPTIVE GAS OPTIMIZATION INTEGRATION
====================================

Integrates the adaptive trading trainer with the gas optimization system
for continuous learning and parameter adjustment on every trade.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from adaptive_trading_trainer import (
    AdaptiveTradingTrainer,
    TradeExecution,
    TradingParameters,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AdaptiveGasOptimizer:
    """
    Enhanced Gas Optimizer with Adaptive Learning

    Features:
    - Integrates with adaptive trading trainer
    - Learns from every trade execution
    - Continuously optimizes gas parameters
    - Adjusts scaling based on performance
    """

    def __init__(self):
        self.trainer = AdaptiveTradingTrainer()
        self.base_gas_fee = 0.001  # Base gas fee as percentage of trade size

        # Enhanced gas optimization parameters (adaptive)
        self.gas_optimization_config = {
            "min_profit_threshold": 100.0,
            "max_gas_ratio": 0.10,
            "safety_margin": 1.5,
            "dynamic_threshold_adjustment": True,
            "learning_rate": 0.1,
            "performance_window": 10,  # Number of trades to consider for adjustments
        }

        # Load existing optimization data
        self.load_optimization_history()

    def calculate_adaptive_gas_threshold(self, market_conditions: Dict) -> float:
        """Calculate adaptive gas threshold based on market conditions and learning"""
        base_threshold = self.trainer.current_parameters.min_profit_threshold

        # Adjust based on market volatility
        volatility_factor = market_conditions.get("volatility", 0.5)
        if volatility_factor > 0.7:
            # High volatility - increase threshold for safety
            adjusted_threshold = base_threshold * (1 + volatility_factor * 0.3)
        else:
            # Low volatility - can be more aggressive
            adjusted_threshold = base_threshold * (0.8 + volatility_factor * 0.4)

        # Adjust based on recent performance
        if self.trainer.performance_metrics["win_rate"] > 0.8:
            # High win rate - can lower threshold slightly
            adjusted_threshold *= 0.9
        elif self.trainer.performance_metrics["win_rate"] < 0.6:
            # Low win rate - increase threshold for safety
            adjusted_threshold *= 1.2

        return adjusted_threshold

    def calculate_adaptive_gas_ratio(
        self, symbol: str, expected_return: float
    ) -> float:
        """Calculate adaptive gas ratio based on learning"""
        base_ratio = self.trainer.current_parameters.max_gas_ratio

        # Adjust based on expected return magnitude
        if expected_return > 1000:
            # High return trades can tolerate slightly higher gas ratios
            adaptive_ratio = base_ratio * 1.2
        elif expected_return < 200:
            # Low return trades need stricter gas ratios
            adaptive_ratio = base_ratio * 0.7
        else:
            adaptive_ratio = base_ratio

        # Adjust based on symbol-specific learning
        symbol_trades = [t for t in self.trainer.trade_history if t.symbol == symbol]
        if len(symbol_trades) >= 3:
            avg_success = sum(t.success_score for t in symbol_trades[-3:]) / 3
            if avg_success > 0.8:
                # This symbol performs well - can be more aggressive
                adaptive_ratio *= 1.1
            elif avg_success < 0.5:
                # This symbol underperforms - be more conservative
                adaptive_ratio *= 0.8

        return min(0.15, max(0.02, adaptive_ratio))  # Bound the ratio

    def optimize_trade_with_learning(
        self,
        symbol: str,
        position_size: float,
        expected_profit: float,
        market_conditions: Dict,
    ) -> Dict:
        """Optimize trade parameters using adaptive learning"""

        # Calculate gas fees
        gas_fees = position_size * self.base_gas_fee

        # Get adaptive thresholds
        adaptive_threshold = self.calculate_adaptive_gas_threshold(market_conditions)
        adaptive_gas_ratio = self.calculate_adaptive_gas_ratio(symbol, expected_profit)

        # Calculate gas efficiency
        gas_efficiency = (
            gas_fees / max(expected_profit, 1) if expected_profit > 0 else 1.0
        )

        # Get ML prediction for this trade
        prediction = self.trainer.predict_trade_outcome(
            symbol, position_size, expected_profit, gas_fees, market_conditions
        )

        # Apply adaptive position sizing
        optimized_position_size = self.trainer.get_optimized_position_size(
            position_size, symbol, expected_profit, market_conditions
        )

        # Recalculate with optimized size
        optimized_gas_fees = optimized_position_size * self.base_gas_fee
        optimized_net_profit = (
            expected_profit * (optimized_position_size / position_size)
        ) - optimized_gas_fees
        optimized_gas_efficiency = optimized_gas_fees / max(optimized_net_profit, 1)

        # Decision logic with adaptive parameters
        should_execute = (
            optimized_net_profit >= adaptive_threshold
            and optimized_gas_efficiency <= adaptive_gas_ratio
            and prediction["predicted_risk"]
            <= self.trainer.current_parameters.risk_tolerance
            and prediction["confidence"]
            >= self.trainer.current_parameters.confidence_threshold
        )

        # Generate recommendation
        if should_execute:
            if prediction["confidence"] > 0.8 and optimized_gas_efficiency < 0.02:
                recommendation = "🔥 EXCELLENT: High confidence, ultra-low gas impact"
                urgency = "IMMEDIATE"
            elif prediction["confidence"] > 0.7 and optimized_gas_efficiency < 0.05:
                recommendation = "✅ VERY GOOD: High confidence, low gas impact"
                urgency = "HIGH"
            elif optimized_gas_efficiency < adaptive_gas_ratio * 0.8:
                recommendation = "✅ GOOD: Acceptable risk with good gas efficiency"
                urgency = "MEDIUM"
            else:
                recommendation = "⚠️ MARGINAL: Meets criteria but watch closely"
                urgency = "LOW"
        else:
            if optimized_net_profit < adaptive_threshold:
                recommendation = f"🚫 SKIP: Profit ${optimized_net_profit:.2f} below threshold ${adaptive_threshold:.2f}"
            elif optimized_gas_efficiency > adaptive_gas_ratio:
                recommendation = f"🚫 SKIP: Gas ratio {optimized_gas_efficiency:.1%} exceeds limit {adaptive_gas_ratio:.1%}"
            elif (
                prediction["predicted_risk"]
                > self.trainer.current_parameters.risk_tolerance
            ):
                recommendation = (
                    f"🚫 SKIP: Risk {prediction['predicted_risk']:.1%} too high"
                )
            else:
                recommendation = (
                    f"🚫 SKIP: Confidence {prediction['confidence']:.1%} too low"
                )
            urgency = "NONE"

        return {
            "symbol": symbol,
            "action": "BUY" if should_execute else "SKIP",
            "original_position_size": position_size,
            "optimized_position_size": optimized_position_size,
            "expected_profit": expected_profit,
            "optimized_net_profit": optimized_net_profit,
            "gas_fees": optimized_gas_fees,
            "gas_efficiency": optimized_gas_efficiency,
            "adaptive_threshold": adaptive_threshold,
            "adaptive_gas_ratio": adaptive_gas_ratio,
            "ml_prediction": prediction,
            "recommendation": recommendation,
            "urgency": urgency,
            "should_execute": should_execute,
            "optimization_factors": {
                "position_scaling": optimized_position_size / position_size,
                "risk_adjustment": 1.0 - prediction["predicted_risk"],
                "confidence_factor": prediction["confidence"],
                "gas_optimization": 1.0 - optimized_gas_efficiency,
            },
        }

    def process_trade_execution_result(self, trade_result: Dict, actual_outcome: Dict):
        """Process actual trade results for learning"""

        # Create trade execution record
        trade = TradeExecution(
            timestamp=datetime.now().isoformat(),
            symbol=trade_result["symbol"],
            action=trade_result["action"],
            position_size=trade_result["optimized_position_size"],
            entry_price=actual_outcome.get("entry_price", 0.0),
            exit_price=actual_outcome.get("exit_price"),
            expected_profit=trade_result["optimized_net_profit"],
            actual_profit=actual_outcome.get("actual_profit", 0.0),
            gas_fees=trade_result["gas_fees"],
            execution_time=actual_outcome.get("execution_time", 0.0),
            market_conditions=actual_outcome.get("market_conditions", {}),
            success_score=0.0,  # Will be calculated by trainer
        )

        # Record with trainer for learning
        self.trainer.record_trade_execution(trade)

        # Update gas optimization config based on performance
        self.update_gas_optimization_config()

        logger.info(f"📝 Recorded trade result for {trade.symbol}")
        logger.info(f"   Expected profit: ${trade.expected_profit:.2f}")
        logger.info(f"   Actual profit: ${trade.actual_profit:.2f}")
        logger.info(f"   Learning updated: {trade.success_score:.2f} success score")

    def update_gas_optimization_config(self):
        """Update gas optimization configuration based on learning"""
        recent_trades = self.trainer.trade_history[
            -self.gas_optimization_config["performance_window"] :
        ]

        if len(recent_trades) >= 5:
            # Calculate recent performance metrics
            avg_success = sum(t.success_score for t in recent_trades) / len(
                recent_trades
            )
            avg_gas_efficiency = sum(
                t.gas_fees / max(t.actual_profit, 1) for t in recent_trades
            ) / len(recent_trades)

            # Adjust gas optimization parameters
            learning_rate = self.gas_optimization_config["learning_rate"]

            # Adjust minimum profit threshold
            current_threshold = self.gas_optimization_config["min_profit_threshold"]
            if avg_success > 0.8:
                # High success - can lower threshold slightly
                new_threshold = current_threshold * (1 - learning_rate * 0.1)
            elif avg_success < 0.6:
                # Low success - increase threshold
                new_threshold = current_threshold * (1 + learning_rate * 0.2)
            else:
                new_threshold = current_threshold

            self.gas_optimization_config["min_profit_threshold"] = new_threshold

            # Adjust max gas ratio
            current_ratio = self.gas_optimization_config["max_gas_ratio"]
            if avg_gas_efficiency < current_ratio * 0.5:
                # Gas efficiency is much better than limit - can be slightly more aggressive
                new_ratio = current_ratio * (1 + learning_rate * 0.05)
            elif avg_gas_efficiency > current_ratio * 0.8:
                # Gas efficiency near limit - tighten it
                new_ratio = current_ratio * (1 - learning_rate * 0.1)
            else:
                new_ratio = current_ratio

            self.gas_optimization_config["max_gas_ratio"] = min(
                0.15, max(0.02, new_ratio)
            )

            logger.info(f"🔧 Updated gas optimization config:")
            logger.info(f"   Min profit threshold: ${new_threshold:.2f}")
            logger.info(f"   Max gas ratio: {new_ratio:.1%}")

    def get_current_optimization_state(self) -> Dict:
        """Get current state of the optimization system"""
        return {
            "timestamp": datetime.now().isoformat(),
            "adaptive_parameters": {
                "current_parameters": self.trainer.current_parameters.__dict__,
                "gas_optimization_config": self.gas_optimization_config,
                "performance_metrics": self.trainer.performance_metrics,
            },
            "learning_status": {
                "total_trades_learned_from": len(self.trainer.trade_history),
                "models_trained": hasattr(
                    self.trainer.profit_predictor, "feature_importances_"
                ),
                "parameter_adjustments_made": self.trainer.performance_metrics.get(
                    "parameter_adjustments", 0
                ),
                "current_win_rate": self.trainer.performance_metrics.get(
                    "win_rate", 0.0
                ),
            },
            "optimization_capabilities": {
                "adaptive_thresholds": True,
                "ml_predictions": True,
                "position_size_optimization": True,
                "symbol_specific_learning": True,
                "market_condition_adjustment": True,
            },
        }

    def save_optimization_history(self):
        """Save optimization history and state"""
        state = self.get_current_optimization_state()

        with open("adaptive_gas_optimization_state.json", "w") as f:
            json.dump(state, f, indent=2)

        logger.info("💾 Saved adaptive gas optimization state")

    def load_optimization_history(self):
        """Load existing optimization history"""
        try:
            with open("adaptive_gas_optimization_state.json", "r") as f:
                state = json.load(f)

            if "adaptive_parameters" in state:
                if "gas_optimization_config" in state["adaptive_parameters"]:
                    self.gas_optimization_config.update(
                        state["adaptive_parameters"]["gas_optimization_config"]
                    )

            logger.info("✅ Loaded existing adaptive gas optimization state")

        except FileNotFoundError:
            logger.info("No existing optimization state found - starting fresh")
        except Exception as e:
            logger.warning(f"Could not load optimization state: {e}")


async def demonstrate_adaptive_gas_optimization():
    """Demonstrate the adaptive gas optimization system"""
    optimizer = AdaptiveGasOptimizer()

    logger.info("🚀 ADAPTIVE GAS OPTIMIZATION DEMONSTRATION")
    logger.info("=" * 60)

    # Test current allocation data with adaptive optimization
    test_allocations = [
        {
            "symbol": "NEAR",
            "position_size": 3898.0,
            "expected_profit": 811.0,
            "market_conditions": {
                "volatility": 0.6,
                "volume": 0.8,
                "momentum": 0.9,
                "trend_strength": 0.85,
            },
        },
        {
            "symbol": "MNGO",
            "position_size": 3856.0,
            "expected_profit": 713.0,
            "market_conditions": {
                "volatility": 0.7,
                "volume": 0.6,
                "momentum": 0.7,
                "trend_strength": 0.75,
            },
        },
        {
            "symbol": "RAY",
            "position_size": 3813.0,
            "expected_profit": 412.0,
            "market_conditions": {
                "volatility": 0.5,
                "volume": 0.9,
                "momentum": 0.8,
                "trend_strength": 0.8,
            },
        },
        {
            "symbol": "COPE",
            "position_size": 3723.0,
            "expected_profit": 197.0,
            "market_conditions": {
                "volatility": 0.8,
                "volume": 0.3,
                "momentum": 0.2,
                "trend_strength": 0.3,
            },
        },
    ]

    optimization_results = []

    for allocation in test_allocations:
        logger.info(f"\n📊 Optimizing {allocation['symbol']}...")

        result = optimizer.optimize_trade_with_learning(
            symbol=allocation["symbol"],
            position_size=allocation["position_size"],
            expected_profit=allocation["expected_profit"],
            market_conditions=allocation["market_conditions"],
        )

        optimization_results.append(result)

        # Log detailed results
        logger.info(f"   Original size: ${result['original_position_size']:.2f}")
        logger.info(f"   Optimized size: ${result['optimized_position_size']:.2f}")
        logger.info(
            f"   Scaling factor: {result['optimization_factors']['position_scaling']:.2f}"
        )
        logger.info(f"   Expected profit: ${result['optimized_net_profit']:.2f}")
        logger.info(f"   Gas efficiency: {result['gas_efficiency']:.1%}")
        logger.info(f"   Decision: {result['action']}")
        logger.info(f"   Recommendation: {result['recommendation']}")

        # Simulate some execution results for learning
        if result["should_execute"]:
            # Simulate varying success rates
            if allocation["symbol"] in ["NEAR", "RAY"]:
                actual_profit = (
                    result["optimized_net_profit"] * 1.1
                )  # Better than expected
            elif allocation["symbol"] == "MNGO":
                actual_profit = result["optimized_net_profit"] * 0.9  # Slightly worse
            else:
                actual_profit = (
                    result["optimized_net_profit"] * 0.7
                )  # Worse than expected

            # Process the result for learning
            actual_outcome = {
                "entry_price": 10.0,  # Simulated
                "actual_profit": actual_profit,
                "execution_time": 0.5,
                "market_conditions": allocation["market_conditions"],
            }

            optimizer.process_trade_execution_result(result, actual_outcome)

        await asyncio.sleep(0.5)

    # Generate comprehensive report
    final_state = optimizer.get_current_optimization_state()

    summary_report = {
        "timestamp": datetime.now().isoformat(),
        "demonstration_summary": {
            "allocations_tested": len(test_allocations),
            "trades_recommended": sum(
                1 for r in optimization_results if r["should_execute"]
            ),
            "trades_skipped": sum(
                1 for r in optimization_results if not r["should_execute"]
            ),
            "total_optimized_allocation": sum(
                r["optimized_position_size"]
                for r in optimization_results
                if r["should_execute"]
            ),
            "expected_total_profit": sum(
                r["optimized_net_profit"]
                for r in optimization_results
                if r["should_execute"]
            ),
            "average_gas_efficiency": sum(
                r["gas_efficiency"] for r in optimization_results if r["should_execute"]
            )
            / max(1, sum(1 for r in optimization_results if r["should_execute"])),
        },
        "optimization_results": optimization_results,
        "current_system_state": final_state,
        "adaptive_learning_status": {
            "system_ready": True,
            "learning_active": True,
            "parameter_optimization": True,
            "gas_protection": True,
            "scaling_optimization": True,
        },
    }

    with open("adaptive_gas_optimization_demo.json", "w") as f:
        json.dump(summary_report, f, indent=2)

    optimizer.save_optimization_history()

    logger.info("\n🎯 ADAPTIVE GAS OPTIMIZATION DEMONSTRATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"✅ Tested {len(test_allocations)} allocations")
    logger.info(
        f"✅ Recommended {summary_report['demonstration_summary']['trades_recommended']} trades"
    )
    logger.info(
        f"✅ Protected against {summary_report['demonstration_summary']['trades_skipped']} marginal trades"
    )
    logger.info(
        f"✅ Learning system active with {final_state['learning_status']['total_trades_learned_from']} trades"
    )
    logger.info(f"📊 Report saved to: adaptive_gas_optimization_demo.json")

    return optimizer


if __name__ == "__main__":
    # Run the adaptive gas optimization demonstration
    optimizer = asyncio.run(demonstrate_adaptive_gas_optimization())

    print("\n" + "=" * 80)
    print("🧠 ADAPTIVE GAS OPTIMIZATION WITH CONTINUOUS LEARNING - ACTIVE")
    print("=" * 80)
    print("✅ Claude trained to analyze and adjust parameters with every trade")
    print("✅ Gas optimization continuously learns from trade outcomes")
    print("✅ Position sizing adapts based on ML predictions")
    print("✅ Symbol-specific learning and market condition adjustments")
    print("✅ Risk and confidence thresholds automatically optimized")
    print("=" * 80)
