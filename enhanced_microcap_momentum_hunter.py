#!/usr/bin/env python3

"""
🎯 ENHANCED MICROCAP MOMENTUM HUNTER
Advanced real-time scanner for microcap tokens with momentum potential
Lower thresholds, broader scanning, immediate opportunity identification
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
class HighPotentialMicrocap:
    """High potential microcap with momentum building"""

    symbol: str
    price: float
    volume_24h: float
    price_change_24h: float
    momentum_score: float
    potential_rating: float
    entry_signal: str
    risk_reward_ratio: float
    claude_analysis: str
    immediate_action: str
    position_size_recommendation: float
    stop_loss_price: float
    target_prices: List[float]
    catalyst_timeline: str


class EnhancedMicrocapHunter:
    """Enhanced microcap momentum hunter with aggressive opportunity detection"""

    def __init__(self):
        self.load_all_data()

        # More aggressive parameters for opportunity detection
        self.aggressive_params = {
            "min_volume": 500,  # Lower volume threshold
            "max_price": 2.0,  # Higher price ceiling
            "min_price": 0.00001,  # Lower price floor
            "momentum_threshold": 2.0,  # Much lower momentum threshold
            "potential_threshold": 40.0,  # Lower potential threshold
            "risk_tolerance": "EXTREME",
            "max_single_allocation": 30.0,  # Higher allocation for best opportunities
            "stop_loss": -12.0,  # Slightly wider stops
            "aggressive_targets": [
                50.0,
                150.0,
                400.0,
                1000.0,
            ],  # Very aggressive targets
        }

    def load_all_data(self):
        """Load all available data"""
        try:
            with open("comprehensive_token_analysis_20250805_155947.json", "r") as f:
                self.all_tokens = json.load(f)
            print(f"✅ Loaded {len(self.all_tokens)} tokens for aggressive scanning")
        except FileNotFoundError:
            self.all_tokens = []

    def calculate_enhanced_potential(self, token: Dict) -> float:
        """Calculate enhanced potential score with aggressive parameters"""
        potential = 0.0

        price = token.get("price", 0.0)
        volume = token.get("volume_24h_usdt", 0.0)
        momentum = token.get("momentum_score", 0.0)
        price_change = token.get("price_change_24h", 0.0)
        sector = token.get("sector", "unknown")

        # Ultra-low price bonus (40% weight) - The lower, the higher the potential
        if price <= 0.0001:
            potential += 40.0
        elif price <= 0.001:
            potential += 35.0
        elif price <= 0.01:
            potential += 30.0
        elif price <= 0.1:
            potential += 25.0
        elif price <= 0.5:
            potential += 20.0
        elif price <= 1.0:
            potential += 15.0
        else:
            potential += 10.0

        # Volume activity (25% weight) - Any volume is good for microcaps
        if volume >= 10000:
            potential += 25.0
        elif volume >= 5000:
            potential += 20.0
        elif volume >= 1000:
            potential += 15.0
        elif volume >= 500:
            potential += 10.0
        else:
            potential += 5.0

        # Any positive momentum (20% weight)
        if momentum >= 10.0:
            potential += 20.0
        elif momentum >= 5.0:
            potential += 15.0
        elif momentum >= 2.0:
            potential += 10.0
        elif momentum >= 1.0:
            potential += 8.0
        else:
            potential += 5.0

        # Sector potential (10% weight)
        high_potential_sectors = ["gaming", "ai", "metaverse", "nft", "meme"]
        medium_potential_sectors = ["defi", "layer1", "infrastructure"]

        if sector in high_potential_sectors:
            potential += 10.0
        elif sector in medium_potential_sectors:
            potential += 7.0
        else:
            potential += 4.0

        # Price action bonus (5% weight)
        if price_change > 0:
            potential += min(abs(price_change) / 10.0, 1.0) * 5.0
        else:
            potential += 2.0  # Even negative can reverse

        return min(potential, 100.0)

    def generate_aggressive_analysis(self, token: Dict, potential: float) -> str:
        """Generate aggressive Claude-style analysis"""
        symbol = token["symbol"]
        price = token["price"]
        volume = token.get("volume_24h_usdt", 0.0)
        momentum = token.get("momentum_score", 0.0)
        sector = token.get("sector", "unknown")
        price_change = token.get("price_change_24h", 0.0)

        if potential >= 80.0:
            analysis = f"""
🔥🔥 ULTRA-HIGH POTENTIAL MICROCAP: {symbol} 🔥🔥

EXPLOSIVE OPPORTUNITY DETECTED:
• Price: ${price:.8f} - EXTREMELY LOW ENTRY POINT
• Sector: {sector.upper()} - High growth potential
• Volume: ${volume:,.0f} - Sufficient for position building
• Momentum: {momentum:.1f} - Building steam

AGGRESSIVE BULL CASE:
• Ultra-low price = Maximum upside potential
• Any significant catalyst could trigger 10-100x moves
• {sector} sector has shown explosive growth patterns
• Low market cap means institutions haven't discovered yet

IMMEDIATE ACTION PLAN:
• BUY SIGNAL: STRONG
• Position Size: 25-30% allocation
• Entry Strategy: IMMEDIATE or on any dip
• Stop Loss: -12% (${price * 0.88:.8f})
• Targets: +50%, +150%, +400%, +1000%

⚠️ EXTREME RISK - EXTREME REWARD
This is a lottery ticket play with massive upside potential.
            """
        elif potential >= 65.0:
            analysis = f"""
🚀 HIGH POTENTIAL MICROCAP: {symbol}

STRONG OPPORTUNITY:
• Price: ${price:.8f} - Low entry point
• {sector} sector positioning
• Volume: ${volume:,.0f} - Adequate activity
• Momentum: {momentum:.1f} - Early stage buildup

BULL THESIS:
• Significant upside from current levels
• Potential for 5-25x if momentum builds
• Low market cap allows for rapid appreciation
• Sector tailwinds could accelerate growth

STRATEGY:
• Entry: BUY on strength or weakness
• Position: 15-20% allocation
• Stop: -12%
• Targets: +50%, +150%, +400%

HIGH RISK - HIGH REWARD PLAY
            """
        elif potential >= 50.0:
            analysis = f"""
📈 MODERATE POTENTIAL MICROCAP: {symbol}

OPPORTUNITY ASSESSMENT:
• Price: ${price:.8f}
• Sector: {sector}
• Current momentum: {momentum:.1f}
• Volume: ${volume:,.0f}

POTENTIAL FACTORS:
• Reasonable entry point
• 2-10x potential if catalysts emerge
• Worth monitoring for breakout patterns
• Could surprise on positive news

CONSERVATIVE APPROACH:
• Small position: 5-10%
• Wait for momentum confirmation
• Tight stop: -10%
• Conservative targets: +25%, +75%, +200%
            """
        else:
            analysis = f"""
👀 WATCHING: {symbol}

CURRENT STATUS:
• Price: ${price:.8f}
• Low momentum: {momentum:.1f}
• Limited volume: ${volume:,.0f}

ASSESSMENT:
• Needs catalyst for significant move
• Monitor for volume increase
• Wait for better entry signals
• Potential future opportunity

RECOMMENDATION: WATCH LIST
            """

        return analysis

    def identify_immediate_opportunities(self) -> List[HighPotentialMicrocap]:
        """Identify immediate high-potential microcap opportunities"""
        opportunities = []

        print("🔍 AGGRESSIVE MICROCAP SCANNING...")
        print("Looking for immediate high-potential opportunities...")

        for token in self.all_tokens:
            if not token.get("symbol", "").endswith("USDT"):
                continue

            price = token.get("price", 0.0)
            volume = token.get("volume_24h_usdt", 0.0)

            # Broader criteria for opportunity detection
            if (
                self.aggressive_params["min_price"]
                <= price
                <= self.aggressive_params["max_price"]
                and volume >= self.aggressive_params["min_volume"]
            ):

                potential = self.calculate_enhanced_potential(token)

                # Lower threshold for inclusion
                if potential >= 40.0:

                    symbol = token["symbol"]
                    momentum = token.get("momentum_score", 0.0)
                    price_change = token.get("price_change_24h", 0.0)

                    # Determine entry signal
                    if potential >= 80.0:
                        entry_signal = "IMMEDIATE_BUY"
                        immediate_action = "BUY NOW"
                        position_size = 30.0
                    elif potential >= 65.0:
                        entry_signal = "STRONG_BUY"
                        immediate_action = "BUY ON STRENGTH"
                        position_size = 20.0
                    elif potential >= 50.0:
                        entry_signal = "BUY"
                        immediate_action = "ACCUMULATE"
                        position_size = 15.0
                    else:
                        entry_signal = "WEAK_BUY"
                        immediate_action = "SMALL POSITION"
                        position_size = 8.0

                    # Risk-reward calculation
                    upside_potential = max(potential * 10, 200)  # Minimum 200% upside
                    downside_risk = 12.0  # 12% stop loss
                    risk_reward_ratio = upside_potential / downside_risk

                    # Calculate prices
                    stop_loss_price = price * (
                        1 - self.aggressive_params["stop_loss"] / 100
                    )
                    target_prices = [
                        price * (1 + target / 100)
                        for target in self.aggressive_params["aggressive_targets"]
                    ]

                    # Generate analysis
                    claude_analysis = self.generate_aggressive_analysis(
                        token, potential
                    )

                    # Catalyst timeline
                    if potential >= 75.0:
                        catalyst_timeline = "IMMEDIATE (Days)"
                    elif potential >= 60.0:
                        catalyst_timeline = "SHORT_TERM (1-4 weeks)"
                    else:
                        catalyst_timeline = "MEDIUM_TERM (1-3 months)"

                    opportunity = HighPotentialMicrocap(
                        symbol=symbol,
                        price=price,
                        volume_24h=volume,
                        price_change_24h=price_change,
                        momentum_score=momentum,
                        potential_rating=potential,
                        entry_signal=entry_signal,
                        risk_reward_ratio=risk_reward_ratio,
                        claude_analysis=claude_analysis,
                        immediate_action=immediate_action,
                        position_size_recommendation=position_size,
                        stop_loss_price=stop_loss_price,
                        target_prices=target_prices,
                        catalyst_timeline=catalyst_timeline,
                    )

                    opportunities.append(opportunity)

        # Sort by potential rating
        opportunities.sort(key=lambda x: x.potential_rating, reverse=True)
        return opportunities

    def execute_aggressive_scan(self):
        """Execute aggressive microcap scan"""
        timestamp = datetime.now()

        print("🎯 ENHANCED MICROCAP MOMENTUM HUNTER")
        print("=" * 50)
        print("Aggressive scanning for immediate opportunities...")

        opportunities = self.identify_immediate_opportunities()

        print(f"\n🚀 IMMEDIATE HIGH-POTENTIAL OPPORTUNITIES: {len(opportunities)}")
        print("-" * 55)

        # Display top opportunities
        for i, opp in enumerate(opportunities[:8], 1):
            print(f"\n#{i}. {opp.symbol}")
            print(f"   💰 Price: ${opp.price:.8f}")
            print(f"   🎯 Potential: {opp.potential_rating:.1f}%")
            print(f"   📊 Entry Signal: {opp.entry_signal}")
            print(f"   💪 Position Size: {opp.position_size_recommendation:.0f}%")
            print(f"   ⚡ Action: {opp.immediate_action}")
            print(f"   📈 Risk/Reward: {opp.risk_reward_ratio:.1f}:1")
            print(f"   ⏰ Timeline: {opp.catalyst_timeline}")

            # Show first target
            if opp.target_prices:
                first_target_gain = (
                    (opp.target_prices[0] - opp.price) / opp.price
                ) * 100
                print(
                    f"   🎯 First Target: ${opp.target_prices[0]:.8f} (+{first_target_gain:.0f}%)"
                )

        # Show detailed analysis for top 3
        print(f"\n📋 DETAILED ANALYSIS - TOP OPPORTUNITIES")
        print("=" * 60)

        for i, opp in enumerate(opportunities[:3], 1):
            print(f"\n{'-'*20} OPPORTUNITY #{i} {'-'*20}")
            print(opp.claude_analysis)

            print(f"\n📊 EXECUTION DETAILS:")
            print(f"• Immediate Action: {opp.immediate_action}")
            print(f"• Position Size: {opp.position_size_recommendation:.0f}%")
            print(f"• Entry: ${opp.price:.8f}")
            print(f"• Stop Loss: ${opp.stop_loss_price:.8f} (-12%)")
            print(f"• Target 1: ${opp.target_prices[0]:.8f} (+50%)")
            print(f"• Target 2: ${opp.target_prices[1]:.8f} (+150%)")
            print(f"• Timeline: {opp.catalyst_timeline}")

        # Save comprehensive report
        report = {
            "timestamp": timestamp.isoformat(),
            "scan_type": "AGGRESSIVE_MICROCAP_MOMENTUM_HUNT",
            "total_opportunities": len(opportunities),
            "immediate_buy_signals": len(
                [o for o in opportunities if "IMMEDIATE" in o.entry_signal]
            ),
            "high_potential_count": len(
                [o for o in opportunities if o.potential_rating >= 70]
            ),
            "opportunities": [asdict(opp) for opp in opportunities],
            "scan_parameters": self.aggressive_params,
        }

        filename = (
            f"aggressive_microcap_hunt_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(filename, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n💾 Aggressive scan report saved: {filename}")
        print(f"🎯 Total Opportunities Found: {len(opportunities)}")
        print(
            f"🔥 Immediate Buy Signals: {len([o for o in opportunities if 'IMMEDIATE' in o.entry_signal])}"
        )
        print(
            f"💎 High Potential (70%+): {len([o for o in opportunities if o.potential_rating >= 70])}"
        )

        return opportunities


def main():
    """Main execution function"""
    print("🎯 ENHANCED MICROCAP MOMENTUM HUNTER")
    print("=" * 40)
    print("Aggressive scanning for immediate opportunities")
    print("Lower thresholds, higher potential rewards")

    hunter = EnhancedMicrocapHunter()
    opportunities = hunter.execute_aggressive_scan()

    if opportunities:
        print(f"\n⚡ IMMEDIATE ACTION ITEMS:")
        immediate_ops = [
            o
            for o in opportunities
            if "IMMEDIATE" in o.entry_signal or o.potential_rating >= 75
        ]

        for opp in immediate_ops[:3]:
            print(
                f"• {opp.symbol}: {opp.immediate_action} - {opp.position_size_recommendation:.0f}% position"
            )

        print(f"\n⚠️ EXTREME RISK WARNINGS:")
        print("• These are lottery ticket plays with extreme volatility")
        print("• Only use risk capital you can afford to lose completely")
        print("• Set stop losses and stick to them")
        print("• Take profits at targets - don't get greedy")
        print("• Monitor positions continuously during trading hours")

    else:
        print("❌ No immediate opportunities found with current criteria")

    print("\n✅ Aggressive microcap hunt completed!")


if __name__ == "__main__":
    main()
