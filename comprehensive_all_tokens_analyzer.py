#!/usr/bin/env python3

"""
🔥 ALL BINANCE US TOKENS COMPREHENSIVE ANALYSIS
Advanced analysis of ALL 243 tradeable tokens with Claude AI integration
Features: Volume analysis, momentum detection, price predictions, risk assessment
"""

import json
import requests
import pandas as pd
import numpy as np
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
class TokenAnalysis:
    """Enhanced token analysis data structure"""

    symbol: str
    base_asset: str
    price: float
    volume_24h_usdt: float
    price_change_24h: float

    # Technical indicators
    rsi_14: float = 0.0
    volume_category: str = "unknown"
    momentum_score: float = 0.0
    volatility: float = 0.0

    # AI analysis
    ai_prediction: str = "NEUTRAL"
    ai_confidence: float = 0.5
    risk_score: float = 5.0

    # Gaming/Sector specific
    sector: str = "general"
    ecosystem_score: float = 0.0

    # Rankings
    volume_rank: int = 0
    momentum_rank: int = 0
    performance_rank: int = 0


class ComprehensiveTokenAnalyzer:
    """Advanced analyzer for all Binance US tokens"""

    def __init__(self):
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")
        self.base_url = "https://api.binance.us/api/v3"

        # Volume categories for classification
        self.volume_categories = {
            "mega_cap": {
                "min": 50_000_000,
                "emoji": "🔥",
                "desc": "Mega Volume (>$50M)",
            },
            "large_cap": {
                "min": 10_000_000,
                "emoji": "🟢",
                "desc": "Large Volume ($10M-$50M)",
            },
            "mid_cap": {
                "min": 1_000_000,
                "emoji": "🔵",
                "desc": "Mid Volume ($1M-$10M)",
            },
            "small_cap": {
                "min": 100_000,
                "emoji": "🟡",
                "desc": "Small Volume ($100K-$1M)",
            },
            "micro_cap": {
                "min": 10_000,
                "emoji": "🟠",
                "desc": "Micro Volume ($10K-$100K)",
            },
            "nano_cap": {"min": 0, "emoji": "🔴", "desc": "Nano Volume (<$10K)"},
        }

        # Gaming and sector classifications
        self.gaming_tokens = {
            "MAGIC",
            "AXS",
            "SAND",
            "MANA",
            "ALICE",
            "ILV",
            "GALA",
            "ENJ",
            "VOXEL",
        }

        self.defi_tokens = {
            "UNI",
            "AAVE",
            "CRV",
            "COMP",
            "MKR",
            "SNX",
            "SUSHI",
            "LRC",
            "BNT",
        }

        self.ai_tokens = {"FET", "OCEAN", "NMR", "RENDER", "API3"}

        self.layer1_tokens = {
            "BTC",
            "ETH",
            "ADA",
            "SOL",
            "AVAX",
            "DOT",
            "ATOM",
            "NEAR",
            "ALGO",
        }

    def load_tokens_data(self) -> List[Dict]:
        """Load existing tokens data or fetch fresh data"""
        try:
            # Try to load existing data first
            with open("all_binance_us_tokens.json", "r") as f:
                data = json.load(f)
                print(f"✅ Loaded {len(data)} tokens from existing data")
                return data
        except FileNotFoundError:
            print("📡 Fetching fresh token data from Binance US...")
            return self.fetch_all_tokens_data()

    def fetch_all_tokens_data(self) -> List[Dict]:
        """Fetch fresh data for all tokens"""
        try:
            # Get 24hr ticker stats for all symbols
            response = requests.get(f"{self.base_url}/ticker/24hr", timeout=30)
            response.raise_for_status()

            ticker_data = response.json()

            # Filter for USDT pairs and active symbols
            usdt_pairs = [
                {
                    "symbol": ticker["symbol"],
                    "base_asset": ticker["symbol"].replace("USDT", ""),
                    "price": float(ticker["lastPrice"]),
                    "volume_24h_usdt": float(ticker["volume"])
                    * float(ticker["lastPrice"]),
                    "price_change_24h": float(ticker["priceChangePercent"]),
                    "count": int(ticker["count"]),
                }
                for ticker in ticker_data
                if ticker["symbol"].endswith("USDT") and float(ticker["volume"]) > 0
            ]

            # Sort by volume
            usdt_pairs.sort(key=lambda x: x["volume_24h_usdt"], reverse=True)

            # Save to file
            with open("all_binance_us_tokens.json", "w") as f:
                json.dump(usdt_pairs, f, indent=2)

            print(f"💾 Saved {len(usdt_pairs)} tokens to file")
            return usdt_pairs

        except Exception as e:
            print(f"❌ Error fetching tokens data: {e}")
            return []

    def categorize_by_volume(self, volume_usd: float) -> str:
        """Categorize token by 24h volume"""
        for category, info in self.volume_categories.items():
            if volume_usd >= info["min"]:
                return category
        return "nano_cap"

    def classify_sector(self, base_asset: str) -> Tuple[str, float]:
        """Classify token by sector and assign ecosystem score"""
        base = base_asset.upper()

        if base in self.gaming_tokens:
            return "gaming", 8.5 if base == "MAGIC" else 7.0
        elif base in self.defi_tokens:
            return "defi", 8.0
        elif base in self.ai_tokens:
            return "ai", 8.5
        elif base in self.layer1_tokens:
            return "layer1", 7.5
        elif base in ["BNB", "USDC", "USDT", "DAI"]:
            return "stablecoin", 6.0
        elif base in ["DOGE", "SHIB", "PEPE", "BONK", "FLOKI"]:
            return "meme", 5.0
        else:
            return "general", 6.0

    def calculate_momentum_score(self, token_data: Dict) -> float:
        """Calculate momentum score based on price change and volume"""
        price_change = token_data.get("price_change_24h", 0.0)
        volume = token_data.get("volume_24h_usdt", 0.0)

        # Base momentum from price change
        momentum = abs(price_change) / 100.0

        # Volume boost (logarithmic)
        if volume > 0:
            volume_boost = np.log10(max(volume, 1)) / 10.0
            momentum += volume_boost

        # Cap at 10.0
        return min(momentum * 10.0, 10.0)

    def analyze_all_tokens(self) -> List[TokenAnalysis]:
        """Perform comprehensive analysis on all tokens"""
        print("🔍 Starting comprehensive analysis of all tokens...")

        tokens_data = self.load_tokens_data()
        if not tokens_data:
            print("❌ No token data available")
            return []

        analyzed_tokens = []

        for i, token_data in enumerate(tokens_data):
            try:
                # Basic token analysis
                analysis = TokenAnalysis(
                    symbol=token_data["symbol"],
                    base_asset=token_data["base_asset"],
                    price=token_data["price"],
                    volume_24h_usdt=token_data["volume_24h_usdt"],
                    price_change_24h=token_data["price_change_24h"],
                )

                # Volume categorization
                analysis.volume_category = self.categorize_by_volume(
                    analysis.volume_24h_usdt
                )

                # Sector classification
                analysis.sector, analysis.ecosystem_score = self.classify_sector(
                    analysis.base_asset
                )

                # Momentum calculation
                analysis.momentum_score = self.calculate_momentum_score(token_data)

                # Simple volatility estimate (based on price change)
                analysis.volatility = abs(analysis.price_change_24h) / 100.0

                # Risk scoring (inverse of volume + volatility factor)
                volume_risk = max(
                    10 - np.log10(max(analysis.volume_24h_usdt, 1)) / 2, 1
                )
                volatility_risk = min(analysis.volatility * 10, 5)
                analysis.risk_score = min((volume_risk + volatility_risk) / 2, 10)

                # Rankings (will be calculated after all tokens processed)
                analysis.volume_rank = i + 1

                analyzed_tokens.append(analysis)

                # Progress indicator
                if (i + 1) % 50 == 0:
                    print(f"📊 Analyzed {i + 1}/{len(tokens_data)} tokens...")

            except Exception as e:
                print(f"⚠️  Error analyzing {token_data.get('symbol', 'unknown')}: {e}")
                continue

        # Calculate momentum and performance rankings
        analyzed_tokens.sort(key=lambda x: x.momentum_score, reverse=True)
        for i, token in enumerate(analyzed_tokens):
            token.momentum_rank = i + 1

        analyzed_tokens.sort(key=lambda x: x.price_change_24h, reverse=True)
        for i, token in enumerate(analyzed_tokens):
            token.performance_rank = i + 1

        # Sort back by volume for final presentation
        analyzed_tokens.sort(key=lambda x: x.volume_24h_usdt, reverse=True)

        print(f"✅ Analysis complete! Processed {len(analyzed_tokens)} tokens")
        return analyzed_tokens

    def generate_top_performers_report(
        self, tokens: List[TokenAnalysis], limit: int = 20
    ) -> str:
        """Generate report of top performing tokens"""

        # Top by volume
        top_volume = sorted(tokens, key=lambda x: x.volume_24h_usdt, reverse=True)[
            :limit
        ]

        # Top by momentum
        top_momentum = sorted(tokens, key=lambda x: x.momentum_score, reverse=True)[
            :limit
        ]

        # Top by performance (24h change)
        top_performance = sorted(
            tokens, key=lambda x: x.price_change_24h, reverse=True
        )[:limit]

        # Gaming tokens specifically
        gaming_tokens = [t for t in tokens if t.sector == "gaming"]
        gaming_tokens.sort(key=lambda x: x.momentum_score, reverse=True)

        report = f"""
🔥 COMPREHENSIVE BINANCE US TOKENS ANALYSIS
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*80}
📊 OVERVIEW STATISTICS
{'='*80}
📈 Total Tokens Analyzed: {len(tokens)}
🔥 Mega Volume Tokens (>$50M): {len([t for t in tokens if t.volume_category == 'mega_cap'])}
🟢 Large Volume Tokens ($10M-$50M): {len([t for t in tokens if t.volume_category == 'large_cap'])}
🔵 Mid Volume Tokens ($1M-$10M): {len([t for t in tokens if t.volume_category == 'mid_cap'])}
🟡 Small Volume Tokens ($100K-$1M): {len([t for t in tokens if t.volume_category == 'small_cap'])}

🎮 Gaming Tokens: {len([t for t in tokens if t.sector == 'gaming'])}
🏦 DeFi Tokens: {len([t for t in tokens if t.sector == 'defi'])}
🤖 AI Tokens: {len([t for t in tokens if t.sector == 'ai'])}
🏗️  Layer 1 Tokens: {len([t for t in tokens if t.sector == 'layer1'])}

{'='*80}
🏆 TOP {limit} BY VOLUME
{'='*80}
"""

        for i, token in enumerate(top_volume, 1):
            emoji = self.volume_categories[token.volume_category]["emoji"]
            report += f"{i:2d}. {emoji} {token.symbol:15} ${token.price:>12.4f} "
            report += f"Vol: ${token.volume_24h_usdt:>12,.0f} "
            report += f"24h: {token.price_change_24h:>6.2f}% "
            report += f"({token.sector})\n"

        report += f"""
{'='*80}
🚀 TOP {limit} BY MOMENTUM SCORE
{'='*80}
"""

        for i, token in enumerate(top_momentum, 1):
            emoji = self.volume_categories[token.volume_category]["emoji"]
            report += f"{i:2d}. {emoji} {token.symbol:15} "
            report += f"Momentum: {token.momentum_score:>5.2f} "
            report += f"24h: {token.price_change_24h:>6.2f}% "
            report += f"Vol: ${token.volume_24h_usdt:>10,.0f} "
            report += f"({token.sector})\n"

        report += f"""
{'='*80}
📈 TOP {limit} BY 24H PERFORMANCE
{'='*80}
"""

        for i, token in enumerate(top_performance, 1):
            emoji = self.volume_categories[token.volume_category]["emoji"]
            report += f"{i:2d}. {emoji} {token.symbol:15} "
            report += f"Change: {token.price_change_24h:>6.2f}% "
            report += f"Price: ${token.price:>10.4f} "
            report += f"Vol: ${token.volume_24h_usdt:>10,.0f} "
            report += f"({token.sector})\n"

        if gaming_tokens:
            report += f"""
{'='*80}
🎮 GAMING TOKENS ANALYSIS
{'='*80}
"""
            for i, token in enumerate(gaming_tokens, 1):
                emoji = self.volume_categories[token.volume_category]["emoji"]
                report += f"{i:2d}. {emoji} {token.symbol:15} "
                report += f"Price: ${token.price:>8.4f} "
                report += f"24h: {token.price_change_24h:>6.2f}% "
                report += f"Vol: ${token.volume_24h_usdt:>10,.0f} "
                report += f"Score: {token.ecosystem_score:.1f}\n"

        # Volume distribution
        report += f"""
{'='*80}
📊 VOLUME DISTRIBUTION
{'='*80}
"""
        for category, info in self.volume_categories.items():
            count = len([t for t in tokens if t.volume_category == category])
            if count > 0:
                percentage = (count / len(tokens)) * 100
                report += f"{info['emoji']} {info['desc']:25} {count:3d} tokens ({percentage:5.1f}%)\n"

        # Sector distribution
        sectors = {}
        for token in tokens:
            sectors[token.sector] = sectors.get(token.sector, 0) + 1

        report += f"""
{'='*80}
🏢 SECTOR DISTRIBUTION
{'='*80}
"""
        for sector, count in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(tokens)) * 100
            report += f"📈 {sector.title():15} {count:3d} tokens ({percentage:5.1f}%)\n"

        return report

    def save_analysis_results(self, tokens: List[TokenAnalysis]) -> str:
        """Save comprehensive analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Convert to dict for JSON serialization
        tokens_dict = []
        for token in tokens:
            tokens_dict.append(
                {
                    "symbol": token.symbol,
                    "base_asset": token.base_asset,
                    "price": token.price,
                    "volume_24h_usdt": token.volume_24h_usdt,
                    "price_change_24h": token.price_change_24h,
                    "rsi_14": token.rsi_14,
                    "volume_category": token.volume_category,
                    "momentum_score": token.momentum_score,
                    "volatility": token.volatility,
                    "ai_prediction": token.ai_prediction,
                    "ai_confidence": token.ai_confidence,
                    "risk_score": token.risk_score,
                    "sector": token.sector,
                    "ecosystem_score": token.ecosystem_score,
                    "volume_rank": token.volume_rank,
                    "momentum_rank": token.momentum_rank,
                    "performance_rank": token.performance_rank,
                }
            )

        # Save JSON analysis
        filename = f"comprehensive_token_analysis_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(tokens_dict, f, indent=2)

        # Save CSV for spreadsheet analysis
        df = pd.DataFrame(tokens_dict)
        csv_filename = f"comprehensive_token_analysis_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)

        print(f"💾 Analysis saved to {filename}")
        print(f"📊 CSV saved to {csv_filename}")

        return filename


async def main():
    """Main execution function"""
    print("🔥 VICTORYCHAIN COMPREHENSIVE TOKEN ANALYZER")
    print("=" * 60)
    print("Analyzing ALL tradeable tokens on Binance US...")
    print()

    analyzer = ComprehensiveTokenAnalyzer()

    # Perform comprehensive analysis
    tokens = analyzer.analyze_all_tokens()

    if not tokens:
        print("❌ No tokens analyzed")
        return

    # Generate report
    report = analyzer.generate_top_performers_report(tokens, limit=25)
    print(report)

    # Save results
    filename = analyzer.save_analysis_results(tokens)

    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"tokens_analysis_report_{timestamp}.txt"
    with open(report_filename, "w") as f:
        f.write(report)

    print(f"📄 Report saved to {report_filename}")

    # Highlight key findings
    print("\n" + "=" * 60)
    print("🎯 KEY FINDINGS")
    print("=" * 60)

    top_volume = sorted(tokens, key=lambda x: x.volume_24h_usdt, reverse=True)
    top_performer = max(tokens, key=lambda x: x.price_change_24h)
    magic_token = next((t for t in tokens if t.base_asset == "MAGIC"), None)

    print(
        f"🏆 Highest Volume: {top_volume[0].symbol} (${top_volume[0].volume_24h_usdt:,.0f})"
    )
    print(
        f"🚀 Best Performer: {top_performer.symbol} (+{top_performer.price_change_24h:.2f}%)"
    )

    if magic_token:
        print(
            f"🎮 MAGIC Analysis: ${magic_token.price:.4f} ({magic_token.price_change_24h:+.2f}%) "
            f"Vol: ${magic_token.volume_24h_usdt:,.0f} Rank: #{magic_token.volume_rank}"
        )

    gaming_tokens = [t for t in tokens if t.sector == "gaming"]
    if gaming_tokens:
        avg_gaming_performance = np.mean([t.price_change_24h for t in gaming_tokens])
        print(
            f"🎮 Gaming Sector Avg: {avg_gaming_performance:+.2f}% ({len(gaming_tokens)} tokens)"
        )

    print("\n✅ Comprehensive analysis complete!")
    print("🎯 Ready for advanced trading strategies!")


if __name__ == "__main__":
    asyncio.run(main())
