#!/usr/bin/env python3
"""
Claude Non-Popular Token Analysis Launcher
Analyzes the least popular tokens using Claude AI for maximum alpha opportunities
"""

import os
import json
from datetime import datetime
from claude_non_popular_trader import ClaudeNonPopularTrader


def analyze_non_popular_tokens():
    """Analyze non-popular tokens without trading (analysis only)"""
    print("🤖 Claude AI Non-Popular Token Analysis")
    print("=" * 60)
    print("Finding alpha in the least popular tokens on Binance US")
    print("Focus: Micro-cap and nano-cap tokens with <$100K daily volume")
    print("=" * 60)

    trader = ClaudeNonPopularTrader()

    # Get non-popular tokens
    print("\n🔍 Scanning for non-popular tokens...")
    tokens = trader.get_non_popular_tokens()

    if not tokens:
        print("❌ No non-popular tokens found")
        return

    print(f"✅ Found {len(tokens)} non-popular tokens")

    # Show volume distribution
    print(f"\n📊 Non-Popular Token Volume Distribution:")

    volume_ranges = [
        (50000, 100000, "High Non-Popular"),
        (25000, 50000, "Mid Non-Popular"),
        (10000, 25000, "Low Non-Popular"),
        (1000, 10000, "Ultra Non-Popular"),
    ]

    for min_vol, max_vol, label in volume_ranges:
        count = len([t for t in tokens if min_vol <= t["volume_usd"] < max_vol])
        if count > 0:
            print(f"  {label:18} (${min_vol:,}-${max_vol:,}): {count:3d} tokens")

    # Focus on the most non-popular (lowest volume)
    ultra_non_popular = [t for t in tokens if t["volume_usd"] < 10000][:15]

    if ultra_non_popular:
        print(f"\n🎯 TOP 15 ULTRA NON-POPULAR TOKENS (Highest Alpha Potential):")
        print("-" * 80)
        print(f"{'Rank':4} {'Symbol':12} {'Volume':12} {'24h Change':12} {'Price':15}")
        print("-" * 80)

        for i, token in enumerate(ultra_non_popular, 1):
            print(
                f"{i:4} {token['symbol']:12} ${token['volume_usd']:>9,.0f} "
                f"{token['price_change_24h']:+10.2f}% ${token['current_price']:>12.8f}"
            )

    # Analyze top 5 with Claude
    print(f"\n🤖 CLAUDE AI ANALYSIS OF TOP 5 NON-POPULAR TOKENS:")
    print("=" * 60)

    market_context = {
        "total_tokens": len(tokens),
        "avg_change": sum(t["price_change_24h"] for t in tokens) / len(tokens),
        "sentiment": (
            "Bearish" if sum(t["price_change_24h"] for t in tokens) < 0 else "Bullish"
        ),
    }

    analysis_results = []

    for i, token in enumerate(tokens[:5], 1):  # Top 5 least popular
        symbol = token["symbol"]
        print(f"\n🔍 [{i}/5] Analyzing {symbol} (Volume: ${token['volume_usd']:,.0f})")

        # Get detailed technical analysis
        detailed_analysis = trader.get_detailed_analysis(symbol)
        if not detailed_analysis:
            print(f"   ❌ Failed to get technical data for {symbol}")
            continue

        # Combine data
        combined_data = {**token, **detailed_analysis}

        # Get Claude's analysis
        claude_analysis = trader.claude_analyze_token(combined_data, market_context)

        # Display results
        recommendation = claude_analysis.get("RECOMMENDATION", "UNKNOWN")
        confidence = claude_analysis.get("confidence", 0)
        reasoning = claude_analysis.get("REASONING", "No reasoning provided")

        print(
            f"   🤖 Claude Recommendation: {recommendation} (Confidence: {confidence}%)"
        )
        print(
            f"   📝 Reasoning: {reasoning[:100]}{'...' if len(reasoning) > 100 else ''}"
        )

        if recommendation == "BUY" and confidence >= 70:
            entry_price = claude_analysis.get(
                "ENTRY_PRICE", combined_data["current_price"]
            )
            take_profit = claude_analysis.get("TAKE_PROFIT_1", 0)
            stop_loss = claude_analysis.get("STOP_LOSS", 0)

            print(
                f"   🎯 Entry: ${entry_price:.8f} | TP: ${take_profit:.8f} | SL: ${stop_loss:.8f}"
            )

            # Calculate potential returns
            if entry_price > 0 and take_profit > 0:
                potential_gain = (take_profit / entry_price - 1) * 100
                print(f"   💰 Potential Gain: {potential_gain:+.1f}%")

        analysis_results.append(
            {
                "symbol": symbol,
                "claude_analysis": claude_analysis,
                "token_data": combined_data,
            }
        )

    # Save analysis results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"claude_non_popular_analysis_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_non_popular_tokens": len(tokens),
                "market_context": market_context,
                "analysis_results": analysis_results,
                "ultra_non_popular_count": len(ultra_non_popular),
            },
            f,
            indent=2,
            default=str,
        )

    print(f"\n💾 Analysis saved to: {filename}")

    # Summary
    buy_recommendations = [
        r
        for r in analysis_results
        if r["claude_analysis"].get("RECOMMENDATION") == "BUY"
    ]
    high_confidence_buys = [
        r
        for r in buy_recommendations
        if r["claude_analysis"].get("confidence", 0) >= 70
    ]

    print(f"\n📊 ANALYSIS SUMMARY:")
    print(f"  • Total Non-Popular Tokens: {len(tokens)}")
    print(f"  • Ultra Non-Popular (<$10K): {len(ultra_non_popular)}")
    print(f"  • Claude BUY Recommendations: {len(buy_recommendations)}")
    print(f"  • High Confidence BUYs (≥70%): {len(high_confidence_buys)}")

    if high_confidence_buys:
        print(f"\n🚀 HIGH CONFIDENCE OPPORTUNITIES:")
        for result in high_confidence_buys:
            symbol = result["symbol"]
            confidence = result["claude_analysis"].get("confidence", 0)
            volume = result["token_data"].get("volume_usd", 0)
            change_24h = result["token_data"].get("price_change_24h", 0)

            print(
                f"  • {symbol:12} - Confidence: {confidence:3d}% | "
                f"Volume: ${volume:>8,.0f} | 24h: {change_24h:+6.2f}%"
            )

    print(f"\n⚠️  REMEMBER: Non-popular tokens are HIGH RISK / HIGH REWARD")
    print(f"   • Use small position sizes (1-3% of portfolio)")
    print(f"   • Set tight stop losses (5-8%)")
    print(f"   • Take profits at 15-30% gains")
    print(f"   • Monitor closely due to low liquidity")


def show_live_trading_option():
    """Show option to start live trading"""
    print(f"\n🔥 READY FOR LIVE TRADING?")
    print("=" * 40)
    print("To start live trading with Claude AI:")
    print("python3 claude_non_popular_trader.py")
    print("")
    print("This will:")
    print("• Analyze non-popular tokens in real-time")
    print("• Use Claude AI to make trading decisions")
    print("• Execute actual trades on Binance US")
    print("• Focus on maximum alpha opportunities")
    print("")
    print("⚠️  WARNING: This involves real money and risk!")


if __name__ == "__main__":
    try:
        analyze_non_popular_tokens()
        show_live_trading_option()
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        print("Check your API keys and internet connection")
