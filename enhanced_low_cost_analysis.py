#!/usr/bin/env python3

"""
🎯 ENHANCED LOW-COST TOKEN ANALYSIS & PREDICTIONS
Advanced AI analysis for tokens in $0.001 - $0.01 range with market intelligence
"""

import json
import os
from datetime import datetime
from typing import Dict, List


def analyze_low_cost_tokens():
    """Enhanced analysis of low-cost tokens with detailed predictions"""

    # Load the prediction report
    try:
        with open("low_cost_token_predictions_20250805_184131.json", "r") as f:
            report = json.load(f)
    except FileNotFoundError:
        print("❌ Prediction report not found")
        return

    tokens = report.get("all_predictions", [])

    print("🔍 ENHANCED LOW-COST TOKEN PREDICTIONS")
    print("=" * 70)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Price Range: $0.001 - $0.01")
    print(f"Total Tokens: {len(tokens)}")

    # Enhanced analysis for each token
    enhanced_predictions = []

    for token in tokens:
        symbol = token["symbol"]
        price = token["price"]
        prediction = token["prediction"]
        confidence = token["confidence"]
        potential_gain = token["potential_gain"]
        volume = token["volume_24h_usdt"]
        change_24h = token["price_change_24h"]

        # Enhanced market intelligence
        market_intelligence = generate_market_intelligence(token)
        risk_assessment = calculate_enhanced_risk(token)
        timing_analysis = analyze_market_timing(token)

        enhanced_token = {
            **token,
            "market_intelligence": market_intelligence,
            "risk_assessment": risk_assessment,
            "timing_analysis": timing_analysis,
            "investment_thesis": generate_investment_thesis(token),
        }

        enhanced_predictions.append(enhanced_token)

    # Print detailed analysis
    print_enhanced_analysis(enhanced_predictions[:5])  # Top 5

    # Generate investment strategy
    generate_portfolio_strategy(enhanced_predictions)

    # Save enhanced report
    enhanced_report = {
        "timestamp": datetime.now().isoformat(),
        "analysis_type": "enhanced_low_cost_predictions",
        "market_conditions": get_market_conditions(),
        "enhanced_predictions": enhanced_predictions,
    }

    filename = (
        f"enhanced_low_cost_predictions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(filename, "w") as f:
        json.dump(enhanced_report, f, indent=2)

    print(f"\n💾 Enhanced report saved: {filename}")


def generate_market_intelligence(token: Dict) -> Dict:
    """Generate market intelligence for a token"""

    price = token["price"]
    volume = token["volume_24h_usdt"]
    change_24h = token["price_change_24h"]
    momentum_score = token["momentum_score"]

    # Volume analysis
    if volume > 50000:
        volume_assessment = "HIGH_LIQUIDITY"
        liquidity_score = 9
    elif volume > 10000:
        volume_assessment = "MODERATE_LIQUIDITY"
        liquidity_score = 6
    else:
        volume_assessment = "LOW_LIQUIDITY"
        liquidity_score = 3

    # Price action analysis
    if change_24h > 5:
        price_action = "STRONG_MOMENTUM"
    elif change_24h > 0:
        price_action = "POSITIVE_MOMENTUM"
    elif change_24h > -5:
        price_action = "CONSOLIDATION"
    else:
        price_action = "CORRECTION"

    # Market cap estimation (rough calculation)
    estimated_market_cap = price * 1000000000  # Assuming 1B token supply

    if estimated_market_cap < 1000000:  # < $1M
        market_cap_category = "MICRO_CAP"
        upside_potential = "EXTREME"
    elif estimated_market_cap < 10000000:  # < $10M
        market_cap_category = "SMALL_CAP"
        upside_potential = "HIGH"
    else:
        market_cap_category = "ESTABLISHED"
        upside_potential = "MODERATE"

    return {
        "volume_assessment": volume_assessment,
        "liquidity_score": liquidity_score,
        "price_action": price_action,
        "market_cap_category": market_cap_category,
        "upside_potential": upside_potential,
        "momentum_strength": (
            "STRONG"
            if momentum_score > 5.5
            else "MODERATE" if momentum_score > 4.5 else "WEAK"
        ),
    }


def calculate_enhanced_risk(token: Dict) -> Dict:
    """Calculate enhanced risk assessment"""

    volatility = token.get("volatility", 0)
    volume = token["volume_24h_usdt"]
    change_24h = token["price_change_24h"]

    # Volatility risk
    if volatility > 0.15:  # >15%
        volatility_risk = "VERY_HIGH"
        vol_score = 8
    elif volatility > 0.10:  # >10%
        volatility_risk = "HIGH"
        vol_score = 6
    elif volatility > 0.05:  # >5%
        volatility_risk = "MEDIUM"
        vol_score = 4
    else:
        volatility_risk = "LOW"
        vol_score = 2

    # Liquidity risk
    if volume < 1000:
        liquidity_risk = "VERY_HIGH"
        liq_score = 8
    elif volume < 10000:
        liquidity_risk = "HIGH"
        liq_score = 6
    elif volume < 50000:
        liquidity_risk = "MEDIUM"
        liq_score = 4
    else:
        liquidity_risk = "LOW"
        liq_score = 2

    # Overall risk score (0-10, higher = riskier)
    overall_risk_score = (vol_score + liq_score) / 2

    if overall_risk_score >= 7:
        overall_risk = "VERY_HIGH"
    elif overall_risk_score >= 5:
        overall_risk = "HIGH"
    elif overall_risk_score >= 3:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"

    return {
        "volatility_risk": volatility_risk,
        "liquidity_risk": liquidity_risk,
        "overall_risk": overall_risk,
        "risk_score": round(overall_risk_score, 1),
        "suggested_position_size": get_position_size_recommendation(overall_risk_score),
    }


def get_position_size_recommendation(risk_score: float) -> str:
    """Get position size recommendation based on risk"""
    if risk_score >= 7:
        return "1-2% (Speculative only)"
    elif risk_score >= 5:
        return "2-5% (Small position)"
    elif risk_score >= 3:
        return "5-8% (Moderate position)"
    else:
        return "8-12% (Larger position acceptable)"


def analyze_market_timing(token: Dict) -> Dict:
    """Analyze market timing for entry"""

    change_24h = token["price_change_24h"]
    momentum_score = token["momentum_score"]
    prediction = token["prediction"]

    # Timing signals
    if change_24h < -5 and prediction in ["BUY", "STRONG_BUY"]:
        timing_signal = "BUY_THE_DIP"
        urgency = "HIGH"
    elif change_24h > 5 and momentum_score > 5:
        timing_signal = "MOMENTUM_ENTRY"
        urgency = "MEDIUM"
    elif change_24h < 0 and prediction in ["BUY", "STRONG_BUY"]:
        timing_signal = "ACCUMULATION_ZONE"
        urgency = "MEDIUM"
    else:
        timing_signal = "WAIT_AND_WATCH"
        urgency = "LOW"

    # Entry strategy
    if timing_signal == "BUY_THE_DIP":
        entry_strategy = "Immediate entry with tight stops"
    elif timing_signal == "MOMENTUM_ENTRY":
        entry_strategy = "Enter on pullback or breakout confirmation"
    elif timing_signal == "ACCUMULATION_ZONE":
        entry_strategy = "Dollar cost average over 1-2 weeks"
    else:
        entry_strategy = "Wait for better entry opportunity"

    return {
        "timing_signal": timing_signal,
        "urgency": urgency,
        "entry_strategy": entry_strategy,
        "optimal_timeframe": "1-4 weeks" if urgency == "HIGH" else "1-2 months",
    }


def generate_investment_thesis(token: Dict) -> str:
    """Generate investment thesis for the token"""

    symbol = token["symbol"]
    price = token["price"]
    prediction = token["prediction"]
    potential_gain = token["potential_gain"]

    if prediction == "STRONG_BUY":
        thesis = f"{symbol} shows exceptional potential with {potential_gain:.1f}% upside. Strong fundamentals and technical setup suggest significant momentum ahead."
    elif prediction == "BUY":
        thesis = f"{symbol} presents solid opportunity with {potential_gain:.1f}% potential. Good risk/reward ratio for medium-term growth."
    else:
        thesis = f"{symbol} is a speculative play with limited upside. Consider only as small allocation for high-risk tolerance."

    return thesis


def get_market_conditions() -> Dict:
    """Get current market conditions assessment"""
    return {
        "overall_sentiment": "CAUTIOUS_OPTIMISM",
        "low_cap_trend": "ACCUMULATION_PHASE",
        "risk_appetite": "MODERATE",
        "recommended_allocation": "5-15% to micro-caps",
        "market_phase": "CONSOLIDATION",
    }


def print_enhanced_analysis(tokens: List[Dict]):
    """Print enhanced analysis for top tokens"""

    print(f"\n🔥 TOP 5 ENHANCED PREDICTIONS")
    print("=" * 70)

    for i, token in enumerate(tokens, 1):
        intel = token["market_intelligence"]
        risk = token["risk_assessment"]
        timing = token["timing_analysis"]

        print(f"\n{i}. {token['symbol']} - ${token['price']:.6f}")
        print("─" * 50)
        print(
            f"💡 Prediction: {token['prediction']} ({token['confidence']:.1%} confidence)"
        )
        print(
            f"📈 Potential: {token['potential_gain']:.1f}% → ${token['target_price']:.6f}"
        )
        print(f"📊 24h Change: {token['price_change_24h']:.2f}%")
        print(f"💰 Volume: ${token['volume_24h_usdt']:,.0f}")

        print(f"\n🧠 Market Intelligence:")
        print(f"   • Liquidity: {intel['volume_assessment']}")
        print(f"   • Price Action: {intel['price_action']}")
        print(f"   • Market Cap: {intel['market_cap_category']}")
        print(f"   • Upside Potential: {intel['upside_potential']}")
        print(f"   • Momentum: {intel['momentum_strength']}")

        print(f"\n⚠️ Risk Assessment:")
        print(f"   • Overall Risk: {risk['overall_risk']} ({risk['risk_score']}/10)")
        print(f"   • Volatility Risk: {risk['volatility_risk']}")
        print(f"   • Liquidity Risk: {risk['liquidity_risk']}")
        print(f"   • Position Size: {risk['suggested_position_size']}")

        print(f"\n⏰ Timing Analysis:")
        print(f"   • Signal: {timing['timing_signal']}")
        print(f"   • Urgency: {timing['urgency']}")
        print(f"   • Strategy: {timing['entry_strategy']}")
        print(f"   • Timeframe: {timing['optimal_timeframe']}")

        print(f"\n💭 Investment Thesis:")
        print(f"   {token['investment_thesis']}")


def generate_portfolio_strategy(tokens: List[Dict]):
    """Generate portfolio strategy for low-cost tokens"""

    print(f"\n🎯 PORTFOLIO STRATEGY FOR LOW-COST TOKENS")
    print("=" * 70)

    # Categorize tokens
    strong_buys = [t for t in tokens if t["prediction"] == "STRONG_BUY"]
    buys = [t for t in tokens if t["prediction"] == "BUY"]
    high_potential = [t for t in tokens if t["potential_gain"] > 50]

    print(f"📊 Portfolio Allocation Recommendations:")
    print(f"   • Total Low-Cost Allocation: 10-20% of portfolio")
    print(f"   • Strong Buy Tokens: {len(strong_buys)} tokens (5-8% allocation)")
    print(f"   • Buy Tokens: {len(buys)} tokens (3-5% allocation)")
    print(f"   • Speculative Plays: Remaining (2-7% allocation)")

    if strong_buys:
        print(f"\n🔥 PRIORITY TARGETS (Strong Buy):")
        for token in strong_buys[:3]:
            print(
                f"   • {token['symbol']}: {token['risk_assessment']['suggested_position_size']}"
            )

    if buys:
        print(f"\n📈 ACCUMULATION TARGETS (Buy):")
        for token in buys[:3]:
            print(
                f"   • {token['symbol']}: {token['risk_assessment']['suggested_position_size']}"
            )

    if high_potential:
        print(f"\n🚀 HIGH UPSIDE POTENTIAL:")
        for token in high_potential[:3]:
            print(f"   • {token['symbol']}: {token['potential_gain']:.1f}% potential")

    print(f"\n⚠️ RISK MANAGEMENT:")
    print(f"   • Never allocate more than 2% to any single micro-cap")
    print(f"   • Use stop losses at -15% to -20%")
    print(f"   • Take profits in stages (25%, 50%, 75% gains)")
    print(f"   • Monitor daily for sudden volume/price changes")
    print(f"   • Be prepared for high volatility")


if __name__ == "__main__":
    analyze_low_cost_tokens()
