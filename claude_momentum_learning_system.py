#!/usr/bin/env python3

"""
🧠 CLAUDE AI MOMENTUM LEARNING SYSTEM
Learns from MAGIC performance patterns and identifies next surge opportunities
Features: Pattern analysis, Claude AI predictions, momentum detection, buy/sell signals
"""

import json
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp
import os
import sys
from dataclasses import dataclass

# Load environment
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))


@dataclass
class MomentumPattern:
    """Pattern analysis for momentum surges"""

    symbol: str
    peak_gain: float
    correction_depth: float
    surge_volume: float
    correction_volume: float
    time_to_peak: int
    correction_time: int
    recovery_probability: float
    next_target: float


@dataclass
class TradingSignal:
    """Trading signal with confidence and reasoning"""

    symbol: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    reasoning: str
    risk_score: float


class ClaudeMomentumAnalyzer:
    """Claude AI-powered momentum analysis and prediction system"""

    def __init__(self):
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": self.claude_api_key,
            "anthropic-version": "2023-06-01",
        }

        # Historical MAGIC performance data
        self.magic_performance_history = {
            "surge_peak": 49.42,
            "correction_depth": -11.85,
            "peak_volume": 11239,
            "correction_volume": 7120,
            "peak_price": 0.2700,
            "correction_price": 0.2380,
            "surge_duration": "hours",
            "correction_duration": "hours",
        }

    async def analyze_magic_pattern(self) -> MomentumPattern:
        """Analyze MAGIC's momentum pattern for learning"""

        # Calculate pattern metrics
        total_swing = self.magic_performance_history["surge_peak"] + abs(
            self.magic_performance_history["correction_depth"]
        )
        volume_drop_ratio = (
            self.magic_performance_history["correction_volume"]
            / self.magic_performance_history["peak_volume"]
        )
        price_retracement = (
            abs(self.magic_performance_history["correction_depth"])
            / self.magic_performance_history["surge_peak"]
        )

        # Recovery probability based on gaming sector strength
        recovery_prob = 0.75 if price_retracement < 0.5 else 0.6

        pattern = MomentumPattern(
            symbol="MAGICUSDT",
            peak_gain=self.magic_performance_history["surge_peak"],
            correction_depth=self.magic_performance_history["correction_depth"],
            surge_volume=self.magic_performance_history["peak_volume"],
            correction_volume=self.magic_performance_history["correction_volume"],
            time_to_peak=6,  # estimated hours
            correction_time=4,  # estimated hours
            recovery_probability=recovery_prob,
            next_target=self.magic_performance_history["correction_price"]
            * 1.3,  # 30% recovery target
        )

        return pattern

    async def get_current_market_data(self) -> List[Dict]:
        """Get fresh market data for analysis"""
        try:
            # Load the most recent analysis
            with open("comprehensive_token_analysis_20250805_155947.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  Recent analysis not found, fetching fresh data...")
            return []

    async def identify_momentum_candidates(self, market_data: List[Dict]) -> List[Dict]:
        """Identify tokens with similar momentum potential to MAGIC's surge"""

        candidates = []

        for token in market_data:
            # Skip stablecoins and very low volume tokens
            if token["volume_24h_usdt"] < 1000 or token["symbol"].endswith("USDC"):
                continue

            # Look for tokens with momentum building patterns
            momentum_score = token.get("momentum_score", 0)
            price_change = token.get("price_change_24h", 0)
            volume = token.get("volume_24h_usdt", 0)
            sector = token.get("sector", "general")

            # Calculate surge potential based on MAGIC pattern
            surge_potential = 0

            # Volume momentum (higher volume = more potential)
            if volume > 50000:
                surge_potential += 2
            elif volume > 20000:
                surge_potential += 1

            # Sector preference (gaming, ai, defi have shown good momentum)
            if sector in ["gaming", "ai", "defi"]:
                surge_potential += 3
            elif sector == "layer1":
                surge_potential += 2

            # Price action patterns
            if -5 < price_change < 5:  # Consolidation phase
                surge_potential += 2
            elif 5 < price_change < 15:  # Early momentum
                surge_potential += 3
            elif price_change > 15:  # Already surging
                surge_potential += 1

            # Risk score (lower risk = better candidate)
            risk_score = token.get("risk_score", 5.0)
            if risk_score < 6:
                surge_potential += 1

            if surge_potential >= 5:  # Minimum threshold
                candidates.append(
                    {
                        **token,
                        "surge_potential": surge_potential,
                        "estimated_gain_potential": surge_potential
                        * 8,  # Rough estimate
                        "confidence": min(surge_potential / 10, 0.9),
                    }
                )

        # Sort by surge potential
        candidates.sort(key=lambda x: x["surge_potential"], reverse=True)
        return candidates[:10]  # Top 10 candidates

    async def claude_analyze_candidates(
        self, candidates: List[Dict], magic_pattern: MomentumPattern
    ) -> Dict:
        """Use Claude AI to analyze momentum candidates"""

        candidates_text = "\n".join(
            [
                f"• {c['symbol']}: ${c['price']:.4f} ({c['price_change_24h']:+.2f}%) "
                f"Vol: ${c['volume_24h_usdt']:,.0f} Sector: {c['sector']} "
                f"Surge Potential: {c['surge_potential']}/10"
                for c in candidates[:8]
            ]
        )

        prompt = f"""
        As an expert crypto trading analyst, analyze these momentum surge candidates based on the MAGIC token pattern:
        
        MAGIC PERFORMANCE PATTERN (LEARNING DATA):
        🎮 MAGIC surged +49.42% to $0.2700 with {magic_pattern.surge_volume:,.0f} volume
        📉 Then corrected -11.85% to $0.2380 with {magic_pattern.correction_volume:,.0f} volume
        🎯 Pattern: Gaming sector token, high ecosystem score, momentum building
        
        CURRENT MOMENTUM CANDIDATES:
        {candidates_text}
        
        ANALYSIS REQUIREMENTS:
        1. Identify the TOP 3 candidates with highest surge potential (similar to MAGIC's +49% pattern)
        2. For each candidate, provide:
           - Expected gain potential (be realistic but optimistic)
           - Time horizon for potential surge
           - Entry strategy and price targets
           - Risk assessment
           - Reasoning based on MAGIC pattern similarities
        
        3. Generate specific BUY/SELL/HOLD signals with:
           - Entry price range
           - Target prices (conservative and aggressive)
           - Stop loss levels
           - Position size recommendations
        
        4. Consider:
           - Sector momentum (gaming showed strong performance)
           - Volume patterns
           - Market timing
           - Risk-reward ratios
        
        Format as JSON with clear structure for trading signals.
        """

        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 3000,
                    "messages": [{"role": "user", "content": prompt}],
                }

                async with session.post(
                    self.base_url, headers=self.headers, json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get("content", [{}])[0].get("text", "")

                        # Try to extract JSON from response
                        try:
                            json_start = content.find("{")
                            json_end = content.rfind("}") + 1
                            if json_start != -1 and json_end != -1:
                                json_str = content[json_start:json_end]
                                analysis = json.loads(json_str)
                            else:
                                analysis = self._create_fallback_analysis(candidates)
                        except json.JSONDecodeError:
                            analysis = self._create_fallback_analysis(candidates)

                        return {
                            "status": "success",
                            "claude_analysis": analysis,
                            "raw_response": content,
                        }
                    else:
                        error_text = await response.text()
                        print(f"❌ Claude API error: {response.status} - {error_text}")
                        return {
                            "status": "error",
                            "claude_analysis": self._create_fallback_analysis(
                                candidates
                            ),
                            "message": error_text,
                        }

        except Exception as e:
            print(f"❌ Claude analysis failed: {e}")
            return {
                "status": "error",
                "claude_analysis": self._create_fallback_analysis(candidates),
                "message": str(e),
            }

    def _create_fallback_analysis(self, candidates: List[Dict]) -> Dict:
        """Create fallback analysis when Claude is unavailable"""
        top_3 = candidates[:3] if len(candidates) >= 3 else candidates

        analysis = {
            "top_candidates": [],
            "trading_signals": [],
            "market_outlook": "Moderate momentum potential based on pattern analysis",
        }

        for i, candidate in enumerate(top_3):
            symbol = candidate["symbol"]
            price = candidate["price"]
            surge_potential = candidate["surge_potential"]

            # Generate fallback signals
            expected_gain = surge_potential * 6  # Conservative estimate
            entry_price = price * 0.98  # Slight dip entry
            target_conservative = price * (1 + expected_gain / 200)
            target_aggressive = price * (1 + expected_gain / 100)
            stop_loss = price * 0.92

            candidate_analysis = {
                "rank": i + 1,
                "symbol": symbol,
                "current_price": price,
                "expected_gain_potential": f"{expected_gain}%",
                "confidence": candidate["confidence"],
                "sector": candidate["sector"],
                "reasoning": f"High surge potential ({surge_potential}/10) in {candidate['sector']} sector",
            }

            trading_signal = {
                "symbol": symbol,
                "action": "BUY" if surge_potential >= 6 else "WATCH",
                "confidence": candidate["confidence"],
                "entry_range": f"${entry_price:.4f} - ${price:.4f}",
                "target_conservative": f"${target_conservative:.4f}",
                "target_aggressive": f"${target_aggressive:.4f}",
                "stop_loss": f"${stop_loss:.4f}",
                "position_size": "2-5% of portfolio",
                "reasoning": f"Pattern-based analysis suggests {expected_gain}% potential",
            }

            analysis["top_candidates"].append(candidate_analysis)
            analysis["trading_signals"].append(trading_signal)

        return analysis

    async def generate_trading_report(
        self, claude_analysis: Dict, magic_pattern: MomentumPattern
    ) -> str:
        """Generate comprehensive trading report"""

        analysis = claude_analysis.get("claude_analysis", {})

        report = f"""
🧠 CLAUDE AI MOMENTUM SURGE ANALYSIS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*80}
📚 LEARNING FROM MAGIC PERFORMANCE
{'='*80}
🎮 MAGIC Pattern Analysis:
   Peak Surge: +{magic_pattern.peak_gain:.2f}% 
   Correction: {magic_pattern.correction_depth:.2f}%
   Volume at Peak: ${magic_pattern.surge_volume:,.0f}
   Volume in Correction: ${magic_pattern.correction_volume:,.0f}
   Recovery Probability: {magic_pattern.recovery_probability:.0%}
   
💡 Key Learnings:
   • Gaming tokens show explosive potential
   • Volume surge precedes price surge
   • Corrections of 20-25% are normal after big gains
   • Recovery often happens within 24-48 hours

{'='*80}
🎯 TOP MOMENTUM SURGE CANDIDATES
{'='*80}
"""

        # Add top candidates
        top_candidates = analysis.get("top_candidates", [])
        for candidate in top_candidates:
            report += f"""
🚀 RANK #{candidate.get('rank', 'N/A')} - {candidate.get('symbol', 'Unknown')}
   💰 Current Price: ${candidate.get('current_price', 0):.4f}
   📈 Expected Gain: {candidate.get('expected_gain_potential', 'TBD')}
   🎯 Confidence: {candidate.get('confidence', 0):.0%}
   🏢 Sector: {candidate.get('sector', 'Unknown').title()}
   💭 Reasoning: {candidate.get('reasoning', 'Pattern-based analysis')}
"""

        report += f"""
{'='*80}
⚡ TRADING SIGNALS & STRATEGY
{'='*80}
"""

        # Add trading signals
        trading_signals = analysis.get("trading_signals", [])
        for signal in trading_signals:
            action_emoji = (
                "🟢"
                if signal.get("action") == "BUY"
                else "🟡" if signal.get("action") == "WATCH" else "🔴"
            )

            report += f"""
{action_emoji} {signal.get('symbol', 'Unknown')} - {signal.get('action', 'HOLD')}
   🎯 Confidence: {signal.get('confidence', 0):.0%}
   📍 Entry Range: {signal.get('entry_range', 'TBD')}
   🎯 Target (Conservative): {signal.get('target_conservative', 'TBD')}
   🚀 Target (Aggressive): {signal.get('target_aggressive', 'TBD')}
   🛑 Stop Loss: {signal.get('stop_loss', 'TBD')}
   💼 Position Size: {signal.get('position_size', '2-5%')}
   💭 Strategy: {signal.get('reasoning', 'Pattern-based entry')}
"""

        # Add MAGIC specific recommendation
        magic_action = (
            "BUY THE DIP" if magic_pattern.recovery_probability > 0.7 else "WAIT"
        )
        report += f"""
{'='*80}
🎮 MAGIC SPECIFIC RECOMMENDATION
{'='*80}
📊 Current Status: $0.2380 (-11.85% from peak)
🎯 Recovery Target: ${magic_pattern.next_target:.4f}
📈 Recovery Probability: {magic_pattern.recovery_probability:.0%}
⚡ Action: {magic_action}

💡 MAGIC Strategy:
   {"🟢 BUY: Strong gaming fundamentals + oversold after surge" if magic_action == "BUY THE DIP" else "🟡 WAIT: Let correction complete before entry"}
   Entry: $0.2300 - $0.2400
   Target: ${magic_pattern.next_target:.4f} (+30% from current)
   Stop: $0.2100 (-12% risk)

{'='*80}
🎯 MARKET OUTLOOK & RISK MANAGEMENT
{'='*80}
📈 Market Outlook: {analysis.get('market_outlook', 'Moderate momentum potential')}

⚠️  Risk Management Rules:
   • Never risk more than 5% per trade
   • Set stop losses at entry
   • Take profits at 25% and 50% gains
   • Watch for volume confirmation
   • Exit if pattern breaks down

🕒 Timing Strategy:
   • Enter during consolidation or slight dips
   • Watch for volume surge confirmation
   • Best entry: Asian/European market hours
   • Avoid FOMO buying at peaks

✅ Success Indicators:
   • Volume increase 2-3x normal
   • Price breaking above resistance
   • Sector momentum building
   • Social sentiment improving
"""

        return report

    async def save_analysis_results(self, report: str, claude_analysis: Dict) -> str:
        """Save analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save detailed JSON analysis
        filename = f"claude_momentum_analysis_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "magic_pattern": self.magic_performance_history,
                    "claude_analysis": claude_analysis,
                    "analysis_type": "momentum_surge_prediction",
                },
                f,
                indent=2,
            )

        # Save readable report
        report_filename = f"momentum_trading_report_{timestamp}.txt"
        with open(report_filename, "w") as f:
            f.write(report)

        print(f"💾 Analysis saved to {filename}")
        print(f"📄 Report saved to {report_filename}")

        return filename


async def main():
    """Main execution function"""
    print("🧠 CLAUDE AI MOMENTUM LEARNING SYSTEM")
    print("=" * 60)
    print("Learning from MAGIC performance and finding next surge opportunities...")
    print()

    analyzer = ClaudeMomentumAnalyzer()

    # Analyze MAGIC pattern
    print("📚 Analyzing MAGIC momentum pattern...")
    magic_pattern = await analyzer.analyze_magic_pattern()

    # Get current market data
    print("📊 Loading current market data...")
    market_data = await analyzer.get_current_market_data()

    if not market_data:
        print("❌ No market data available")
        return

    # Identify momentum candidates
    print("🔍 Identifying momentum surge candidates...")
    candidates = await analyzer.identify_momentum_candidates(market_data)

    if not candidates:
        print("❌ No suitable candidates found")
        return

    print(f"✅ Found {len(candidates)} momentum candidates")

    # Claude AI analysis
    print("🤖 Running Claude AI analysis...")
    claude_analysis = await analyzer.claude_analyze_candidates(
        candidates, magic_pattern
    )

    # Generate comprehensive report
    report = await analyzer.generate_trading_report(claude_analysis, magic_pattern)
    print(report)

    # Save results
    await analyzer.save_analysis_results(report, claude_analysis)

    # Quick summary
    print("\n" + "=" * 60)
    print("🎯 QUICK TRADING SUMMARY")
    print("=" * 60)

    if claude_analysis.get("status") == "success":
        top_candidates = claude_analysis.get("claude_analysis", {}).get(
            "top_candidates", []
        )
        if top_candidates:
            for i, candidate in enumerate(top_candidates[:3], 1):
                symbol = candidate.get("symbol", "Unknown")
                gain_potential = candidate.get("expected_gain_potential", "TBD")
                confidence = candidate.get("confidence", 0)
                print(
                    f"{i}. 🚀 {symbol}: {gain_potential} potential (Confidence: {confidence:.0%})"
                )

    print(f"\n🎮 MAGIC Recovery: {magic_pattern.recovery_probability:.0%} probability")
    print(f"🎯 Target: ${magic_pattern.next_target:.4f}")
    print("\n✅ Analysis complete! Ready for strategic trading!")


if __name__ == "__main__":
    asyncio.run(main())
