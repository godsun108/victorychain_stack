#!/usr/bin/env python3

"""
🧠🪄 ENHANCED INTELLIGENT LEARNING BOT WITH MAGIC-DRIVEN ALLOCATION
Integrates MAGIC learnings into continuous learning and dynamic reallocation
Focuses on gaming sector momentum using learned parameters
"""

import json
import os
import sys
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import uuid
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

# Add project root to path
sys.path.append(os.path.dirname(__file__))

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException

    binance_available = True
except ImportError:
    binance_available = False

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))


@dataclass
class MagicLearningParameters:
    """Enhanced learning parameters based on MAGIC analysis"""

    gaming_weight: float = 0.35  # 35% weight for gaming sector
    nft_integration_weight: float = 0.25  # 25% weight for NFT potential
    ecosystem_strength_weight: float = 0.20  # 20% weight for ecosystem
    momentum_weight: float = 0.15  # 15% weight for momentum
    volume_weight: float = 0.05  # 5% weight for volume

    # MAGIC-learned thresholds
    min_gaming_score: float = 7.0  # MAGIC has 8.5
    min_ecosystem_score: float = 6.5  # MAGIC has 8.5
    target_gains: List[float] = None
    stop_loss_threshold: float = -15.0
    max_single_position: float = 0.15
    reallocation_trigger: float = 0.10  # 10% gain triggers reallocation check

    def __post_init__(self):
        if self.target_gains is None:
            self.target_gains = [30.0, 50.0, 100.0]


@dataclass
class Position:
    """Active position with MAGIC-style tracking"""

    symbol: str
    entry_price: float
    current_price: float
    allocation_percentage: float
    entry_time: datetime
    stop_loss: float
    target_prices: List[float]
    current_gain: float
    magic_similarity_score: float
    gaming_correlation: float
    position_id: str
    status: str = "ACTIVE"

    def calculate_gain(self, current_price: float) -> float:
        """Calculate current gain percentage"""
        self.current_price = current_price
        self.current_gain = (
            (current_price - self.entry_price) / self.entry_price
        ) * 100
        return self.current_gain


@dataclass
class LearningEvent:
    """Learning event based on MAGIC-style analysis"""

    timestamp: datetime
    event_type: str
    symbol: str
    trigger: str
    gain_loss: float
    learning_data: Dict
    magic_correlation: float
    action_taken: str


class EnhancedIntelligentLearningBot:
    """Enhanced bot with MAGIC-driven learning and allocation"""

    def __init__(self):
        self.magic_params = MagicLearningParameters()
        self.positions: Dict[str, Position] = {}
        self.learning_history: List[LearningEvent] = []
        self.allocation_portfolio = {"cash": 1.0}  # Start with 100% cash
        self.magic_learned_patterns = {}
        self.gaming_sector_momentum = {}
        self.load_existing_data()

    def load_existing_data(self):
        """Load existing MAGIC analysis and token data"""
        try:
            # Load MAGIC analysis
            with open("magic_analysis_20250805_142539.json", "r") as f:
                self.magic_analysis = json.load(f)

            # Load comprehensive token data
            with open("comprehensive_token_analysis_20250805_155947.json", "r") as f:
                self.token_data = json.load(f)

            # Load recent MAGIC allocation
            try:
                with open("magic_driven_allocation_20250805_191133.json", "r") as f:
                    self.recent_magic_allocation = json.load(f)
            except FileNotFoundError:
                self.recent_magic_allocation = None

            print("✅ Loaded MAGIC analysis and learning data")

        except FileNotFoundError as e:
            print(f"⚠️ Could not load data file: {e}")
            self.magic_analysis = {}
            self.token_data = []

    def calculate_magic_pattern_score(self, token_data: Dict) -> float:
        """Calculate how well a token matches MAGIC's successful pattern"""
        score = 0.0

        # Gaming sector match (highest weight)
        if token_data.get("sector") == "gaming":
            score += self.magic_params.gaming_weight * 100

        # Ecosystem strength (MAGIC scored 8.5)
        ecosystem_score = token_data.get("ecosystem_score", 5.0)
        ecosystem_normalized = min(ecosystem_score / 10.0, 1.0)
        score += (
            self.magic_params.ecosystem_strength_weight * ecosystem_normalized * 100
        )

        # Momentum correlation
        momentum = token_data.get("momentum_score", 0.0)
        momentum_normalized = min(momentum / 50.0, 1.0)  # Normalize to 50 max
        score += self.magic_params.momentum_weight * momentum_normalized * 100

        # Volume activity
        volume = token_data.get("volume_24h_usdt", 0)
        volume_score = 1.0 if volume > 10000 else volume / 10000
        score += self.magic_params.volume_weight * volume_score * 100

        # NFT integration potential (gaming tokens get high scores)
        nft_potential = 0.9 if token_data.get("sector") == "gaming" else 0.3
        score += self.magic_params.nft_integration_weight * nft_potential * 100

        return min(score, 100.0)

    def identify_reallocation_opportunities(self) -> List[Dict]:
        """Identify new allocation opportunities using MAGIC patterns"""
        opportunities = []

        for token_data in self.token_data:
            if not token_data.get("symbol", "").endswith("USDT"):
                continue

            symbol = token_data["symbol"]

            # Skip if already have position
            if symbol in self.positions:
                continue

            # Calculate MAGIC pattern score
            magic_score = self.calculate_magic_pattern_score(token_data)

            # Only consider high-scoring opportunities
            if magic_score >= 60.0:
                opportunity = {
                    "symbol": symbol,
                    "magic_pattern_score": magic_score,
                    "gaming_correlation": (
                        1.0 if token_data.get("sector") == "gaming" else 0.3
                    ),
                    "ecosystem_score": token_data.get("ecosystem_score", 5.0),
                    "momentum_score": token_data.get("momentum_score", 0.0),
                    "current_price": token_data.get("price", 0.0),
                    "volume_24h": token_data.get("volume_24h_usdt", 0.0),
                    "price_change_24h": token_data.get("price_change_24h", 0.0),
                    "recommended_allocation": min(
                        magic_score / 100 * 0.15, 0.15
                    ),  # Max 15% like MAGIC
                    "reasoning": self.generate_allocation_reasoning(
                        token_data, magic_score
                    ),
                }
                opportunities.append(opportunity)

        # Sort by MAGIC pattern score
        opportunities.sort(key=lambda x: x["magic_pattern_score"], reverse=True)
        return opportunities[:5]  # Top 5 opportunities

    def generate_allocation_reasoning(
        self, token_data: Dict, magic_score: float
    ) -> List[str]:
        """Generate reasoning for allocation based on MAGIC learnings"""
        reasoning = []

        if token_data.get("sector") == "gaming":
            reasoning.append(
                "Gaming sector correlation matches MAGIC's 8.5/10 gaming score"
            )

        ecosystem_score = token_data.get("ecosystem_score", 5.0)
        if ecosystem_score >= 7.0:
            reasoning.append(
                f"Strong ecosystem score ({ecosystem_score}/10) similar to MAGIC"
            )

        momentum = token_data.get("momentum_score", 0.0)
        if momentum >= 20.0:
            reasoning.append(
                f"High momentum ({momentum:.1f}) indicates strong market interest"
            )

        if magic_score >= 80.0:
            reasoning.append("Exceptional MAGIC pattern similarity (80%+ match)")
        elif magic_score >= 70.0:
            reasoning.append("Strong MAGIC pattern similarity (70%+ match)")

        volume = token_data.get("volume_24h_usdt", 0)
        if volume >= 50000:
            reasoning.append("Healthy trading volume indicates market liquidity")

        return reasoning

    def execute_dynamic_reallocation(self) -> Dict:
        """Execute dynamic reallocation based on MAGIC learnings"""
        timestamp = datetime.now()

        print("\n🧠🪄 ENHANCED DYNAMIC REALLOCATION USING MAGIC LEARNINGS")
        print("=" * 60)

        # Check current positions for reallocation triggers
        positions_to_reallocate = []
        for symbol, position in self.positions.items():
            # Simulate current price (in real system, fetch from API)
            current_price = position.entry_price * (1 + np.random.uniform(-0.05, 0.15))
            current_gain = position.calculate_gain(current_price)

            if current_gain >= self.magic_params.reallocation_trigger:
                positions_to_reallocate.append(
                    {
                        "symbol": symbol,
                        "position_data": {
                            "symbol": position.symbol,
                            "entry_price": position.entry_price,
                            "current_price": current_price,
                            "allocation_percentage": position.allocation_percentage,
                            "magic_similarity_score": position.magic_similarity_score,
                            "gaming_correlation": position.gaming_correlation,
                        },
                        "current_gain": current_gain,
                        "realized_amount": position.allocation_percentage,
                    }
                )

        # Identify new opportunities
        opportunities = self.identify_reallocation_opportunities()

        reallocation_plan = {
            "timestamp": timestamp.isoformat(),
            "strategy": "ENHANCED_MAGIC_DYNAMIC_REALLOCATION",
            "magic_learned_parameters": asdict(self.magic_params),
            "positions_to_reallocate": positions_to_reallocate,
            "new_opportunities": opportunities[:3],  # Top 3
            "total_available_cash": self.allocation_portfolio.get("cash", 0.0),
            "executed_trades": [],
            "learning_events": [],
        }

        available_cash = self.allocation_portfolio.get("cash", 0.0)

        # Reallocate from profitable positions
        for pos_data in positions_to_reallocate:
            symbol = pos_data["symbol"]
            gain = pos_data["current_gain"]
            realized_amount = pos_data["realized_amount"]

            print(f"\n💰 REALLOCATING FROM {symbol}")
            print(f"   Current Gain: {gain:.2f}%")
            print(f"   Realized Amount: {realized_amount:.1f}%")

            # Partial reallocation (keep 50% of profitable position)
            reallocation_amount = realized_amount * 0.5
            available_cash += reallocation_amount

            # Update position
            self.positions[symbol].allocation_percentage *= 0.5

            # Record learning event
            learning_event = LearningEvent(
                timestamp=timestamp,
                event_type="REALLOCATION_TRIGGER",
                symbol=symbol,
                trigger=f"Gained {gain:.2f}%, reallocating {reallocation_amount:.1f}%",
                gain_loss=gain,
                learning_data={"magic_pattern_match": True, "gaming_correlation": True},
                magic_correlation=pos_data["position_data"]["magic_similarity_score"],
                action_taken="PARTIAL_REALLOCATION",
            )
            self.learning_history.append(learning_event)

            # Convert learning event to dict for JSON serialization
            learning_event_dict = asdict(learning_event)
            learning_event_dict["timestamp"] = learning_event_dict[
                "timestamp"
            ].isoformat()
            reallocation_plan["learning_events"].append(learning_event_dict)

        # Allocate to new opportunities
        for opportunity in opportunities[:3]:
            if available_cash <= 0.05:  # Need at least 5% cash
                break

            symbol = opportunity["symbol"]
            allocation = min(opportunity["recommended_allocation"], available_cash)

            print(f"\n🎯 NEW ALLOCATION: {symbol}")
            print(f"   MAGIC Pattern Score: {opportunity['magic_pattern_score']:.2f}")
            print(f"   Gaming Correlation: {opportunity['gaming_correlation']:.2f}")
            print(f"   Allocation: {allocation:.1f}%")
            print(f"   Reasoning:")
            for reason in opportunity["reasoning"]:
                print(f"     • {reason}")

            # Create new position
            new_position = Position(
                symbol=symbol,
                entry_price=opportunity["current_price"],
                current_price=opportunity["current_price"],
                allocation_percentage=allocation,
                entry_time=timestamp,
                stop_loss=opportunity["current_price"]
                * (1 + self.magic_params.stop_loss_threshold / 100),
                target_prices=[
                    opportunity["current_price"] * (1 + gain / 100)
                    for gain in self.magic_params.target_gains
                ],
                current_gain=0.0,
                magic_similarity_score=opportunity["magic_pattern_score"],
                gaming_correlation=opportunity["gaming_correlation"],
                position_id=str(uuid.uuid4()),
            )

            self.positions[symbol] = new_position
            available_cash -= allocation

            # Record trade
            trade_record = {
                "symbol": symbol,
                "action": "BUY",
                "allocation_percentage": allocation,
                "entry_price": opportunity["current_price"],
                "magic_pattern_score": opportunity["magic_pattern_score"],
                "reasoning": opportunity["reasoning"],
                "timestamp": timestamp.isoformat(),
            }
            reallocation_plan["executed_trades"].append(trade_record)

        # Update cash position
        self.allocation_portfolio["cash"] = available_cash

        # Save reallocation plan
        filename = (
            f"enhanced_magic_reallocation_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(filename, "w") as f:
            json.dump(reallocation_plan, f, indent=2)

        print(f"\n💾 Enhanced reallocation plan saved: {filename}")
        print(f"💰 Remaining Cash: {available_cash:.1f}%")
        print(f"📊 Total Positions: {len(self.positions)}")
        print(f"🧠 Learning Events: {len(self.learning_history)}")

        return reallocation_plan

    def generate_learning_summary(self) -> Dict:
        """Generate summary of MAGIC-driven learning"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_learning_events": len(self.learning_history),
            "active_positions": len(self.positions),
            "magic_pattern_applications": 0,
            "gaming_sector_focus": 0,
            "average_magic_similarity": 0.0,
            "key_learnings": [],
        }

        if self.positions:
            magic_scores = [
                pos.magic_similarity_score for pos in self.positions.values()
            ]
            gaming_positions = sum(
                1 for pos in self.positions.values() if pos.gaming_correlation > 0.5
            )

            summary["average_magic_similarity"] = statistics.mean(magic_scores)
            summary["gaming_sector_focus"] = (
                gaming_positions / len(self.positions)
            ) * 100
            summary["magic_pattern_applications"] = len(
                [s for s in magic_scores if s > 70]
            )

        # Key learnings from MAGIC analysis
        summary["key_learnings"] = [
            "Gaming sector tokens prioritized (MAGIC scored 8.5/10)",
            "NFT integration weighted heavily (MAGIC scored 9.2/10)",
            "Ecosystem strength used as primary filter",
            "Conservative risk management with 15% stop loss",
            "Multiple target gains: 30%, 50%, 100%",
            "Dynamic reallocation triggered at 10% gains",
        ]

        return summary


def main():
    """Main execution function"""
    print("🧠🪄 ENHANCED INTELLIGENT LEARNING BOT WITH MAGIC-DRIVEN ALLOCATION")
    print("=" * 70)
    print(
        "Integrating MAGIC learnings for continuous learning and dynamic reallocation"
    )

    bot = EnhancedIntelligentLearningBot()

    # Initialize with some positions based on recent MAGIC allocation
    if bot.recent_magic_allocation:
        print("\n📊 Initializing with recent MAGIC-driven positions...")
        for allocation in bot.recent_magic_allocation.get("allocations", []):
            symbol = allocation["symbol"]
            position = Position(
                symbol=symbol,
                entry_price=allocation["entry_price"],
                current_price=allocation["entry_price"],
                allocation_percentage=allocation["allocation_percentage"],
                entry_time=datetime.fromisoformat(allocation["execution_time"]),
                stop_loss=allocation["stop_loss"],
                target_prices=allocation["target_prices"],
                current_gain=0.0,
                magic_similarity_score=allocation["confidence_score"],
                gaming_correlation=(
                    1.0 if "gaming" in allocation.get("reasoning", []) else 0.5
                ),
                position_id=str(uuid.uuid4()),
            )
            bot.positions[symbol] = position
            bot.allocation_portfolio["cash"] = (
                bot.allocation_portfolio.get("cash", 1.0)
                - allocation["allocation_percentage"] / 100
            )

        print(f"✅ Initialized with {len(bot.positions)} MAGIC-derived positions")

    # Execute dynamic reallocation
    reallocation_plan = bot.execute_dynamic_reallocation()

    # Generate learning summary
    learning_summary = bot.generate_learning_summary()

    print("\n🧠 LEARNING SUMMARY")
    print("-" * 40)
    print(f"📈 Active Positions: {learning_summary['active_positions']}")
    print(f"🎮 Gaming Sector Focus: {learning_summary['gaming_sector_focus']:.1f}%")
    print(
        f"🪄 Average MAGIC Similarity: {learning_summary['average_magic_similarity']:.2f}"
    )
    print(f"🎯 High Pattern Matches: {learning_summary['magic_pattern_applications']}")

    print(f"\n🔑 KEY LEARNINGS APPLIED:")
    for learning in learning_summary["key_learnings"]:
        print(f"  • {learning}")

    # Save learning summary
    with open("enhanced_magic_learning_summary.json", "w") as f:
        json.dump(learning_summary, f, indent=2)

    print("\n✅ Enhanced MAGIC-driven learning and reallocation completed!")
    print("🔄 Bot is now continuously learning and adapting based on MAGIC patterns")


if __name__ == "__main__":
    main()
