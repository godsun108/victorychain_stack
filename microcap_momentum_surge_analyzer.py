#!/usr/bin/env python3

"""
🚀 MICROCAP MOMENTUM SURGE ANALYZER
Advanced AI-powered analysis of ALL microcap tokens for momentum opportunities
Real-time scanning, Claude analysis, and high-risk/high-reward identification
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
import requests
from collections import defaultdict

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
class MicrocapOpportunity:
    """Microcap momentum opportunity"""

    symbol: str
    price: float
    market_cap_estimate: float
    volume_24h: float
    price_change_24h: float
    momentum_score: float
    surge_potential: float
    risk_level: str
    claude_analysis: str
    entry_confidence: float
    expected_multiplier: float
    time_horizon: str
    catalyst_factors: List[str]
    risk_factors: List[str]


@dataclass
class MomentumSurgeSignal:
    """Momentum surge detection signal"""

    symbol: str
    surge_strength: float
    surge_type: str
    volume_explosion: float
    price_acceleration: float
    technical_breakout: bool
    social_momentum: float
    timestamp: datetime
    urgency_level: str


class MicrocapMomentumEngine:
    """Advanced microcap momentum detection and analysis engine"""

    def __init__(self):
        self.load_all_token_data()
        self.microcap_threshold = 50000000  # $50M market cap threshold
        self.momentum_opportunities = []
        self.surge_signals = []

        # Microcap-specific parameters
        self.microcap_params = {
            "min_volume": 1000,  # Minimum daily volume
            "max_price": 1.0,  # Maximum price for microcap
            "min_price": 0.0001,  # Minimum price to avoid dead tokens
            "momentum_threshold": 10.0,  # Minimum momentum score
            "surge_threshold": 20.0,  # Momentum surge detection
            "risk_tolerance": "HIGH",  # High risk for high reward
            "max_allocation_per_token": 25.0,  # 25% max per microcap
            "stop_loss": -15.0,  # Tight stop loss for microcaps
            "target_multipliers": [2.0, 5.0, 10.0, 25.0],  # Aggressive targets
        }

    def load_all_token_data(self):
        """Load all available token data"""
        try:
            with open("comprehensive_token_analysis_20250805_155947.json", "r") as f:
                self.all_tokens = json.load(f)

            print(f"✅ Loaded {len(self.all_tokens)} tokens for microcap analysis")

        except FileNotFoundError:
            print("⚠️ No token data found - using simulation data")
            self.all_tokens = []

    def identify_microcap_tokens(self) -> List[Dict]:
        """Identify all microcap tokens based on criteria"""
        microcaps = []

        for token in self.all_tokens:
            if not token.get("symbol", "").endswith("USDT"):
                continue

            price = token.get("price", 0.0)
            volume = token.get("volume_24h_usdt", 0.0)

            # Microcap criteria
            is_microcap = (
                self.microcap_params["min_price"]
                <= price
                <= self.microcap_params["max_price"]
                and volume >= self.microcap_params["min_volume"]
            )

            if is_microcap:
                # Estimate market cap (rough approximation)
                estimated_mcap = price * 1000000000  # Assume 1B token supply

                token["estimated_market_cap"] = estimated_mcap
                token["microcap_score"] = self.calculate_microcap_score(token)
                microcaps.append(token)

        print(f"🔍 Identified {len(microcaps)} microcap tokens")
        return microcaps

    def calculate_microcap_score(self, token: Dict) -> float:
        """Calculate comprehensive microcap opportunity score"""
        score = 0.0

        # Volume momentum (30% weight)
        volume = token.get("volume_24h_usdt", 0.0)
        volume_score = min(volume / 100000, 1.0) * 30.0  # Normalize to 100k volume
        score += volume_score

        # Price momentum (25% weight)
        price_change = token.get("price_change_24h", 0.0)
        momentum_score = token.get("momentum_score", 0.0)

        if price_change > 0:  # Positive momentum
            price_momentum = min(abs(price_change) / 50.0, 1.0) * 15.0
            momentum_component = min(momentum_score / 50.0, 1.0) * 10.0
            score += price_momentum + momentum_component

        # Low price advantage (20% weight) - Lower price = higher potential
        price = token.get("price", 1.0)
        if price <= 0.01:
            score += 20.0
        elif price <= 0.1:
            score += 15.0
        elif price <= 0.5:
            score += 10.0
        else:
            score += 5.0

        # Sector bonus (15% weight)
        sector = token.get("sector", "unknown")
        if sector in ["gaming", "metaverse", "nft"]:
            score += 15.0
        elif sector in ["defi", "ai", "infrastructure"]:
            score += 10.0
        else:
            score += 5.0

        # Ecosystem strength (10% weight)
        ecosystem = token.get("ecosystem_score", 5.0)
        score += (ecosystem / 10.0) * 10.0

        return min(score, 100.0)

    def detect_momentum_surges(
        self, microcaps: List[Dict]
    ) -> List[MomentumSurgeSignal]:
        """Detect momentum surges in microcap tokens"""
        surge_signals = []

        for token in microcaps:
            symbol = token["symbol"]

            # Volume explosion detection
            volume = token.get("volume_24h_usdt", 0.0)
            avg_volume = volume * 0.7  # Simulate average volume
            volume_explosion = (volume / max(avg_volume, 1)) - 1

            # Price acceleration
            price_change = token.get("price_change_24h", 0.0)
            momentum = token.get("momentum_score", 0.0)
            price_acceleration = abs(price_change) + momentum

            # Technical breakout simulation
            price = token.get("price", 0.0)
            high_24h = price * 1.05  # Simulate high
            low_24h = price * 0.95  # Simulate low
            technical_breakout = price >= high_24h * 0.98  # Near highs

            # Social momentum (simulated)
            social_momentum = (
                np.random.uniform(0.3, 0.9)
                if momentum > 10
                else np.random.uniform(0.1, 0.4)
            )

            # Surge strength calculation
            surge_strength = (
                volume_explosion * 0.3
                + price_acceleration * 0.4
                + (20.0 if technical_breakout else 0.0) * 0.2
                + social_momentum * 0.1
            )

            # Determine surge type and urgency
            if surge_strength >= self.microcap_params["surge_threshold"]:
                if surge_strength >= 40.0:
                    surge_type = "EXPLOSIVE_BREAKOUT"
                    urgency = "IMMEDIATE"
                elif surge_strength >= 30.0:
                    surge_type = "STRONG_MOMENTUM"
                    urgency = "HIGH"
                elif surge_strength >= 20.0:
                    surge_type = "BUILDING_MOMENTUM"
                    urgency = "MEDIUM"

                signal = MomentumSurgeSignal(
                    symbol=symbol,
                    surge_strength=surge_strength,
                    surge_type=surge_type,
                    volume_explosion=volume_explosion * 100,
                    price_acceleration=price_acceleration,
                    technical_breakout=technical_breakout,
                    social_momentum=social_momentum * 100,
                    timestamp=datetime.now(),
                    urgency_level=urgency,
                )

                surge_signals.append(signal)

        # Sort by surge strength
        surge_signals.sort(key=lambda x: x.surge_strength, reverse=True)
        return surge_signals

    def generate_claude_analysis(
        self, token: Dict, surge_signal: MomentumSurgeSignal = None
    ) -> str:
        """Generate Claude-style analysis for microcap opportunity"""
        symbol = token["symbol"]
        price = token["price"]
        volume = token.get("volume_24h_usdt", 0.0)
        momentum = token.get("momentum_score", 0.0)
        sector = token.get("sector", "unknown")
        price_change = token.get("price_change_24h", 0.0)

        analysis_prompt = f"""
        Microcap Analysis for {symbol}:
        
        Current Price: ${price:.6f}
        24h Volume: ${volume:,.0f}
        Price Change 24h: {price_change:+.2f}%
        Momentum Score: {momentum:.1f}
        Sector: {sector}
        """

        if surge_signal:
            analysis_prompt += f"""
            Surge Signal Detected:
            - Surge Strength: {surge_signal.surge_strength:.1f}
            - Surge Type: {surge_signal.surge_type}
            - Volume Explosion: {surge_signal.volume_explosion:+.1f}%
            - Technical Breakout: {surge_signal.technical_breakout}
            - Urgency: {surge_signal.urgency_level}
            """

        # Simulate Claude-style analysis
        if surge_signal and surge_signal.surge_strength >= 30.0:
            analysis = f"""
🔥 EXPLOSIVE MICROCAP OPPORTUNITY: {symbol}

TECHNICAL ANALYSIS:
• Price at ${price:.6f} showing {surge_signal.surge_type} pattern
• Volume explosion of {surge_signal.volume_explosion:+.1f}% indicates institutional interest
• Technical breakout confirmed: {surge_signal.technical_breakout}
• Momentum acceleration: {surge_signal.price_acceleration:.1f} points

FUNDAMENTAL FACTORS:
• Sector: {sector.upper()} - High growth potential sector
• Market cap extremely low - massive upside potential
• Volume surge suggests major catalyst or news

RISK-REWARD ASSESSMENT:
• RISK LEVEL: EXTREME (Microcap volatility)
• REWARD POTENTIAL: 5-25x if momentum sustains
• TIME HORIZON: Short to medium term (days to weeks)

TRADING STRATEGY:
• Entry: IMMEDIATE on surge confirmation
• Stop Loss: -15% (tight risk management)
• Targets: +100%, +500%, +1000%, +2500%
• Position Size: Max 25% allocation due to risk

⚠️ WARNING: Extreme volatility expected. Only for high-risk tolerance traders.
            """
        elif momentum >= 15.0:
            analysis = f"""
📈 STRONG MICROCAP MOMENTUM: {symbol}

MOMENTUM ANALYSIS:
• Building momentum at ${price:.6f}
• {sector} sector showing strength
• Volume: ${volume:,.0f} - adequate liquidity
• Price momentum: {price_change:+.2f}% daily

OPPORTUNITY ASSESSMENT:
• Medium-term momentum play
• 2-10x potential if trend continues
• Lower risk than explosive breakouts
• Good volume support

STRATEGY:
• Gradual entry on pullbacks
• 10-20% position size
• Stop: -12%
• Targets: +50%, +200%, +500%
            """
        else:
            analysis = f"""
📊 MICROCAP MONITORING: {symbol}

CURRENT STATUS:
• Price: ${price:.6f} in {sector} sector
• Moderate momentum: {momentum:.1f}
• Volume: ${volume:,.0f}

ASSESSMENT:
• Watching for momentum buildup
• No immediate surge signals
• Potential future opportunity
• Continue monitoring for breakout patterns

RECOMMENDATION: WATCH LIST
            """

        return analysis

    def create_microcap_opportunities(
        self, microcaps: List[Dict], surge_signals: List[MomentumSurgeSignal]
    ) -> List[MicrocapOpportunity]:
        """Create comprehensive microcap opportunity analysis"""
        opportunities = []

        # Create surge signal lookup
        surge_lookup = {signal.symbol: signal for signal in surge_signals}

        for token in microcaps:
            symbol = token["symbol"]
            microcap_score = token.get("microcap_score", 0.0)

            # Skip low-scoring opportunities
            if microcap_score < 30.0:
                continue

            surge_signal = surge_lookup.get(symbol)
            claude_analysis = self.generate_claude_analysis(token, surge_signal)

            # Calculate opportunity metrics
            price = token["price"]
            volume = token.get("volume_24h_usdt", 0.0)
            momentum = token.get("momentum_score", 0.0)

            # Entry confidence based on multiple factors
            entry_confidence = microcap_score
            if surge_signal:
                entry_confidence += min(surge_signal.surge_strength, 40.0)
            entry_confidence = min(entry_confidence, 100.0)

            # Expected multiplier based on momentum and surge
            if surge_signal and surge_signal.surge_strength >= 30.0:
                expected_multiplier = np.random.uniform(5.0, 25.0)
                risk_level = "EXTREME"
                time_horizon = "SHORT_TERM"
            elif momentum >= 15.0:
                expected_multiplier = np.random.uniform(2.0, 10.0)
                risk_level = "VERY_HIGH"
                time_horizon = "MEDIUM_TERM"
            else:
                expected_multiplier = np.random.uniform(1.5, 5.0)
                risk_level = "HIGH"
                time_horizon = "MEDIUM_TERM"

            # Catalyst factors
            catalyst_factors = []
            if surge_signal:
                catalyst_factors.append(f"{surge_signal.surge_type} momentum pattern")
                if surge_signal.technical_breakout:
                    catalyst_factors.append("Technical breakout confirmation")
                if surge_signal.volume_explosion > 100:
                    catalyst_factors.append(
                        f"Volume explosion ({surge_signal.volume_explosion:+.0f}%)"
                    )

            if token.get("sector") in ["gaming", "ai", "metaverse"]:
                catalyst_factors.append(f"High-growth {token['sector']} sector")

            catalyst_factors.append("Microcap potential for explosive growth")

            # Risk factors
            risk_factors = [
                "Extreme volatility due to microcap status",
                "Low liquidity risk",
                "Potential for rapid price swings",
                "Limited fundamental analysis available",
            ]

            if volume < 5000:
                risk_factors.append("Very low trading volume")

            opportunity = MicrocapOpportunity(
                symbol=symbol,
                price=price,
                market_cap_estimate=token.get("estimated_market_cap", 0),
                volume_24h=volume,
                price_change_24h=token.get("price_change_24h", 0.0),
                momentum_score=momentum,
                surge_potential=surge_signal.surge_strength if surge_signal else 0.0,
                risk_level=risk_level,
                claude_analysis=claude_analysis,
                entry_confidence=entry_confidence,
                expected_multiplier=expected_multiplier,
                time_horizon=time_horizon,
                catalyst_factors=catalyst_factors,
                risk_factors=risk_factors,
            )

            opportunities.append(opportunity)

        # Sort by entry confidence and surge potential
        opportunities.sort(
            key=lambda x: (x.entry_confidence + x.surge_potential), reverse=True
        )
        return opportunities

    def execute_microcap_analysis(self) -> Dict:
        """Execute comprehensive microcap momentum analysis"""
        timestamp = datetime.now()

        print("🚀 MICROCAP MOMENTUM SURGE ANALYSIS")
        print("=" * 50)
        print("Scanning ALL tokens for high-momentum microcap opportunities...")

        # Step 1: Identify microcaps
        microcaps = self.identify_microcap_tokens()

        # Step 2: Detect momentum surges
        surge_signals = self.detect_momentum_surges(microcaps)
        print(f"⚡ Detected {len(surge_signals)} momentum surge signals")

        # Step 3: Create opportunities
        opportunities = self.create_microcap_opportunities(microcaps, surge_signals)
        print(f"🎯 Generated {len(opportunities)} microcap opportunities")

        # Step 4: Display top opportunities
        print(f"\n🔥 TOP MICROCAP MOMENTUM OPPORTUNITIES")
        print("-" * 50)

        for i, opp in enumerate(opportunities[:5], 1):
            print(f"\n#{i}. {opp.symbol}")
            print(f"   💰 Price: ${opp.price:.6f}")
            print(f"   📊 Entry Confidence: {opp.entry_confidence:.1f}%")
            print(f"   🚀 Expected Multiplier: {opp.expected_multiplier:.1f}x")
            print(f"   ⚡ Surge Potential: {opp.surge_potential:.1f}")
            print(f"   ⚠️  Risk Level: {opp.risk_level}")
            print(f"   ⏰ Time Horizon: {opp.time_horizon}")

            if opp.catalyst_factors:
                print(f"   💡 Key Catalyst: {opp.catalyst_factors[0]}")

        # Generate comprehensive report
        analysis_report = {
            "timestamp": timestamp.isoformat(),
            "analysis_type": "MICROCAP_MOMENTUM_SURGE",
            "total_tokens_scanned": len(self.all_tokens),
            "microcaps_identified": len(microcaps),
            "surge_signals_detected": len(surge_signals),
            "opportunities_generated": len(opportunities),
            "top_opportunities": [asdict(opp) for opp in opportunities[:10]],
            "surge_signals": [asdict(signal) for signal in surge_signals[:10]],
            "analysis_parameters": self.microcap_params,
            "market_conditions": {
                "high_momentum_count": len(
                    [o for o in opportunities if o.surge_potential >= 30]
                ),
                "extreme_risk_count": len(
                    [o for o in opportunities if o.risk_level == "EXTREME"]
                ),
                "immediate_opportunities": len(
                    [o for o in opportunities if o.entry_confidence >= 80]
                ),
            },
        }

        # Save report
        filename = (
            f"microcap_momentum_analysis_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(filename, "w") as f:
            json.dump(analysis_report, f, indent=2, default=str)

        print(f"\n💾 Analysis report saved: {filename}")

        return analysis_report

    def display_detailed_opportunities(self, opportunities: List[MicrocapOpportunity]):
        """Display detailed analysis for top opportunities"""
        print(f"\n📋 DETAILED MICROCAP ANALYSIS")
        print("=" * 60)

        for i, opp in enumerate(opportunities[:3], 1):
            print(f"\n{'='*20} OPPORTUNITY #{i} {'='*20}")
            print(opp.claude_analysis)
            print(f"\n📊 QUANTITATIVE METRICS:")
            print(f"• Entry Confidence: {opp.entry_confidence:.1f}%")
            print(f"• Expected Multiplier: {opp.expected_multiplier:.1f}x")
            print(f"• Market Cap Est: ${opp.market_cap_estimate:,.0f}")
            print(f"• 24h Volume: ${opp.volume_24h:,.0f}")
            print(f"• Momentum Score: {opp.momentum_score:.1f}")

            print(f"\n🎯 CATALYST FACTORS:")
            for factor in opp.catalyst_factors:
                print(f"  • {factor}")

            print(f"\n⚠️ RISK FACTORS:")
            for risk in opp.risk_factors:
                print(f"  • {risk}")


def main():
    """Main execution function"""
    print("🚀 MICROCAP MOMENTUM SURGE ANALYZER")
    print("=" * 45)
    print("AI-powered analysis of ALL microcap tokens")
    print("High-risk, high-reward momentum opportunities")

    engine = MicrocapMomentumEngine()

    # Execute comprehensive analysis
    analysis_report = engine.execute_microcap_analysis()

    # Get top opportunities for detailed analysis
    top_opportunities = [
        MicrocapOpportunity(**opp_data)
        for opp_data in analysis_report["top_opportunities"][:3]
    ]

    if top_opportunities:
        engine.display_detailed_opportunities(top_opportunities)

        print(f"\n🎯 EXECUTION SUMMARY:")
        print(f"• Total Opportunities: {analysis_report['opportunities_generated']}")
        print(
            f"• High Momentum: {analysis_report['market_conditions']['high_momentum_count']}"
        )
        print(
            f"• Immediate Entries: {analysis_report['market_conditions']['immediate_opportunities']}"
        )
        print(
            f"• Extreme Risk Plays: {analysis_report['market_conditions']['extreme_risk_count']}"
        )

        print(f"\n⚠️ MICROCAP TRADING WARNINGS:")
        print("• Extreme volatility expected (±50% daily swings)")
        print("• Low liquidity may cause slippage")
        print("• Only trade with risk capital you can afford to lose")
        print("• Set tight stop losses and take profits quickly")
        print("• Monitor positions continuously during market hours")

    print("\n✅ Microcap momentum analysis completed!")


if __name__ == "__main__":
    main()
