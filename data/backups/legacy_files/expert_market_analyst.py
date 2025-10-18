#!/usr/bin/env python3
"""
Expert-Level Market Analysis System
Comprehensive analysis mimicking Claude's analytical style using advanced algorithms
"""

import os
import json
from datetime import datetime
from typing import Dict, List
import numpy as np


class ExpertMarketAnalyst:
    def __init__(self):
        print("🧠 Expert Market Analyst initialized - Advanced AI-style analysis")

    def load_latest_market_data(self) -> Dict:
        """Load the most recent comprehensive market analysis"""
        try:
            import glob

            files = glob.glob("expanded_all_tokens_analysis_*.json")
            if not files:
                files = glob.glob("enhanced_market_analysis_*.json")

            if not files:
                print("❌ No recent market analysis files found")
                return {}

            latest_file = max(files)
            print(f"📊 Loading market data from: {latest_file}")

            with open(latest_file, "r") as f:
                return json.load(f)

        except Exception as e:
            print(f"Error loading market data: {e}")
            return {}

    def get_current_portfolio(self) -> Dict:
        """Get current portfolio status"""
        try:
            from binance.client import Client
            from dotenv import load_dotenv

            load_dotenv()

            client = Client(
                api_key=os.getenv("BINANCEUS_KEY"),
                api_secret=os.getenv("BINANCEUS_SECRET"),
                tld="us",
            )

            account = client.get_account()
            portfolio = {"positions": {}, "total_value": 0}

            for balance in account["balances"]:
                free = float(balance["free"])
                locked = float(balance["locked"])
                total = free + locked

                if total > 0:
                    if balance["asset"] == "USDT":
                        portfolio["positions"][balance["asset"]] = {
                            "amount": total,
                            "usd_value": total,
                            "daily_change": 0,
                        }
                        portfolio["total_value"] += total
                    else:
                        try:
                            symbol = balance["asset"] + "USDT"
                            ticker = client.get_ticker(symbol=symbol)
                            price = float(ticker["lastPrice"])
                            usd_value = total * price
                            daily_change = float(ticker["priceChangePercent"])

                            portfolio["positions"][balance["asset"]] = {
                                "amount": total,
                                "usd_value": usd_value,
                                "daily_change": daily_change,
                            }
                            portfolio["total_value"] += usd_value
                        except:
                            continue

            return portfolio
        except Exception as e:
            print(f"Error getting portfolio: {e}")
            return {"positions": {}, "total_value": 0}

    def analyze_market_cycle_phase(self, market_data: Dict) -> Dict:
        """Analyze what phase of the market cycle we're in"""

        market_summary = market_data.get("market_summary", {})
        perf = market_summary.get("market_performance", {})
        momentum = market_summary.get("momentum_analysis", {})
        volume = market_summary.get("volume_analysis", {})

        avg_change = perf.get("avg_change", 0)
        positive_ratio = perf.get("positive_ratio", 0.5)
        high_momentum_count = momentum.get("high_momentum_count", 0)
        exceptional_momentum = momentum.get("exceptional_momentum_count", 0)

        # Cycle phase analysis
        if exceptional_momentum > 5 and avg_change > 5:
            phase = "euphoria"
            description = "Market in euphoric phase - extreme caution needed"
            risk_level = "extreme"
        elif high_momentum_count > 20 and avg_change > 3:
            phase = "bull_run"
            description = "Strong bull market - good time for aggressive positioning"
            risk_level = "medium"
        elif positive_ratio > 0.6 and avg_change > 0:
            phase = "recovery"
            description = "Market in recovery phase - selective opportunities emerging"
            risk_level = "low"
        elif positive_ratio > 0.4:
            phase = "consolidation"
            description = "Market consolidating - range-bound trading"
            risk_level = "low"
        elif avg_change < -2:
            phase = "bear_market"
            description = "Bear market conditions - focus on capital preservation"
            risk_level = "high"
        else:
            phase = "uncertainty"
            description = "Mixed signals - cautious approach recommended"
            risk_level = "medium"

        return {
            "phase": phase,
            "description": description,
            "risk_level": risk_level,
            "confidence": self.calculate_analysis_confidence(market_data),
        }

    def calculate_analysis_confidence(self, market_data: Dict) -> float:
        """Calculate confidence level in market analysis"""

        total_tokens = market_data.get("total_tokens_analyzed", 0)
        volume_breakdown = market_data.get("volume_breakdown", {})
        high_volume_count = volume_breakdown.get(
            "high_volume", 0
        ) + volume_breakdown.get("ultra_high_volume", 0)

        # Confidence based on data quality
        confidence = 0.5  # Base confidence

        # More tokens analyzed = higher confidence
        if total_tokens > 150:
            confidence += 0.2
        elif total_tokens > 100:
            confidence += 0.1

        # More high-volume tokens = higher confidence
        if high_volume_count > 10:
            confidence += 0.2
        elif high_volume_count > 5:
            confidence += 0.1

        # Market consistency check
        market_summary = market_data.get("market_summary", {})
        positive_ratio = market_summary.get("market_performance", {}).get(
            "positive_ratio", 0.5
        )
        if 0.3 < positive_ratio < 0.7:
            confidence += 0.1  # Mixed market reduces confidence
        else:
            confidence += 0.2  # Clear directional bias increases confidence

        return min(confidence, 1.0)

    def evaluate_trading_opportunities(self, market_data: Dict) -> Dict:
        """Evaluate and rank trading opportunities"""

        top_opportunities = market_data.get("top_opportunities", {})
        momentum_leaders = top_opportunities.get("momentum_leaders", [])
        balanced_opportunities = top_opportunities.get("balanced_opportunities", [])
        hidden_gems = market_data.get("hidden_gems", [])

        # Categorize opportunities by risk/reward
        opportunities = {
            "high_conviction": [],
            "moderate_conviction": [],
            "speculative": [],
            "avoid": [],
        }

        for token in momentum_leaders[:10]:
            momentum = token.get("momentum_score", 0)
            volume = token.get("volume_24h", 0)
            change = token.get("daily_change", 0)

            if momentum > 80 and volume > 100000 and change > 3:
                opportunities["high_conviction"].append(
                    {
                        "token": token["token"],
                        "reasoning": f"Strong momentum ({momentum:.0f}), high volume (${volume:,.0f}), solid gains ({change:+.1f}%)",
                        "score": momentum + (volume / 10000) + (change * 2),
                    }
                )
            elif momentum > 60 and volume > 50000:
                opportunities["moderate_conviction"].append(
                    {
                        "token": token["token"],
                        "reasoning": f"Good momentum ({momentum:.0f}), decent volume (${volume:,.0f})",
                        "score": momentum + (volume / 20000) + change,
                    }
                )
            elif volume < 10000:
                opportunities["avoid"].append(
                    {
                        "token": token["token"],
                        "reasoning": f"Low liquidity risk (${volume:,.0f} volume)",
                        "score": 0,
                    }
                )
            else:
                opportunities["speculative"].append(
                    {
                        "token": token["token"],
                        "reasoning": f"Mixed signals - momentum {momentum:.0f}, volume ${volume:,.0f}",
                        "score": momentum / 2,
                    }
                )

        # Sort by score within each category
        for category in opportunities:
            opportunities[category].sort(key=lambda x: x.get("score", 0), reverse=True)

        return opportunities

    def analyze_portfolio_positioning(
        self, portfolio_data: Dict, market_data: Dict
    ) -> Dict:
        """Analyze current portfolio positioning"""

        positions = portfolio_data.get("positions", {})
        total_value = portfolio_data.get("total_value", 0)

        # Get performance of current holdings
        all_tokens = market_data.get("all_tokens", [])
        token_lookup = {token["token"]: token for token in all_tokens}

        portfolio_analysis = {
            "cash_position": 0,
            "winning_positions": [],
            "losing_positions": [],
            "momentum_analysis": {},
            "diversification_score": 0,
            "risk_assessment": "unknown",
        }

        if total_value > 0:
            usdt_value = positions.get("USDT", {}).get("usd_value", 0)
            portfolio_analysis["cash_position"] = (usdt_value / total_value) * 100

            for asset, data in positions.items():
                if asset == "USDT":
                    continue

                daily_change = data.get("daily_change", 0)
                usd_value = data.get("usd_value", 0)
                weight = (usd_value / total_value) * 100

                position_data = {
                    "asset": asset,
                    "weight": weight,
                    "daily_change": daily_change,
                    "usd_value": usd_value,
                }

                # Get momentum data if available
                if asset in token_lookup:
                    token_data = token_lookup[asset]
                    position_data["momentum_score"] = token_data.get(
                        "momentum_score", 0
                    )
                    portfolio_analysis["momentum_analysis"][asset] = token_data.get(
                        "momentum_score", 0
                    )

                if daily_change > 0:
                    portfolio_analysis["winning_positions"].append(position_data)
                else:
                    portfolio_analysis["losing_positions"].append(position_data)

            # Calculate diversification score
            position_count = len([p for p in positions.keys() if p != "USDT"])
            max_weight = max(
                [
                    data.get("usd_value", 0) / total_value
                    for data in positions.values()
                    if isinstance(data, dict)
                ]
            )

            if position_count > 5 and max_weight < 0.4:
                portfolio_analysis["diversification_score"] = "well_diversified"
            elif position_count > 3 and max_weight < 0.6:
                portfolio_analysis["diversification_score"] = "moderately_diversified"
            else:
                portfolio_analysis["diversification_score"] = "concentrated"

        return portfolio_analysis

    def generate_expert_recommendations(
        self, market_data: Dict, portfolio_data: Dict
    ) -> Dict:
        """Generate expert-level trading recommendations"""

        cycle_analysis = self.analyze_market_cycle_phase(market_data)
        opportunities = self.evaluate_trading_opportunities(market_data)
        portfolio_analysis = self.analyze_portfolio_positioning(
            portfolio_data, market_data
        )

        recommendations = {
            "immediate_actions": [],
            "strategic_positioning": [],
            "risk_management": [],
            "system_optimization": [],
            "market_timing": [],
        }

        # Immediate actions based on market phase
        if cycle_analysis["phase"] == "recovery":
            recommendations["immediate_actions"].extend(
                [
                    "Consider deploying some cash into high-conviction opportunities",
                    "Monitor momentum leaders for breakout signals",
                    "Maintain current winning positions",
                ]
            )
        elif cycle_analysis["phase"] == "consolidation":
            recommendations["immediate_actions"].extend(
                [
                    "Hold current profitable positions",
                    "Avoid new positions unless exceptional momentum emerges",
                    "Consider taking partial profits on large gains",
                ]
            )
        elif cycle_analysis["phase"] == "bear_market":
            recommendations["immediate_actions"].extend(
                [
                    "Reduce risk exposure immediately",
                    "Increase cash position",
                    "Set tight stop losses on remaining positions",
                ]
            )

        # Strategic positioning
        cash_pct = portfolio_analysis.get("cash_position", 0)
        if cash_pct > 50:
            recommendations["strategic_positioning"].append(
                f"High cash position ({cash_pct:.1f}%) - consider gradual deployment into quality opportunities"
            )
        elif cash_pct < 20:
            recommendations["strategic_positioning"].append(
                f"Low cash position ({cash_pct:.1f}%) - consider taking some profits to build reserves"
            )

        # System optimization
        market_summary = market_data.get("market_summary", {})
        high_momentum_count = market_summary.get("momentum_analysis", {}).get(
            "high_momentum_count", 0
        )
        exceptional_count = market_summary.get("momentum_analysis", {}).get(
            "exceptional_momentum_count", 0
        )

        if exceptional_count == 0 and high_momentum_count < 5:
            recommendations["system_optimization"].extend(
                [
                    "Consider lowering momentum thresholds - current market shows low overall momentum",
                    "Focus on volume-weighted opportunities rather than pure momentum",
                    "Implement more nuanced opportunity scoring",
                ]
            )

        return recommendations

    def generate_comprehensive_analysis(self) -> Dict:
        """Generate comprehensive expert analysis"""

        print("🧠 GENERATING EXPERT-LEVEL COMPREHENSIVE ANALYSIS")
        print("=" * 60)

        # Load data
        market_data = self.load_latest_market_data()
        if not market_data:
            print("❌ No market data available")
            return {}

        portfolio_data = self.get_current_portfolio()

        # Perform analysis
        cycle_analysis = self.analyze_market_cycle_phase(market_data)
        opportunities = self.evaluate_trading_opportunities(market_data)
        portfolio_analysis = self.analyze_portfolio_positioning(
            portfolio_data, market_data
        )
        recommendations = self.generate_expert_recommendations(
            market_data, portfolio_data
        )

        # Display results
        self.display_expert_analysis(
            market_data,
            cycle_analysis,
            opportunities,
            portfolio_analysis,
            recommendations,
        )

        # Create comprehensive report
        report = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "expert_comprehensive",
            "market_data_summary": {
                "total_tokens": market_data.get("total_tokens_analyzed", 0),
                "sentiment": market_data.get("market_summary", {}).get(
                    "sentiment", "unknown"
                ),
                "avg_change": market_data.get("market_summary", {})
                .get("market_performance", {})
                .get("avg_change", 0),
                "momentum_leaders_count": len(
                    market_data.get("top_opportunities", {}).get("momentum_leaders", [])
                ),
            },
            "market_cycle_analysis": cycle_analysis,
            "trading_opportunities": opportunities,
            "portfolio_analysis": portfolio_analysis,
            "expert_recommendations": recommendations,
            "analysis_confidence": cycle_analysis.get("confidence", 0.5),
        }

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"expert_comprehensive_analysis_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Expert analysis saved: {filename}")

        return report

    def display_expert_analysis(
        self,
        market_data: Dict,
        cycle_analysis: Dict,
        opportunities: Dict,
        portfolio_analysis: Dict,
        recommendations: Dict,
    ):
        """Display comprehensive expert analysis"""

        print("\n🧠 EXPERT MARKET ANALYSIS")
        print("=" * 50)

        # Market cycle analysis
        print(f"📊 MARKET CYCLE ANALYSIS:")
        print(f"   Phase: {cycle_analysis['phase'].upper()}")
        print(f"   Description: {cycle_analysis['description']}")
        print(f"   Risk Level: {cycle_analysis['risk_level'].upper()}")
        print(f"   Analysis Confidence: {cycle_analysis['confidence']:.1%}")

        # Market overview
        market_summary = market_data.get("market_summary", {})
        perf = market_summary.get("market_performance", {})
        momentum = market_summary.get("momentum_analysis", {})

        print(f"\n📈 MARKET METRICS:")
        print(
            f"   Total Tokens Analyzed: {market_data.get('total_tokens_analyzed', 0)}"
        )
        print(f"   Average Change: {perf.get('avg_change', 0):+.2f}%")
        print(f"   Positive Ratio: {perf.get('positive_ratio', 0):.1%}")
        print(f"   High Momentum Count: {momentum.get('high_momentum_count', 0)}")
        print(
            f"   Exceptional Momentum: {momentum.get('exceptional_momentum_count', 0)}"
        )

        # Trading opportunities
        print(f"\n🎯 TRADING OPPORTUNITIES:")

        high_conv = opportunities.get("high_conviction", [])
        if high_conv:
            print(f"   HIGH CONVICTION ({len(high_conv)}):")
            for opp in high_conv[:3]:
                print(f"     • {opp['token']}: {opp['reasoning']}")

        mod_conv = opportunities.get("moderate_conviction", [])
        if mod_conv:
            print(f"   MODERATE CONVICTION ({len(mod_conv)}):")
            for opp in mod_conv[:3]:
                print(f"     • {opp['token']}: {opp['reasoning']}")

        avoid = opportunities.get("avoid", [])
        if avoid:
            print(f"   AVOID ({len(avoid)}): {[opp['token'] for opp in avoid[:5]]}")

        # Portfolio analysis
        print(f"\n💼 PORTFOLIO ANALYSIS:")
        print(f"   Cash Position: {portfolio_analysis.get('cash_position', 0):.1f}%")
        print(
            f"   Winning Positions: {len(portfolio_analysis.get('winning_positions', []))}"
        )
        print(
            f"   Losing Positions: {len(portfolio_analysis.get('losing_positions', []))}"
        )
        print(
            f"   Diversification: {portfolio_analysis.get('diversification_score', 'unknown')}"
        )

        # Recommendations
        print(f"\n💡 EXPERT RECOMMENDATIONS:")

        for category, recs in recommendations.items():
            if recs:
                print(f"   {category.upper().replace('_', ' ')}:")
                for rec in recs:
                    print(f"     • {rec}")


def main():
    analyst = ExpertMarketAnalyst()
    report = analyst.generate_comprehensive_analysis()


if __name__ == "__main__":
    main()
