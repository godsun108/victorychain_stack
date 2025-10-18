#!/usr/bin/env python3
"""
VictoryChain Complete Token Scanner
Analyzes ALL available USDT pairs on Binance US for momentum opportunities
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Optional


class CompleteTokenScanner:
    def __init__(self):
        self.claude_api_key = os.getenv(
            "CLAUDE_API_KEY",
            "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",
        )
        self.binance_us_base = "https://api.binance.us"

    def get_all_usdt_pairs(self) -> List[str]:
        """Get all USDT trading pairs available on Binance US"""
        try:
            response = requests.get(f"{self.binance_us_base}/api/v3/exchangeInfo")
            if response.status_code == 200:
                exchange_info = response.json()
                usdt_pairs = []

                for symbol_info in exchange_info["symbols"]:
                    symbol = symbol_info["symbol"]
                    if (
                        symbol.endswith("USDT")
                        and symbol_info["status"] == "TRADING"
                        and symbol_info["isSpotTradingAllowed"]
                    ):
                        usdt_pairs.append(symbol)

                usdt_pairs.sort()
                return usdt_pairs
            else:
                print(f"❌ Failed to get exchange info: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching exchange info: {e}")
            return []

    def get_market_data_batch(self, symbols: List[str]) -> Dict[str, Dict]:
        """Get market data for all symbols in one request"""
        try:
            # Get 24hr ticker statistics for all symbols
            response = requests.get(f"{self.binance_us_base}/api/v3/ticker/24hr")
            if response.status_code == 200:
                tickers = response.json()

                market_data = {}
                symbol_set = set(symbols)

                for ticker in tickers:
                    symbol = ticker["symbol"]
                    if symbol in symbol_set:
                        try:
                            last_price = float(ticker["lastPrice"])
                            volume = float(ticker["volume"])
                            quote_volume = float(ticker["quoteVolume"])

                            # Skip tokens with very low volume or price
                            if quote_volume < 1000 or last_price < 0.000001:
                                continue

                            market_data[symbol] = {
                                "symbol": symbol,
                                "price": last_price,
                                "change_24h": float(ticker["priceChangePercent"]),
                                "volume_24h": quote_volume,
                                "volume_change": float(ticker["count"]),
                                "high_24h": float(ticker["highPrice"]),
                                "low_24h": float(ticker["lowPrice"]),
                                "open_price": float(ticker["openPrice"]),
                                "trades_24h": int(ticker["count"]),
                            }
                        except (ValueError, KeyError):
                            continue

                return market_data
            else:
                print(f"❌ Failed to fetch market data: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Error fetching market data: {e}")
            return {}

    def analyze_token_momentum(self, symbol: str, data: Dict) -> Dict:
        """Analyze individual token for momentum potential"""

        # Quick technical analysis scoring
        score = 0
        reasons = []

        # Price momentum (24h change)
        change_24h = data["change_24h"]
        if change_24h > 15:
            score += 30
            reasons.append(f"Strong +{change_24h:.1f}% momentum")
        elif change_24h > 5:
            score += 20
            reasons.append(f"Good +{change_24h:.1f}% momentum")
        elif change_24h > 0:
            score += 10
            reasons.append(f"Positive +{change_24h:.1f}% trend")
        elif change_24h > -5:
            score += 5
            reasons.append(f"Minor {change_24h:.1f}% decline")
        else:
            reasons.append(f"Significant {change_24h:.1f}% decline")

        # Volume analysis
        volume_24h = data["volume_24h"]
        if volume_24h > 10000000:  # $10M+
            score += 25
            reasons.append(f"Very high volume ${volume_24h/1000000:.1f}M")
        elif volume_24h > 1000000:  # $1M+
            score += 15
            reasons.append(f"High volume ${volume_24h/1000000:.1f}M")
        elif volume_24h > 100000:  # $100K+
            score += 10
            reasons.append(f"Good volume ${volume_24h/1000:.0f}K")
        else:
            reasons.append(f"Low volume ${volume_24h/1000:.0f}K")

        # Volatility (range analysis)
        price_range = (data["high_24h"] - data["low_24h"]) / data["price"] * 100
        if price_range > 20:
            score += 20
            reasons.append(f"High volatility {price_range:.1f}%")
        elif price_range > 10:
            score += 15
            reasons.append(f"Good volatility {price_range:.1f}%")
        elif price_range > 5:
            score += 10
            reasons.append(f"Moderate volatility {price_range:.1f}%")

        # Trading activity
        trades_24h = data["trades_24h"]
        if trades_24h > 100000:
            score += 15
            reasons.append(f"Very active {trades_24h:,} trades")
        elif trades_24h > 10000:
            score += 10
            reasons.append(f"Active {trades_24h:,} trades")

        # Current position relative to 24h range
        price_range_24h = data["high_24h"] - data["low_24h"]
        if price_range_24h > 0:
            current_pos = (data["price"] - data["low_24h"]) / price_range_24h
            if current_pos > 0.8:
                score += 15
                reasons.append("Near 24h high")
            elif current_pos < 0.2:
                score += 10
                reasons.append("Near 24h low (potential bounce)")
        else:
            # Handle case where high == low (no price movement)
            reasons.append("No 24h price range")

        # Estimate gain potential based on factors
        if score >= 80:
            gain_potential = min(25 + (score - 80) * 0.5, 40)
            confidence = 85
            risk = "MEDIUM"
        elif score >= 60:
            gain_potential = min(15 + (score - 60) * 0.5, 25)
            confidence = 70
            risk = "MEDIUM"
        elif score >= 40:
            gain_potential = min(8 + (score - 40) * 0.3, 15)
            confidence = 55
            risk = "HIGH"
        else:
            gain_potential = max(score * 0.2, 2)
            confidence = 40
            risk = "VERY_HIGH"

        target_price = data["price"] * (1 + gain_potential / 100)

        return {
            "symbol": symbol,
            "momentum_score": score,
            "gain_potential": gain_potential,
            "confidence": confidence,
            "risk_level": risk,
            "target_price": target_price,
            "reasons": reasons,
            "current_price": data["price"],
            "change_24h": change_24h,
            "volume_24h": volume_24h,
            "market_cap": data.get("market_cap", 0),
        }

    def scan_all_tokens(self) -> List[Dict]:
        """Scan all available USDT pairs for momentum opportunities"""
        print("🔍 Discovering all USDT pairs on Binance US...")

        # Get all USDT pairs
        all_pairs = self.get_all_usdt_pairs()
        print(f"📊 Found {len(all_pairs)} USDT pairs")

        # Get market data for all pairs
        print("📈 Fetching market data for all pairs...")
        market_data = self.get_market_data_batch(all_pairs)
        print(f"💹 Analyzing {len(market_data)} active pairs...")

        # Analyze each token
        opportunities = []
        high_potential_count = 0

        for symbol, data in market_data.items():
            analysis = self.analyze_token_momentum(symbol, data)
            opportunities.append(analysis)

            # Count high potential opportunities
            if analysis["gain_potential"] >= 20 and analysis["confidence"] >= 60:
                high_potential_count += 1

        # Sort by potential (gain * confidence)
        opportunities.sort(
            key=lambda x: x["gain_potential"] * (x["confidence"] / 100), reverse=True
        )

        print(f"🚀 Found {high_potential_count} tokens with 20%+ potential!")

        return opportunities

    def display_opportunities(self, opportunities: List[Dict], show_all: bool = False):
        """Display the trading opportunities"""

        # Filter for high-potential opportunities
        high_potential = [
            opp
            for opp in opportunities
            if opp["gain_potential"] >= 20 and opp["confidence"] >= 60
        ]

        medium_potential = [
            opp
            for opp in opportunities
            if 10 <= opp["gain_potential"] < 20 and opp["confidence"] >= 50
        ]

        print("\n" + "=" * 80)
        print("🚀 HIGH MOMENTUM OPPORTUNITIES (20%+ Potential)")
        print("=" * 80)

        if not high_potential:
            print("❌ No high-momentum opportunities found at this time")
        else:
            for i, opp in enumerate(high_potential[:10], 1):  # Top 10
                risk_emoji = {
                    "LOW": "🟢",
                    "MEDIUM": "🟡",
                    "HIGH": "🔴",
                    "VERY_HIGH": "🔴",
                }.get(opp["risk_level"], "🔴")

                print(f"\n{i}. {opp['symbol']} 📈")
                print(f"   Current Price:    ${opp['current_price']:.8f}")
                print(f"   Target Price:     ${opp['target_price']:.8f}")
                print(f"   Gain Potential:   {opp['gain_potential']:.1f}%")
                print(f"   Confidence:       {opp['confidence']}%")
                print(f"   24h Change:       {opp['change_24h']:+.2f}%")
                print(f"   24h Volume:       ${opp['volume_24h']:,.0f}")
                print(f"   Risk Level:       {risk_emoji} {opp['risk_level']}")
                print(f"   Momentum Score:   {opp['momentum_score']}/100")
                print(f"   Key Factors:      {', '.join(opp['reasons'][:3])}")

        if show_all and medium_potential:
            print(f"\n" + "=" * 80)
            print("📊 MEDIUM POTENTIAL OPPORTUNITIES (10-20%)")
            print("=" * 80)

            for i, opp in enumerate(medium_potential[:15], 1):  # Top 15
                print(
                    f"{i:2d}. {opp['symbol']:<12} | {opp['gain_potential']:5.1f}% | "
                    f"{opp['confidence']:2.0f}% conf | {opp['change_24h']:+6.2f}% | "
                    f"${opp['volume_24h']/1000:6.0f}K vol"
                )

        # Trading recommendations
        if high_potential:
            print(f"\n💡 LIVE TRADING RECOMMENDATIONS:")
            print(f"   🎯 Focus on top 3-5 opportunities for best risk/reward")
            print(f"   💰 Use $75-100 position size per token")
            print(f"   🛡️ Set 8% stop losses to protect capital")
            print(f"   ⏰ Hold for 24-48 hours or until target hit")
            print(f"   📊 Monitor positions every 2-4 hours")

            # Show specific trade setups for top 3
            print(f"\n🎯 READY-TO-EXECUTE TRADE SETUPS:")
            for i, opp in enumerate(high_potential[:3], 1):
                stop_loss_price = opp["current_price"] * 0.92
                position_size = 75
                quantity = position_size / opp["current_price"]

                print(f"\n   Trade {i}: {opp['symbol']}")
                print(f"     Entry:      ${opp['current_price']:.8f}")
                print(
                    f"     Target:     ${opp['target_price']:.8f} (+{opp['gain_potential']:.1f}%)"
                )
                print(f"     Stop Loss:  ${stop_loss_price:.8f} (-8%)")
                print(f"     Size:       ${position_size} ({quantity:.2f} tokens)")
                print(
                    f"     Risk:       {opp['risk_level']} | Confidence: {opp['confidence']}%"
                )


def main():
    print("🔍 VictoryChain Complete Token Scanner")
    print("=====================================")
    print("📊 Analyzing ALL USDT pairs on Binance US")
    print("🎯 Finding 20-30% momentum opportunities")
    print("")

    scanner = CompleteTokenScanner()

    # Scan all tokens
    opportunities = scanner.scan_all_tokens()

    # Display results
    scanner.display_opportunities(opportunities, show_all=True)

    print(f"\n📋 SCAN SUMMARY:")
    print(f"   • Total pairs analyzed: {len(opportunities)}")
    high_potential = sum(
        1
        for opp in opportunities
        if opp["gain_potential"] >= 20 and opp["confidence"] >= 60
    )
    medium_potential = sum(
        1
        for opp in opportunities
        if 10 <= opp["gain_potential"] < 20 and opp["confidence"] >= 50
    )
    print(f"   • High potential (20%+): {high_potential}")
    print(f"   • Medium potential (10-20%): {medium_potential}")
    print(f"   • Scan completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\n⚡ NEXT STEPS:")
    print(f"   1. Review the opportunities above")
    print(f"   2. Run: ./momentum_system.sh trade")
    print(f"   3. Execute trades on selected tokens")
    print(f"   4. Monitor positions for exits")


if __name__ == "__main__":
    main()
