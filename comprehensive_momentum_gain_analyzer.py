#!/usr/bin/env python3

"""
📈 COMPREHENSIVE MOMENTUM GAIN ANALYSIS
Complete analysis of momentum patterns and potential gains for all tokens
Advanced AI-driven momentum scoring with profit prediction system
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import statistics
import numpy as np
from dataclasses import dataclass, asdict
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
class MomentumAnalysis:
    """Comprehensive momentum analysis for a token"""

    symbol: str
    current_price: float
    price_change_24h: float
    volume_24h: float
    momentum_score: float
    momentum_category: str
    momentum_strength: str
    gain_potential_1w: float
    gain_potential_1m: float
    gain_potential_3m: float
    confidence_score: float
    risk_level: str
    sector: str
    market_cap_category: str
    liquidity_rating: str
    volatility_rating: str
    trend_direction: str
    support_strength: float
    resistance_strength: float
    breakout_probability: float
    recommended_action: str
    position_size: float
    entry_strategy: str
    exit_strategy: str
    momentum_indicators: Dict
    ai_prediction: str


class ComprehensiveMomentumAnalyzer:
    """Advanced momentum analyzer for all tokens"""

    def __init__(self):
        # Initialize Binance client
        self.BINANCEUS_KEY = os.getenv("BINANCEUS_KEY")
        self.BINANCEUS_SECRET = os.getenv("BINANCEUS_SECRET")
        self.client = None

        if binance_available and self.BINANCEUS_KEY:
            try:
                self.client = Client(self.BINANCEUS_KEY, self.BINANCEUS_SECRET)
                print("✅ Comprehensive Momentum Analyzer connected to Binance")
            except Exception as e:
                print(f"⚠️ Binance client error: {e}")

        # Load all token data
        self.all_tokens = self._load_all_token_data()

        # Momentum analysis parameters
        self.momentum_weights = {
            "price_momentum": 0.25,
            "volume_momentum": 0.20,
            "volatility_factor": 0.15,
            "trend_consistency": 0.15,
            "sector_strength": 0.10,
            "liquidity_factor": 0.10,
            "technical_indicators": 0.05,
        }

        # Gain prediction models
        self.gain_models = {
            "conservative": {"multiplier": 1.2, "timeframe": "1-2 weeks"},
            "moderate": {"multiplier": 1.5, "timeframe": "2-4 weeks"},
            "aggressive": {"multiplier": 2.0, "timeframe": "1-2 months"},
            "ultra_aggressive": {"multiplier": 3.0, "timeframe": "2-3 months"},
        }

    def _load_all_token_data(self) -> List[Dict]:
        """Load all available token data"""
        try:
            with open("comprehensive_token_analysis_20250805_155947.json", "r") as f:
                data = json.load(f)
                print(f"📊 Loaded {len(data)} tokens for analysis")
                return data
        except FileNotFoundError:
            print("⚠️ Comprehensive token analysis file not found")
            return []

    def calculate_momentum_score(self, token: Dict) -> float:
        """Calculate comprehensive momentum score (0-10)"""

        price_change = token.get("price_change_24h", 0)
        volume = token.get("volume_24h_usdt", 0)
        volatility = token.get("volatility", 0)
        momentum_score = token.get("momentum_score", 0)

        # Price momentum component (0-2.5)
        if price_change > 10:
            price_momentum = 2.5
        elif price_change > 5:
            price_momentum = 2.0
        elif price_change > 2:
            price_momentum = 1.5
        elif price_change > 0:
            price_momentum = 1.0
        elif price_change > -3:
            price_momentum = 0.5
        else:
            price_momentum = 0

        # Volume momentum component (0-2.0)
        if volume > 100000:
            volume_momentum = 2.0
        elif volume > 50000:
            volume_momentum = 1.6
        elif volume > 20000:
            volume_momentum = 1.2
        elif volume > 5000:
            volume_momentum = 0.8
        else:
            volume_momentum = 0.4

        # Volatility factor (0-1.5)
        if 0.05 <= volatility <= 0.12:  # Optimal volatility range
            volatility_factor = 1.5
        elif 0.03 <= volatility <= 0.15:
            volatility_factor = 1.2
        elif volatility < 0.02:  # Too stable
            volatility_factor = 0.6
        else:  # Too volatile
            volatility_factor = 0.3

        # Trend consistency (0-1.5)
        trend_consistency = min(momentum_score / 6, 1.5)

        # Sector strength (0-1.0)
        sector = token.get("sector", "general")
        sector_multipliers = {
            "gaming": 1.0,
            "defi": 0.9,
            "layer1": 0.8,
            "nft": 0.7,
            "metaverse": 0.8,
            "meme": 0.6,
            "general": 0.5,
        }
        sector_strength = sector_multipliers.get(sector, 0.5)

        # Liquidity factor (0-1.0)
        liquidity_factor = min(volume / 50000, 1.0)

        # Technical indicators (0-0.5)
        technical_score = 0.3  # Base score (would integrate RSI, MACD, etc.)
        if price_change > 0:
            technical_score += 0.2

        # Calculate weighted score
        total_score = (
            price_momentum * self.momentum_weights["price_momentum"]
            + volume_momentum * self.momentum_weights["volume_momentum"]
            + volatility_factor * self.momentum_weights["volatility_factor"]
            + trend_consistency * self.momentum_weights["trend_consistency"]
            + sector_strength * self.momentum_weights["sector_strength"]
            + liquidity_factor * self.momentum_weights["liquidity_factor"]
            + technical_score * self.momentum_weights["technical_indicators"]
        ) * 10

        return min(total_score, 10.0)

    def predict_gain_potential(
        self, token: Dict, momentum_score: float
    ) -> Tuple[float, float, float]:
        """Predict gain potential for 1 week, 1 month, and 3 months"""

        price = token["price"]
        volatility = token.get("volatility", 0.05)
        volume = token.get("volume_24h_usdt", 0)
        sector = token.get("sector", "general")

        # Base gain calculation
        base_gain = momentum_score / 10  # 0.0 to 1.0

        # Volatility adjustment
        volatility_multiplier = min(
            volatility * 10, 2.0
        )  # Higher volatility = higher potential

        # Volume adjustment
        volume_multiplier = 1.0 + min(
            volume / 100000, 1.0
        )  # Higher volume = higher confidence

        # Sector adjustment
        sector_multipliers = {
            "gaming": 1.3,
            "defi": 1.2,
            "layer1": 1.1,
            "nft": 1.2,
            "metaverse": 1.25,
            "meme": 1.4,
            "general": 1.0,
        }
        sector_multiplier = sector_multipliers.get(sector, 1.0)

        # Time-based predictions
        week_1_gain = (
            base_gain * 0.3 * volatility_multiplier * volume_multiplier
        )  # Conservative
        month_1_gain = (
            base_gain
            * 0.6
            * volatility_multiplier
            * volume_multiplier
            * sector_multiplier
        )
        month_3_gain = (
            base_gain
            * 1.2
            * volatility_multiplier
            * volume_multiplier
            * sector_multiplier
        )

        # Cap maximum gains to realistic levels
        week_1_gain = min(week_1_gain, 0.5)  # Max 50% in 1 week
        month_1_gain = min(month_1_gain, 2.0)  # Max 200% in 1 month
        month_3_gain = min(month_3_gain, 5.0)  # Max 500% in 3 months

        return week_1_gain, month_1_gain, month_3_gain

    def analyze_momentum_indicators(self, token: Dict) -> Dict:
        """Analyze detailed momentum indicators"""

        price_change = token.get("price_change_24h", 0)
        volume = token.get("volume_24h_usdt", 0)
        volatility = token.get("volatility", 0)
        momentum_score = token.get("momentum_score", 0)

        indicators = {}

        # Price action analysis
        if price_change > 5:
            indicators["price_action"] = "STRONG_BULLISH"
        elif price_change > 2:
            indicators["price_action"] = "BULLISH"
        elif price_change > -2:
            indicators["price_action"] = "NEUTRAL"
        elif price_change > -5:
            indicators["price_action"] = "BEARISH"
        else:
            indicators["price_action"] = "STRONG_BEARISH"

        # Volume analysis
        if volume > 100000:
            indicators["volume_strength"] = "VERY_HIGH"
        elif volume > 50000:
            indicators["volume_strength"] = "HIGH"
        elif volume > 20000:
            indicators["volume_strength"] = "MODERATE"
        elif volume > 5000:
            indicators["volume_strength"] = "LOW"
        else:
            indicators["volume_strength"] = "VERY_LOW"

        # Momentum trend
        if momentum_score > 7:
            indicators["momentum_trend"] = "ACCELERATING"
        elif momentum_score > 5.5:
            indicators["momentum_trend"] = "BUILDING"
        elif momentum_score > 4:
            indicators["momentum_trend"] = "STEADY"
        else:
            indicators["momentum_trend"] = "DECLINING"

        # Volatility assessment
        if volatility > 0.15:
            indicators["volatility"] = "EXTREME"
        elif volatility > 0.10:
            indicators["volatility"] = "HIGH"
        elif volatility > 0.05:
            indicators["volatility"] = "MODERATE"
        else:
            indicators["volatility"] = "LOW"

        return indicators

    def generate_trading_recommendation(
        self,
        token: Dict,
        momentum_score: float,
        gain_potential: Tuple[float, float, float],
    ) -> Tuple[str, float, str, str]:
        """Generate trading recommendation"""

        week_1, month_1, month_3 = gain_potential
        price_change = token.get("price_change_24h", 0)
        volume = token.get("volume_24h_usdt", 0)

        # Risk assessment
        if volume < 1000:
            risk = "VERY_HIGH"
        elif volume < 5000:
            risk = "HIGH"
        elif volume < 20000:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        # Action recommendation
        if momentum_score >= 8 and month_1 > 0.5:
            action = "STRONG_BUY"
            position_size = 0.08  # 8%
        elif momentum_score >= 6.5 and month_1 > 0.3:
            action = "BUY"
            position_size = 0.06  # 6%
        elif momentum_score >= 5 and month_1 > 0.2:
            action = "ACCUMULATE"
            position_size = 0.04  # 4%
        elif momentum_score >= 3.5:
            action = "WATCH"
            position_size = 0.02  # 2%
        else:
            action = "AVOID"
            position_size = 0.0

        # Entry strategy
        if price_change > 3:
            entry_strategy = "WAIT_FOR_PULLBACK"
        elif price_change < -3:
            entry_strategy = "BUY_THE_DIP"
        else:
            entry_strategy = "GRADUAL_ACCUMULATION"

        # Exit strategy
        if month_1 > 1.0:  # >100% potential
            exit_strategy = "SCALE_OUT_25_50_75"
        elif month_1 > 0.5:  # >50% potential
            exit_strategy = "SCALE_OUT_50_100"
        else:
            exit_strategy = "CONSERVATIVE_20_40"

        return action, position_size, entry_strategy, exit_strategy

    def analyze_all_tokens(self) -> List[MomentumAnalysis]:
        """Analyze momentum for all tokens"""

        print("🔍 Analyzing momentum for all tokens...")

        analyses = []

        for token in self.all_tokens:
            try:
                # Calculate momentum score
                momentum_score = self.calculate_momentum_score(token)

                # Predict gain potential
                gain_1w, gain_1m, gain_3m = self.predict_gain_potential(
                    token, momentum_score
                )

                # Analyze momentum indicators
                momentum_indicators = self.analyze_momentum_indicators(token)

                # Generate recommendations
                action, position_size, entry_strategy, exit_strategy = (
                    self.generate_trading_recommendation(
                        token, momentum_score, (gain_1w, gain_1m, gain_3m)
                    )
                )

                # Categorize momentum
                if momentum_score >= 8:
                    momentum_category = "EXPLOSIVE"
                    momentum_strength = "VERY_STRONG"
                elif momentum_score >= 6.5:
                    momentum_category = "STRONG"
                    momentum_strength = "STRONG"
                elif momentum_score >= 5:
                    momentum_category = "MODERATE"
                    momentum_strength = "MODERATE"
                elif momentum_score >= 3.5:
                    momentum_category = "WEAK"
                    momentum_strength = "WEAK"
                else:
                    momentum_category = "NEGLIGIBLE"
                    momentum_strength = "VERY_WEAK"

                # Market cap category
                price = token["price"]
                if price < 0.001:
                    market_cap_category = "MICRO"
                elif price < 0.1:
                    market_cap_category = "SMALL"
                elif price < 10:
                    market_cap_category = "MEDIUM"
                else:
                    market_cap_category = "LARGE"

                # Create analysis
                analysis = MomentumAnalysis(
                    symbol=token["symbol"],
                    current_price=token["price"],
                    price_change_24h=token.get("price_change_24h", 0),
                    volume_24h=token.get("volume_24h_usdt", 0),
                    momentum_score=momentum_score,
                    momentum_category=momentum_category,
                    momentum_strength=momentum_strength,
                    gain_potential_1w=gain_1w,
                    gain_potential_1m=gain_1m,
                    gain_potential_3m=gain_3m,
                    confidence_score=min(
                        momentum_score / 10 + token.get("volume_24h_usdt", 0) / 100000,
                        1.0,
                    ),
                    risk_level=self._get_risk_level(token),
                    sector=token.get("sector", "general"),
                    market_cap_category=market_cap_category,
                    liquidity_rating=self._get_liquidity_rating(
                        token.get("volume_24h_usdt", 0)
                    ),
                    volatility_rating=self._get_volatility_rating(
                        token.get("volatility", 0)
                    ),
                    trend_direction=self._get_trend_direction(
                        token.get("price_change_24h", 0)
                    ),
                    support_strength=0.7,  # Simplified
                    resistance_strength=0.6,  # Simplified
                    breakout_probability=min(momentum_score / 15, 1.0),
                    recommended_action=action,
                    position_size=position_size,
                    entry_strategy=entry_strategy,
                    exit_strategy=exit_strategy,
                    momentum_indicators=momentum_indicators,
                    ai_prediction=self._get_ai_prediction(momentum_score, gain_1m),
                )

                analyses.append(analysis)

            except Exception as e:
                print(f"⚠️ Error analyzing {token.get('symbol', 'unknown')}: {e}")

        # Sort by momentum score
        analyses.sort(key=lambda x: x.momentum_score, reverse=True)

        return analyses

    def _get_risk_level(self, token: Dict) -> str:
        """Get risk level for token"""
        volume = token.get("volume_24h_usdt", 0)
        volatility = token.get("volatility", 0)

        if volume < 1000 or volatility > 0.2:
            return "VERY_HIGH"
        elif volume < 5000 or volatility > 0.15:
            return "HIGH"
        elif volume < 20000 or volatility > 0.10:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_liquidity_rating(self, volume: float) -> str:
        """Get liquidity rating"""
        if volume > 100000:
            return "EXCELLENT"
        elif volume > 50000:
            return "GOOD"
        elif volume > 20000:
            return "FAIR"
        elif volume > 5000:
            return "POOR"
        else:
            return "VERY_POOR"

    def _get_volatility_rating(self, volatility: float) -> str:
        """Get volatility rating"""
        if volatility > 0.15:
            return "EXTREME"
        elif volatility > 0.10:
            return "HIGH"
        elif volatility > 0.05:
            return "MODERATE"
        else:
            return "LOW"

    def _get_trend_direction(self, price_change: float) -> str:
        """Get trend direction"""
        if price_change > 5:
            return "STRONG_UP"
        elif price_change > 2:
            return "UP"
        elif price_change > -2:
            return "SIDEWAYS"
        elif price_change > -5:
            return "DOWN"
        else:
            return "STRONG_DOWN"

    def _get_ai_prediction(self, momentum_score: float, gain_1m: float) -> str:
        """Get AI prediction"""
        if momentum_score >= 8 and gain_1m > 0.5:
            return "EXPLOSIVE_GROWTH"
        elif momentum_score >= 6.5 and gain_1m > 0.3:
            return "STRONG_GROWTH"
        elif momentum_score >= 5 and gain_1m > 0.2:
            return "MODERATE_GROWTH"
        elif momentum_score >= 3.5:
            return "SLOW_GROWTH"
        else:
            return "STAGNANT"

    def generate_comprehensive_report(self, analyses: List[MomentumAnalysis]) -> Dict:
        """Generate comprehensive momentum report"""

        # Summary statistics
        total_tokens = len(analyses)
        strong_buy_count = len(
            [a for a in analyses if a.recommended_action == "STRONG_BUY"]
        )
        buy_count = len([a for a in analyses if a.recommended_action == "BUY"])
        explosive_momentum = len(
            [a for a in analyses if a.momentum_category == "EXPLOSIVE"]
        )

        avg_momentum_score = statistics.mean([a.momentum_score for a in analyses])
        avg_gain_potential_1m = statistics.mean([a.gain_potential_1m for a in analyses])

        # Sector analysis
        sector_performance = defaultdict(list)
        for analysis in analyses:
            sector_performance[analysis.sector].append(analysis.momentum_score)

        best_sectors = {}
        for sector, scores in sector_performance.items():
            best_sectors[sector] = {
                "avg_momentum": statistics.mean(scores),
                "token_count": len(scores),
                "max_momentum": max(scores),
            }

        # Top performers
        top_10_momentum = analyses[:10]
        top_10_potential = sorted(
            analyses, key=lambda x: x.gain_potential_1m, reverse=True
        )[:10]

        return {
            "timestamp": datetime.now().isoformat(),
            "analysis_summary": {
                "total_tokens_analyzed": total_tokens,
                "strong_buy_signals": strong_buy_count,
                "buy_signals": buy_count,
                "explosive_momentum_tokens": explosive_momentum,
                "average_momentum_score": round(avg_momentum_score, 2),
                "average_1m_gain_potential": round(avg_gain_potential_1m * 100, 1),
            },
            "sector_analysis": best_sectors,
            "top_10_momentum": [asdict(a) for a in top_10_momentum],
            "top_10_potential": [asdict(a) for a in top_10_potential],
            "all_analyses": [asdict(a) for a in analyses],
        }


def main():
    """Main execution function"""

    print("📈 COMPREHENSIVE MOMENTUM GAIN ANALYSIS")
    print("=" * 70)

    analyzer = ComprehensiveMomentumAnalyzer()

    # Analyze all tokens
    analyses = analyzer.analyze_all_tokens()

    if not analyses:
        print("❌ No token data available for analysis")
        return

    # Generate comprehensive report
    report = analyzer.generate_comprehensive_report(analyses)

    # Print summary
    summary = report["analysis_summary"]
    print(f"\n📊 ANALYSIS SUMMARY")
    print(f"Total Tokens Analyzed: {summary['total_tokens_analyzed']}")
    print(f"Strong Buy Signals: {summary['strong_buy_signals']}")
    print(f"Buy Signals: {summary['buy_signals']}")
    print(f"Explosive Momentum Tokens: {summary['explosive_momentum_tokens']}")
    print(f"Average Momentum Score: {summary['average_momentum_score']}/10")
    print(f"Average 1M Gain Potential: {summary['average_1m_gain_potential']:.1f}%")

    # Print top momentum tokens
    print(f"\n🔥 TOP 10 MOMENTUM TOKENS")
    print("=" * 70)

    for i, analysis in enumerate(report["top_10_momentum"], 1):
        print(f"\n{i}. {analysis['symbol']} - ${analysis['current_price']:.6f}")
        print(
            f"   Momentum Score: {analysis['momentum_score']:.1f}/10 ({analysis['momentum_strength']})"
        )
        print(f"   24h Change: {analysis['price_change_24h']:.2f}%")
        print(
            f"   Gain Potential: 1W: {analysis['gain_potential_1w']*100:.1f}% | 1M: {analysis['gain_potential_1m']*100:.1f}% | 3M: {analysis['gain_potential_3m']*100:.1f}%"
        )
        print(
            f"   Action: {analysis['recommended_action']} ({analysis['position_size']*100:.1f}% allocation)"
        )
        print(
            f"   Volume: ${analysis['volume_24h']:,.0f} ({analysis['liquidity_rating']})"
        )
        print(
            f"   Risk: {analysis['risk_level']} | Sector: {analysis['sector'].title()}"
        )
        print(f"   AI Prediction: {analysis['ai_prediction']}")

    # Print sector analysis
    print(f"\n🏆 SECTOR PERFORMANCE RANKING")
    print("=" * 70)

    sector_data = report["sector_analysis"]
    sorted_sectors = sorted(
        sector_data.items(), key=lambda x: x[1]["avg_momentum"], reverse=True
    )

    for i, (sector, data) in enumerate(sorted_sectors, 1):
        print(
            f"{i}. {sector.title()}: Avg Momentum {data['avg_momentum']:.1f} ({data['token_count']} tokens)"
        )

    # Print top potential gains
    print(f"\n💰 TOP 10 POTENTIAL GAINS (1 Month)")
    print("=" * 70)

    for i, analysis in enumerate(report["top_10_potential"], 1):
        gain_1m = analysis["gain_potential_1m"] * 100
        print(
            f"{i}. {analysis['symbol']}: {gain_1m:.1f}% potential (Momentum: {analysis['momentum_score']:.1f}/10)"
        )

    # Save comprehensive report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"comprehensive_momentum_analysis_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n💾 Comprehensive report saved: {filename}")

    # Investment recommendations
    print(f"\n💡 INVESTMENT RECOMMENDATIONS")
    print("=" * 70)

    strong_buys = [a for a in analyses if a.recommended_action == "STRONG_BUY"]
    buys = [a for a in analyses if a.recommended_action == "BUY"]

    if strong_buys:
        print(f"🔥 IMMEDIATE OPPORTUNITIES (Strong Buy - {len(strong_buys)} tokens):")
        total_allocation = 0
        for token in strong_buys[:5]:  # Top 5
            allocation = token.position_size * 100
            total_allocation += allocation
            print(
                f"   • {token.symbol}: {allocation:.1f}% allocation - {token.gain_potential_1m*100:.1f}% 1M potential"
            )
        print(f"   Total Strong Buy Allocation: {total_allocation:.1f}%")

    if buys:
        print(f"\n📈 ACCUMULATION TARGETS (Buy - {len(buys)} tokens):")
        total_allocation = 0
        for token in buys[:5]:  # Top 5
            allocation = token.position_size * 100
            total_allocation += allocation
            print(
                f"   • {token.symbol}: {allocation:.1f}% allocation - {token.gain_potential_1m*100:.1f}% 1M potential"
            )
        print(f"   Total Buy Allocation: {total_allocation:.1f}%")

    print(f"\n🎯 COMPREHENSIVE MOMENTUM ANALYSIS COMPLETE!")


if __name__ == "__main__":
    main()
