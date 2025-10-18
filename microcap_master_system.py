#!/usr/bin/env python3

"""
BTC-FREE MICRO-CAP MASTER SYSTEM
================================
Complete integration of all framework components:
- Token universe scanning & analysis
- AI-powered predictions with ML models
- Quality-based categorization
- Execution planning & risk management
- Real-time monitoring & alerts
"""

import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# Import our framework components
from ai_prediction_engine import MicroCapPredictionEngine
from binance_us_token_analyzer import BinanceUSTokenAnalyzer


class MicroCapMasterSystem:
    """Complete BTC-free micro-cap trading system"""

    def __init__(self):
        self.token_analyzer = BinanceUSTokenAnalyzer()
        self.prediction_engine = MicroCapPredictionEngine()

        # Framework state
        self.available_tokens = []
        self.hedge_basket = []
        self.quality_longs = []
        self.current_predictions = {}
        self.portfolio_allocation = {}
        self.risk_metrics = {}

        # Configuration
        self.target_portfolio_value = 100000  # $100k example
        self.max_positions = 20
        self.min_position_size = 1000  # $1k minimum
        self.rebalance_frequency = 3600  # 1 hour

    async def initialize_system(self):
        """Initialize complete system"""
        print("🚀 INITIALIZING BTC-FREE MICRO-CAP MASTER SYSTEM")
        print("=" * 55)

        # Step 1: Load and analyze all tokens
        print("📊 Step 1: Token Universe Analysis...")
        self.token_analyzer.run_complete_analysis()
        self.available_tokens = [t["symbol"] for t in self.token_analyzer.all_tokens]
        self.hedge_basket = [t["symbol"] for t in self.token_analyzer.hedge_basket]
        self.quality_longs = [t["symbol"] for t in self.token_analyzer.quality_longs]

        print(f"✅ Analyzed {len(self.available_tokens)} tokens")
        print(f"   - Quality longs: {len(self.quality_longs)}")
        print(f"   - Hedge basket: {len(self.hedge_basket)}")

        # Step 2: Train AI models
        print("\n🤖 Step 2: AI Model Training...")
        await self.prediction_engine.train_prediction_models(self.available_tokens)

        # Step 3: Generate initial predictions
        print("\n🔮 Step 3: Initial Predictions...")
        tokens_data = {
            token["symbol"]: token for token in self.token_analyzer.all_tokens
        }
        self.current_predictions = await self.prediction_engine.generate_predictions(
            tokens_data
        )

        print("✅ System initialization complete")

    def calculate_portfolio_allocation(self) -> Dict[str, float]:
        """Calculate optimal portfolio allocation based on predictions"""
        print("\n💼 Calculating Portfolio Allocation...")

        if not self.current_predictions:
            return {}

        # Get top predictions for longs and shorts
        top_buys = self.prediction_engine.get_top_predictions("buy", 15)
        top_sells = self.prediction_engine.get_top_predictions("sell", 10)

        allocation = {}

        # Long positions (70% of portfolio)
        long_capital = self.target_portfolio_value * 0.70
        total_long_score = sum(p.confidence_score for p in top_buys)

        for i, prediction in enumerate(top_buys):
            if i >= self.max_positions // 2:  # Limit positions
                break

            # Weight by confidence and expected return
            weight = prediction.confidence_score / total_long_score
            position_size = long_capital * weight

            if position_size >= self.min_position_size:
                allocation[prediction.symbol] = {
                    "side": "long",
                    "size_usd": position_size,
                    "confidence": prediction.confidence_score,
                    "expected_return": (
                        (
                            prediction.predicted_prices.get(
                                "1h", prediction.current_price
                            )
                            / prediction.current_price
                        )
                        - 1
                    )
                    * 100,
                    "risk_score": prediction.risk_score,
                }

        # Short positions (hedge basket - 30% of portfolio)
        short_capital = self.target_portfolio_value * 0.30
        hedge_positions = min(len(self.hedge_basket), 10)  # Max 10 hedge positions

        if hedge_positions > 0:
            position_size = short_capital / hedge_positions

            for symbol in self.hedge_basket[:hedge_positions]:
                if symbol in self.current_predictions:
                    prediction = self.current_predictions[symbol]
                    allocation[symbol] = {
                        "side": "short",
                        "size_usd": position_size,
                        "confidence": prediction.confidence_score,
                        "expected_return": (
                            (
                                prediction.predicted_prices.get(
                                    "1h", prediction.current_price
                                )
                                / prediction.current_price
                            )
                            - 1
                        )
                        * 100,
                        "risk_score": prediction.risk_score,
                    }

        self.portfolio_allocation = allocation

        print(f"✅ Portfolio allocation calculated:")
        print(
            f"   - Long positions: {len([a for a in allocation.values() if a['side'] == 'long'])}"
        )
        print(
            f"   - Short positions: {len([a for a in allocation.values() if a['side'] == 'short'])}"
        )
        print(
            f"   - Total capital allocated: ${sum(a['size_usd'] for a in allocation.values()):,.0f}"
        )

        return allocation

    def calculate_risk_metrics(self) -> Dict:
        """Calculate comprehensive risk metrics"""
        if not self.portfolio_allocation:
            return {}

        # Portfolio concentration
        position_sizes = [pos["size_usd"] for pos in self.portfolio_allocation.values()]
        max_position_pct = (
            max(position_sizes) / self.target_portfolio_value * 100
            if position_sizes
            else 0
        )

        # Prediction confidence
        confidences = [pos["confidence"] for pos in self.portfolio_allocation.values()]
        avg_confidence = np.mean(confidences) if confidences else 0

        # Expected returns
        returns = [pos["expected_return"] for pos in self.portfolio_allocation.values()]
        portfolio_expected_return = np.mean(returns) if returns else 0
        return_volatility = np.std(returns) if len(returns) > 1 else 0

        # Risk scores
        risk_scores = [pos["risk_score"] for pos in self.portfolio_allocation.values()]
        avg_risk_score = np.mean(risk_scores) if risk_scores else 0

        # Long/Short balance
        long_capital = sum(
            pos["size_usd"]
            for pos in self.portfolio_allocation.values()
            if pos["side"] == "long"
        )
        short_capital = sum(
            pos["size_usd"]
            for pos in self.portfolio_allocation.values()
            if pos["side"] == "short"
        )
        net_exposure = (
            (long_capital - short_capital) / self.target_portfolio_value * 100
        )

        risk_metrics = {
            "max_position_pct": max_position_pct,
            "avg_confidence": avg_confidence,
            "portfolio_expected_return": portfolio_expected_return,
            "return_volatility": return_volatility,
            "avg_risk_score": avg_risk_score,
            "net_exposure_pct": net_exposure,
            "long_short_ratio": (
                long_capital / short_capital if short_capital > 0 else float("inf")
            ),
            "total_positions": len(self.portfolio_allocation),
            "diversification_score": (
                1 - (max_position_pct / 100) if max_position_pct > 0 else 1
            ),
        }

        self.risk_metrics = risk_metrics
        return risk_metrics

    def generate_execution_plan(self) -> Dict:
        """Generate detailed execution plan"""
        if not self.portfolio_allocation:
            return {}

        execution_plan = {
            "timestamp": datetime.now().isoformat(),
            "execution_type": "portfolio_rebalance",
            "total_positions": len(self.portfolio_allocation),
            "estimated_execution_time": 5,  # 5 minutes
            "position_details": [],
        }

        for symbol, position in self.portfolio_allocation.items():
            if symbol in self.current_predictions:
                current_price = self.current_predictions[symbol].current_price

                position_detail = {
                    "symbol": symbol,
                    "side": position["side"],
                    "size_usd": position["size_usd"],
                    "current_price": current_price,
                    "quantity": position["size_usd"] / current_price,
                    "confidence": position["confidence"],
                    "expected_return": position["expected_return"],
                    "execution_priority": (
                        "high" if position["confidence"] > 0.8 else "medium"
                    ),
                    "execution_method": "4_leg_ladder",
                    "participation_limit": 0.08,  # 8% of volume
                }

                execution_plan["position_details"].append(position_detail)

        return execution_plan

    def print_system_status(self):
        """Print comprehensive system status"""
        print("\n" + "=" * 60)
        print("🏆 BTC-FREE MICRO-CAP MASTER SYSTEM STATUS")
        print("=" * 60)

        # Market overview
        print(f"📊 MARKET OVERVIEW")
        print(f"   Total tokens analyzed: {len(self.available_tokens)}")
        print(f"   Quality long candidates: {len(self.quality_longs)}")
        print(f"   Hedge basket size: {len(self.hedge_basket)}")
        print(f"   Active predictions: {len(self.current_predictions)}")

        # Prediction summary
        if self.current_predictions:
            buy_signals = len(
                [
                    p
                    for p in self.current_predictions.values()
                    if p.recommendation in ["buy", "strong_buy"]
                ]
            )
            sell_signals = len(
                [
                    p
                    for p in self.current_predictions.values()
                    if p.recommendation in ["sell", "strong_sell"]
                ]
            )
            avg_confidence = np.mean(
                [p.confidence_score for p in self.current_predictions.values()]
            )

            print(f"\n🤖 AI PREDICTIONS")
            print(f"   Buy signals: {buy_signals}")
            print(f"   Sell signals: {sell_signals}")
            print(f"   Average confidence: {avg_confidence:.1%}")

        # Portfolio allocation
        if self.portfolio_allocation:
            long_positions = len(
                [p for p in self.portfolio_allocation.values() if p["side"] == "long"]
            )
            short_positions = len(
                [p for p in self.portfolio_allocation.values() if p["side"] == "short"]
            )
            total_allocated = sum(
                p["size_usd"] for p in self.portfolio_allocation.values()
            )

            print(f"\n💼 PORTFOLIO ALLOCATION")
            print(f"   Long positions: {long_positions}")
            print(f"   Short positions: {short_positions}")
            print(f"   Total allocated: ${total_allocated:,.0f}")
            print(
                f"   Allocation rate: {total_allocated/self.target_portfolio_value:.1%}"
            )

        # Risk metrics
        if self.risk_metrics:
            print(f"\n🛡️ RISK METRICS")
            print(f"   Max position: {self.risk_metrics['max_position_pct']:.1f}%")
            print(f"   Net exposure: {self.risk_metrics['net_exposure_pct']:.1f}%")
            print(f"   Avg confidence: {self.risk_metrics['avg_confidence']:.1%}")
            print(
                f"   Expected return: {self.risk_metrics['portfolio_expected_return']:.1f}%"
            )
            print(
                f"   Diversification: {self.risk_metrics['diversification_score']:.1%}"
            )

        # Top opportunities
        if hasattr(self.prediction_engine, "token_predictions"):
            top_buys = self.prediction_engine.get_top_predictions("buy", 3)
            if top_buys:
                print(f"\n🚀 TOP OPPORTUNITIES")
                for i, pred in enumerate(top_buys):
                    expected_return = (
                        (
                            pred.predicted_prices.get("1h", pred.current_price)
                            / pred.current_price
                        )
                        - 1
                    ) * 100
                    print(
                        f"   {i+1}. {pred.symbol}: +{expected_return:.1f}% (confidence: {pred.confidence_score:.1%})"
                    )

    def save_system_state(self):
        """Save complete system state"""
        system_state = {
            "timestamp": datetime.now().isoformat(),
            "system_config": {
                "target_portfolio_value": self.target_portfolio_value,
                "max_positions": self.max_positions,
                "min_position_size": self.min_position_size,
            },
            "market_analysis": {
                "total_tokens": len(self.available_tokens),
                "quality_longs": self.quality_longs,
                "hedge_basket": self.hedge_basket,
            },
            "portfolio_allocation": self.portfolio_allocation,
            "risk_metrics": self.risk_metrics,
            "prediction_summary": {
                "total_predictions": len(self.current_predictions),
                "avg_confidence": (
                    np.mean(
                        [p.confidence_score for p in self.current_predictions.values()]
                    )
                    if self.current_predictions
                    else 0
                ),
                "buy_signals": (
                    len(
                        [
                            p
                            for p in self.current_predictions.values()
                            if p.recommendation in ["buy", "strong_buy"]
                        ]
                    )
                    if self.current_predictions
                    else 0
                ),
            },
        }

        with open("microcap_master_system_state.json", "w") as f:
            json.dump(system_state, f, indent=2, default=str)

        print("💾 System state saved to microcap_master_system_state.json")

    async def run_complete_system(self):
        """Run complete system cycle"""
        start_time = time.time()

        # Initialize
        await self.initialize_system()

        # Calculate allocation
        self.calculate_portfolio_allocation()

        # Calculate risk metrics
        self.calculate_risk_metrics()

        # Generate execution plan
        execution_plan = self.generate_execution_plan()

        # Print status
        self.print_system_status()

        # Save state
        self.save_system_state()

        # Save execution plan
        with open("execution_plan.json", "w") as f:
            json.dump(execution_plan, f, indent=2, default=str)

        total_time = time.time() - start_time

        print(f"\n⏱️ Total system cycle time: {total_time:.1f} seconds")
        print(f"💾 Execution plan saved to execution_plan.json")
        print("\n🏁 BTC-FREE MICRO-CAP MASTER SYSTEM COMPLETE")


async def main():
    """Run the complete master system"""
    system = MicroCapMasterSystem()
    await system.run_complete_system()


if __name__ == "__main__":
    asyncio.run(main())
