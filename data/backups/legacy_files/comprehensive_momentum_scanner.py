#!/usr/bin/env python3
"""
Comprehensive Momentum Scanner - Check all tradable tokens every few hours
Analyzes momentum for buy/hold decisions
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import numpy as np
from binance.client import Client
from dotenv import load_dotenv


class ComprehensiveMomentumScanner:
    def __init__(self):
        load_dotenv()
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

    def get_momentum_score(self, symbol: str) -> float:
        """Calculate advanced momentum score"""
        try:
            # Get various timeframe data
            klines_1h = self.client.get_klines(symbol=symbol, interval="1h", limit=24)
            klines_4h = self.client.get_klines(symbol=symbol, interval="4h", limit=12)
            klines_1d = self.client.get_klines(symbol=symbol, interval="1d", limit=7)

            if not klines_1h or not klines_4h or not klines_1d:
                return 0

            # Calculate price changes
            current_price = float(klines_1h[-1][4])
            price_1h_ago = (
                float(klines_1h[-2][4]) if len(klines_1h) > 1 else current_price
            )
            price_4h_ago = (
                float(klines_4h[-2][4]) if len(klines_4h) > 1 else current_price
            )
            price_24h_ago = (
                float(klines_1d[-2][4]) if len(klines_1d) > 1 else current_price
            )

            change_1h = ((current_price - price_1h_ago) / price_1h_ago) * 100
            change_4h = ((current_price - price_4h_ago) / price_4h_ago) * 100
            change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100

            # Volume analysis
            volumes = [float(k[5]) for k in klines_1h[-6:]]
            avg_volume = np.mean(volumes[:-1]) if len(volumes) > 1 else volumes[0]
            current_volume = volumes[-1]
            volume_surge = (current_volume / avg_volume) if avg_volume > 0 else 1

            # Momentum calculation
            momentum_score = 50  # Base score

            # Time-weighted price momentum
            momentum_score += change_1h * 3  # Recent movement is most important
            momentum_score += change_4h * 2  # Medium-term trend
            momentum_score += change_24h * 1  # Longer-term context

            # Volume factor
            if volume_surge > 2:
                momentum_score += 20
            elif volume_surge > 1.5:
                momentum_score += 10
            elif volume_surge < 0.5:
                momentum_score -= 10

            # Consistency bonus (all timeframes positive)
            if change_1h > 0 and change_4h > 0 and change_24h > 0:
                momentum_score += 15

            # Volatility factor (higher volatility = higher potential)
            price_range = max([float(k[2]) for k in klines_1h[-24:]]) - min(
                [float(k[3]) for k in klines_1h[-24:]]
            )
            volatility = (price_range / current_price) * 100
            momentum_score += min(volatility * 0.5, 10)

            return max(momentum_score, 0)

        except Exception as e:
            return 0

    def scan_all_tradable_tokens(self) -> List[Dict]:
        """Scan ALL tradable tokens for momentum opportunities"""
        print("🔍 SCANNING ALL TRADABLE TOKENS FOR MOMENTUM...")
        print("=" * 60)

        # Get all tickers
        tickers = self.client.get_ticker()
        usdt_pairs = [
            t
            for t in tickers
            if t["symbol"].endswith("USDT") and t["symbol"] != "USDCUSDT"
        ]

        print(f"📊 Analyzing {len(usdt_pairs)} USDT trading pairs...")

        opportunities = []
        high_momentum = []
        moderate_momentum = []

        for i, ticker in enumerate(usdt_pairs):
            symbol = ticker["symbol"]
            token = symbol.replace("USDT", "")

            try:
                # Get momentum score
                momentum_score = self.get_momentum_score(symbol)

                # Get basic data
                daily_change = float(ticker["priceChangePercent"])
                volume_24h = float(ticker["quoteVolume"])
                price = float(ticker["lastPrice"])

                token_data = {
                    "symbol": symbol,
                    "token": token,
                    "momentum_score": momentum_score,
                    "daily_change": daily_change,
                    "volume_24h": volume_24h,
                    "price": price,
                    "timestamp": datetime.now().isoformat(),
                }

                # Categorize opportunities
                if momentum_score >= 200:  # Exceptional
                    high_momentum.append(token_data)
                elif momentum_score >= 100:  # Good
                    moderate_momentum.append(token_data)

                opportunities.append(token_data)

                # Progress indicator
                if (i + 1) % 20 == 0:
                    print(f"🔄 Processed {i + 1}/{len(usdt_pairs)} tokens...")

                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                print(f"⚠️  Error analyzing {symbol}: {e}")
                continue

        # Sort by momentum score
        opportunities.sort(key=lambda x: x["momentum_score"], reverse=True)
        high_momentum.sort(key=lambda x: x["momentum_score"], reverse=True)
        moderate_momentum.sort(key=lambda x: x["momentum_score"], reverse=True)

        return opportunities, high_momentum, moderate_momentum

    def generate_momentum_report(self):
        """Generate comprehensive momentum analysis report"""
        print("🚀 GENERATING COMPREHENSIVE MOMENTUM REPORT")
        print("=" * 60)

        opportunities, high_momentum, moderate_momentum = (
            self.scan_all_tradable_tokens()
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Summary stats
        print(
            f"\n📊 MOMENTUM ANALYSIS SUMMARY ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        )
        print("=" * 60)
        print(f"🔍 Total tokens analyzed: {len(opportunities)}")
        print(f"🔥 High momentum (200+): {len(high_momentum)}")
        print(f"⚡ Moderate momentum (100+): {len(moderate_momentum)}")
        print(
            f"📈 Positive daily change: {len([o for o in opportunities if o['daily_change'] > 0])}"
        )

        # Top opportunities
        print(f"\n🏆 TOP 10 MOMENTUM OPPORTUNITIES:")
        print("-" * 80)
        print(f"{'Token':<8} {'Momentum':<10} {'24h%':<8} {'Volume':<12} {'Price':<10}")
        print("-" * 80)

        for opp in opportunities[:10]:
            print(
                f"{opp['token']:<8} {opp['momentum_score']:<10.1f} {opp['daily_change']:<8.2f} "
                f"${opp['volume_24h']:<11,.0f} ${opp['price']:<10.6f}"
            )

        # High momentum tokens
        if high_momentum:
            print(f"\n🔥 EXCEPTIONAL MOMENTUM TOKENS (200+):")
            print("-" * 80)
            for token in high_momentum[:5]:
                print(
                    f"  {token['token']}: Score {token['momentum_score']:.1f}, "
                    f"24h: {token['daily_change']:+.2f}%, Vol: ${token['volume_24h']:,.0f}"
                )

        # Buy/Hold recommendations
        print(f"\n💡 AUTOMATED TRADING RECOMMENDATIONS:")
        print("-" * 60)

        buy_candidates = [
            o
            for o in opportunities
            if o["momentum_score"] >= 150 and o["volume_24h"] > 100000
        ]
        hold_candidates = [
            o
            for o in opportunities
            if o["momentum_score"] >= 100 and o["daily_change"] > 0
        ]

        print(f"🎯 BUY candidates (momentum 150+, volume 100k+): {len(buy_candidates)}")
        if buy_candidates:
            for token in buy_candidates[:3]:
                print(
                    f"  ✅ {token['token']}: Score {token['momentum_score']:.1f}, "
                    f"Change {token['daily_change']:+.2f}%"
                )

        print(f"💎 HOLD candidates (momentum 100+, positive): {len(hold_candidates)}")
        if hold_candidates:
            for token in hold_candidates[:5]:
                print(
                    f"  💎 {token['token']}: Score {token['momentum_score']:.1f}, "
                    f"Change {token['daily_change']:+.2f}%"
                )

        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tokens": len(opportunities),
                "high_momentum_count": len(high_momentum),
                "moderate_momentum_count": len(moderate_momentum),
                "positive_change_count": len(
                    [o for o in opportunities if o["daily_change"] > 0]
                ),
            },
            "top_opportunities": opportunities[:20],
            "high_momentum_tokens": high_momentum,
            "moderate_momentum_tokens": moderate_momentum[:10],
            "buy_candidates": buy_candidates,
            "hold_candidates": hold_candidates[:10],
        }

        filename = f"comprehensive_momentum_analysis_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\n💾 Detailed report saved: {filename}")

        return report_data


def main():
    scanner = ComprehensiveMomentumScanner()
    scanner.generate_momentum_report()


if __name__ == "__main__":
    main()
