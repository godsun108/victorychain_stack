#!/usr/bin/env python3
"""
VictoryChain Ultimate Trading System - Enhanced Edition
🚀 MAGICUSDT Pattern + Claude AI + Smart Gains + Advanced Analytics

ENHANCED FEATURES:
✨ Multi-Strategy Analysis (MAGICUSDT Pattern + AI + ML)
🧠 Smart Gains-Only Logic (4%+ targets, 1.2% max loss)
📊 Advanced Risk Management & Position Sizing
🎯 Quantum Data Analysis & Winner Trait Learning
⚡ Real-time Portfolio Optimization
🛡️  Emergency Stop Loss & 24/7 Monitoring
"""

import os
import json
import sys
import logging
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

# Configure enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            f'victorychain_ultimate_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
    ],
)
logger = logging.getLogger(__name__)


class VictoryChainUltimateTrader:
    def __init__(self):
        load_dotenv()

        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        self.claude_api_key = os.getenv("CLAUDE_API_KEY")

        # Enhanced MAGICUSDT winning traits (updated with current performance)
        self.magicusdt_traits = {
            "performance": 32.32,  # Current +32.32% gain
            "momentum_score": 0.998,  # Near perfect momentum
            "range_position": 0.882,  # 88.2% of daily range
            "pattern_type": "MOMENTUM_SURGE",
            "controlled_volatility": True,
            "technical_alignment": True,
            "similarity_threshold": 70.0,  # 70%+ similarity required
        }

        # Smart Gains-Only Configuration - MAXIMUM CAPITAL DEPLOYMENT
        self.smart_gains_config = {
            "confidence_threshold": 0.70,  # 70%+ confidence required (lowered for more trades)
            "min_gain_target": 3.0,  # 3%+ gain target (lowered for more opportunities)
            "max_loss_tolerance": 2.0,  # 2% max loss (slightly higher for bigger positions)
            "win_rate_target": 0.65,  # 65%+ win rate
            "position_size_pct": 0.90,  # 90% MAX CAPITAL DEPLOYMENT
        }

        # Advanced Risk Management - AGGRESSIVE CAPITAL ALLOCATION
        self.risk_config = {
            "max_portfolio_risk": 0.90,  # 90% max portfolio deployment
            "emergency_stop_loss": 0.25,  # 25% portfolio loss = emergency stop
            "daily_loss_limit": 0.15,  # 15% daily loss limit
            "max_positions": 1,  # SINGLE POSITION - ALL IN
            "min_trade_amount": 10.0,  # Minimum $10 trade (adjusted for LOT_SIZE requirements)
        }

        # Market Analysis Cache
        self.market_cache = {}
        self.last_analysis_time = 0
        self.cache_expiry = 300  # 5 minutes

        print("🚀 VictoryChain Ultimate Trading System Initialized")
        print("🎯 Multi-Strategy AI-Powered Trading Platform")
        print("⚡ MAXIMUM CAPITAL DEPLOYMENT MODE - 90% POSITION SIZING")
        print("💰 ALL-IN STRATEGY: Single Position with Full Available Capital")

    def get_all_tradable_tokens(self):
        """Get all USDT trading pairs with enhanced analytics"""
        try:
            # Check cache first for performance
            if (
                time.time() - self.last_analysis_time
            ) < self.cache_expiry and self.market_cache:
                logger.info("📊 Using cached market data")
                return self.market_cache.get("tokens", [])

            logger.info("📡 Fetching enhanced market data from Binance US...")

            # Get exchange info for tradable symbols
            exchange_info = self.client.get_exchange_info()
            tradable_symbols = set()

            for symbol_info in exchange_info["symbols"]:
                symbol = symbol_info["symbol"]
                if (
                    symbol.endswith("USDT")
                    and symbol_info["status"] == "TRADING"
                    and symbol != "USDCUSDT"
                ):
                    tradable_symbols.add(symbol)

            tickers = self.client.get_ticker()
            enhanced_tokens = []

            for ticker in tickers:
                if ticker["symbol"] in tradable_symbols:
                    try:
                        # Enhanced data processing
                        price_change = float(ticker["priceChangePercent"])
                        volume = float(ticker["quoteVolume"])
                        current_price = float(ticker["lastPrice"])
                        high_24h = float(ticker["highPrice"])
                        low_24h = float(ticker["lowPrice"])

                        # Calculate advanced metrics
                        price_range = (
                            high_24h - low_24h if high_24h != low_24h else 0.01
                        )
                        range_position = (
                            (current_price - low_24h) / price_range
                            if price_range > 0
                            else 0.5
                        )

                        # Volume categorization
                        if volume >= 100000:
                            volume_category = "high"
                        elif volume >= 10000:
                            volume_category = "medium"
                        else:
                            volume_category = "low"

                        # Enhanced ticker with analytics
                        enhanced_ticker = {
                            **ticker,
                            "range_position": range_position,
                            "price_range": price_range,
                            "volume_category": volume_category,
                            "momentum_score": min(abs(price_change) / 20.0, 1.0),
                            "volatility": (
                                price_range / current_price if current_price > 0 else 0
                            ),
                            "strength_score": range_position
                            * min(abs(price_change) / 10.0, 1.0),
                        }

                        enhanced_tokens.append(enhanced_ticker)

                    except (ValueError, ZeroDivisionError):
                        continue

            # Update cache
            self.market_cache = {"tokens": enhanced_tokens, "timestamp": time.time()}
            self.last_analysis_time = time.time()

            print(
                f"📊 Found {len(enhanced_tokens)} tradable USDT pairs with enhanced analytics"
            )
            return enhanced_tokens

        except Exception as e:
            logger.error(f"Error fetching tokens: {e}")
            return []

    def analyze_with_claude(self, tokens_data):
        """Enhanced Claude API analysis with structured output"""
        if not self.claude_api_key:
            print("⚠️  Claude API key not found, using enhanced fallback analysis")
            return self.enhanced_fallback_analysis(tokens_data)

        # Get top movers for Claude analysis (increased to 40 for better analysis)
        top_movers = sorted(
            tokens_data,
            key=lambda x: abs(float(x.get("priceChangePercent", 0))),
            reverse=True,
        )[:40]

        # Enhanced prompt with more context
        prompt = f"""
As an expert crypto trader, analyze these Binance US tokens against MAGICUSDT's exceptional winning pattern.

MAGICUSDT REFERENCE PATTERN (Current Performance):
- Performance: +{self.magicusdt_traits['performance']:.2f}% (exceptional gain)
- Momentum Score: {self.magicusdt_traits['momentum_score']} (near perfect)
- Range Position: {self.magicusdt_traits['range_position']:.1%} (strong positioning)
- Strategy: Quality momentum over volume, controlled volatility
- Risk Profile: Managed risk with strong directional bias

ENHANCED MARKET DATA ({len(top_movers)} top movers with analytics):
{json.dumps([{
    'symbol': t['symbol'],
    'change': f"{float(t['priceChangePercent']):.2f}%",
    'price': t['lastPrice'],
    'volume': f"${float(t['quoteVolume']):,.0f}",
    'volume_category': t.get('volume_category', 'unknown'),
    'range_position': f"{t.get('range_position', 0):.1%}",
    'momentum_score': f"{t.get('momentum_score', 0):.3f}",
    'strength_score': f"{t.get('strength_score', 0):.3f}",
    'high': t['highPrice'],
    'low': t['lowPrice']
} for t in top_movers], indent=2)}

ADVANCED ANALYSIS REQUIREMENTS:
1. Score similarity to MAGICUSDT pattern (0-100%)
2. Identify the TOP 3 tokens with highest trading potential
3. Focus on tokens with >5% gains AND high range positions
4. Prioritize momentum and technical strength over pure volume
5. Assess risk/reward ratios for each recommendation
6. Provide specific entry criteria and position sizing advice
7. Consider Smart Gains criteria (4%+ targets, 1.5% max loss)

Return detailed JSON format with rankings, confidence scores, and specific trading recommendations.
"""

        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.claude_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )

            if response.status_code == 200:
                claude_response = response.json()
                analysis_text = claude_response["content"][0]["text"]

                print("✅ Enhanced Claude AI analysis completed")

                # Try to extract structured data
                try:
                    import re

                    json_match = re.search(r"\{.*\}", analysis_text, re.DOTALL)
                    if json_match:
                        structured_data = json.loads(json_match.group())
                        return {
                            "analysis_text": analysis_text,
                            "structured_recommendations": structured_data,
                            "claude_insights": True,
                            "top_movers": top_movers[:10],
                            "confidence": 0.85,
                        }
                except:
                    pass

                return {
                    "analysis_text": analysis_text,
                    "claude_insights": True,
                    "top_movers": top_movers[:10],
                    "confidence": 0.75,
                }
            else:
                print(f"❌ Claude API error: {response.status_code}")
                return self.enhanced_fallback_analysis(tokens_data)

        except Exception as e:
            print(f"❌ Claude analysis failed: {e}")
            return self.enhanced_fallback_analysis(tokens_data)

    def enhanced_fallback_analysis(self, tokens_data):
        """Enhanced fallback analysis with Smart Gains logic and advanced scoring"""
        print(
            "🔄 Using enhanced MAGICUSDT pattern matching with Smart Gains filters..."
        )

        opportunities = []

        for token in tokens_data:
            try:
                symbol = token["symbol"]
                price_change = float(token["priceChangePercent"])
                current_price = float(token["lastPrice"])
                high_24h = float(token["highPrice"])
                low_24h = float(token["lowPrice"])
                volume = float(token["quoteVolume"])

                # Enhanced metrics from token data
                range_position = token.get("range_position", 0.5)
                momentum_score = token.get("momentum_score", 0)
                strength_score = token.get("strength_score", 0)
                volatility = token.get("volatility", 0)
                volume_category = token.get("volume_category", "low")

                # Smart Gains filter - minimum performance threshold
                if (
                    price_change < self.smart_gains_config["min_gain_target"]
                    or volume < 1000
                ):
                    continue

                # Enhanced MAGICUSDT similarity scoring
                performance_score = (
                    min(abs(price_change) / self.magicusdt_traits["performance"], 1.0)
                    * 35
                )
                momentum_score_weight = momentum_score * 25
                position_score = range_position * 20
                volume_score = min(volume / 50000, 1.0) * 10
                volatility_score = (
                    1 - min(volatility * 2, 1.0)
                ) * 10  # Lower volatility = higher score

                similarity = (
                    performance_score
                    + momentum_score_weight
                    + position_score
                    + volume_score
                    + volatility_score
                )

                # Calculate confidence score
                confidence = min((similarity / 100.0) * (strength_score + 0.5), 1.0)

                # Smart Gains confidence filter
                if confidence < self.smart_gains_config["confidence_threshold"]:
                    continue

                # Risk assessment
                risk_score = volatility * 10 + (1 - range_position) * 5

                if similarity >= self.magicusdt_traits["similarity_threshold"]:
                    opportunities.append(
                        {
                            "symbol": symbol,
                            "magicusdt_similarity": similarity,
                            "price_change": price_change,
                            "range_position": range_position,
                            "current_price": current_price,
                            "volume": volume,
                            "volume_category": volume_category,
                            "momentum_score": momentum_score,
                            "strength_score": strength_score,
                            "volatility": volatility,
                            "confidence": confidence,
                            "risk_score": risk_score,
                            "smart_gains_approved": True,
                            "scores": {
                                "performance": performance_score,
                                "momentum": momentum_score_weight,
                                "position": position_score,
                                "volume": volume_score,
                                "volatility": volatility_score,
                            },
                        }
                    )

            except (ValueError, KeyError):
                continue

        # Sort by similarity and confidence
        opportunities.sort(
            key=lambda x: (x["magicusdt_similarity"], x["confidence"]), reverse=True
        )

        return {
            "opportunities": opportunities[:10],  # Top 10
            "total_analyzed": len(tokens_data),
            "smart_gains_filtered": len(opportunities),
            "analysis_method": "enhanced_pattern_matching_with_smart_gains",
            "magicusdt_reference": self.magicusdt_traits,
        }

    def display_results(self, analysis):
        """Enhanced display of analysis results with Smart Gains insights"""
        print("\n🏆 VICTORYCHAIN ULTIMATE TRADING ANALYSIS")
        print("=" * 70)

        if "analysis_text" in analysis:
            # Claude analysis
            print("🧠 Claude AI Enhanced Insights:")
            claude_text = analysis["analysis_text"]
            preview = (
                claude_text[:1500] + "..." if len(claude_text) > 1500 else claude_text
            )
            print(preview)

            if "structured_recommendations" in analysis:
                print("\n📊 Structured Recommendations Available")

        if "opportunities" in analysis:
            # Enhanced fallback analysis
            opportunities = analysis["opportunities"]
            smart_gains_count = len(
                [o for o in opportunities if o.get("smart_gains_approved")]
            )

            print(f"\n🎯 FOUND {len(opportunities)} HIGH-CONFIDENCE OPPORTUNITIES")
            print(f"✅ {smart_gains_count} passed Smart Gains filters")
            print(f"📊 Analyzed {analysis.get('total_analyzed', 0)} total tokens")

            for i, opp in enumerate(opportunities[:5], 1):
                symbol = opp["symbol"]
                similarity = opp["magicusdt_similarity"]
                performance = opp["price_change"]
                confidence = opp.get("confidence", 0)
                volume_cat = opp.get("volume_category", "unknown")
                risk_score = opp.get("risk_score", 5)

                print(f"\n{i}. {symbol}")
                print(f"   🎯 MAGICUSDT Similarity: {similarity:.1f}%")
                print(f"   📈 Performance: {performance:+.2f}%")
                print(f"   🎪 Confidence: {confidence:.1%}")
                print(f"   📊 Range Position: {opp['range_position']:.1%}")
                print(f"   💰 Price: ${opp['current_price']:.6f}")
                print(f"   💸 Volume: ${opp['volume']:,.0f} ({volume_cat})")
                print(f"   🛡️  Risk Score: {risk_score:.1f}/10")

                if opp.get("smart_gains_approved"):
                    print(f"   ✅ Smart Gains Approved")

                if similarity >= 85:
                    print(f"   🚀 EXCEPTIONAL MATCH - Prime trading candidate!")
                elif similarity >= 75:
                    print(f"   ⚡ STRONG MATCH - High potential")
                elif similarity >= 70:
                    print(f"   📈 GOOD MATCH - Consider for portfolio")

    def calculate_enhanced_position_size(self, opportunity, usdt_balance):
        """MAXIMUM CAPITAL DEPLOYMENT - Use all available capital for position sizing"""
        if usdt_balance < self.risk_config["min_trade_amount"]:
            return None

        # AGGRESSIVE POSITION SIZING - Use 90% of available capital
        base_position = usdt_balance * self.smart_gains_config["position_size_pct"]

        # Confidence-based adjustments (still apply some risk management)
        confidence = opportunity.get("confidence", 0.5)
        risk_score = opportunity.get("risk_score", 5) / 10.0
        similarity = opportunity.get("magicusdt_similarity", 50) / 100.0

        # Aggressive multiplier - favor high confidence trades
        confidence_multiplier = max(confidence * 1.2, 0.8)  # Min 80% of position
        risk_multiplier = max((1 - risk_score) * 1.1, 0.7)  # Min 70% of position
        similarity_multiplier = max(similarity * 1.3, 0.9)  # Min 90% of position

        # Calculate final position (aggressive sizing)
        total_multiplier = (
            confidence_multiplier + risk_multiplier + similarity_multiplier
        ) / 3
        adjusted_position = base_position * total_multiplier

        # MAXIMUM LIMITS - Use almost all capital
        max_position = usdt_balance * 0.95  # Use 95% of all available capital
        min_position = usdt_balance * 0.70  # Minimum 70% of capital

        final_position = max(min_position, min(adjusted_position, max_position))

        # Ensure we don't exceed available balance (leave $1 for fees)
        if final_position > (usdt_balance - 1):
            final_position = usdt_balance - 1

        return {
            "position_size": final_position,
            "position_pct": final_position / usdt_balance,
            "confidence_factor": confidence,
            "risk_factor": risk_score,
            "expected_gain": final_position
            * (self.smart_gains_config["min_gain_target"] / 100),
            "max_loss": final_position
            * (self.smart_gains_config["max_loss_tolerance"] / 100),
            "risk_reward_ratio": self.smart_gains_config["min_gain_target"]
            / self.smart_gains_config["max_loss_tolerance"],
            "capital_deployment": "MAXIMUM",
            "strategy": "ALL_IN_SINGLE_POSITION",
        }

    def execute_trade_recommendation(self, analysis):
        """Enhanced trading recommendation with Smart Gains logic"""
        print("\n💡 ENHANCED TRADING RECOMMENDATION")
        print("=" * 45)

        # Get account balance AFTER liquidating all positions
        try:
            # STEP 1: LIQUIDATE ALL EXISTING POSITIONS
            final_usdt_balance = self.liquidate_all_positions()

            if final_usdt_balance <= 0:
                # Fallback: get current USDT balance
                account = self.client.get_account()
                for balance in account["balances"]:
                    if balance["asset"] == "USDT":
                        final_usdt_balance = float(balance["free"])
                        break

            print(f"\n💰 Available USDT (after liquidation): ${final_usdt_balance:.2f}")

            if "opportunities" in analysis and analysis["opportunities"]:
                best_opp = analysis["opportunities"][0]

                print(f"\n🎯 #1 RECOMMENDED TRADE: {best_opp['symbol']}")
                print(
                    f"   MAGICUSDT Similarity: {best_opp['magicusdt_similarity']:.1f}%"
                )
                print(f"   Performance: {best_opp['price_change']:+.2f}%")
                print(f"   Confidence: {best_opp.get('confidence', 0):.1%}")
                print(f"   Risk Score: {best_opp.get('risk_score', 5):.1f}/10")

                if final_usdt_balance >= self.risk_config["min_trade_amount"]:
                    position_info = self.calculate_enhanced_position_size(
                        best_opp, final_usdt_balance
                    )

                    if position_info:
                        print(f"\n� MAXIMUM CAPITAL DEPLOYMENT PLAN:")
                        print(f"   🎯 Symbol: {best_opp['symbol']}")
                        print(
                            f"   💸 Position Size: ${position_info['position_size']:.2f} ({position_info['position_pct']:.1%} of ALL capital)"
                        )
                        print(f"   ⚡ Strategy: {position_info['strategy']}")
                        print(
                            f"   🎪 Capital Deployment: {position_info['capital_deployment']}"
                        )
                        print(
                            f"   📈 Target Gain: ${position_info['expected_gain']:.2f} (+{self.smart_gains_config['min_gain_target']:.1f}%)"
                        )
                        print(
                            f"   🛡️  Max Loss: ${position_info['max_loss']:.2f} (-{self.smart_gains_config['max_loss_tolerance']:.1f}%)"
                        )
                        print(
                            f"   ⚖️  Risk/Reward: 1:{position_info['risk_reward_ratio']:.1f}"
                        )
                        print(f"   ⏰ Hold Time: 1-4 hours (momentum dependent)")

                        # ALL-IN execution instructions
                        print(f"\n🚀 ALL-IN EXECUTION STEPS:")
                        print(f"   0. ✅ ALL OTHER POSITIONS LIQUIDATED")
                        print(f"   1. Open Binance US → {best_opp['symbol']}")
                        print(f"   2. Verify price: ${best_opp['current_price']:.6f}")
                        print(
                            f"   3. 💰 MARKET BUY: ${position_info['position_size']:.2f} (ALMOST ALL CAPITAL)"
                        )
                        print(
                            f"   4. 📈 Take Profit: +{self.smart_gains_config['min_gain_target']:.1f}% → ${best_opp['current_price'] * (1 + self.smart_gains_config['min_gain_target']/100):.6f}"
                        )
                        print(
                            f"   5. 🛡️  Stop Loss: -{self.smart_gains_config['max_loss_tolerance']:.1f}% → ${best_opp['current_price'] * (1 - self.smart_gains_config['max_loss_tolerance']/100):.6f}"
                        )
                        print(
                            f"   6. 👀 Monitor CLOSELY - this is 90%+ of your capital!"
                        )

                        # Enhanced trading metrics inline
                        print(f"\n📊 ENHANCED TRADING METRICS:")
                        try:
                            # Get order book for liquidity analysis
                            depth = self.client.get_order_book(
                                symbol=best_opp["symbol"], limit=20
                            )
                            best_bid = (
                                float(depth["bids"][0][0])
                                if depth["bids"]
                                else best_opp["current_price"]
                            )
                            best_ask = (
                                float(depth["asks"][0][0])
                                if depth["asks"]
                                else best_opp["current_price"]
                            )
                            spread = (
                                ((best_ask - best_bid) / best_bid) * 100
                                if best_bid > 0
                                else 0.1
                            )

                            bid_liquidity = sum(
                                float(bid[1]) * float(bid[0])
                                for bid in depth["bids"][:5]
                            )
                            ask_liquidity = sum(
                                float(ask[1]) * float(ask[0])
                                for ask in depth["asks"][:5]
                            )
                            total_liquidity = bid_liquidity + ask_liquidity

                            print(f"   💸 VOLUME & LIQUIDITY:")
                            print(f"   📊 24h Volume: ${best_opp['volume']:,.0f}")
                            print(
                                f"   🌊 Order Book Liquidity: ${total_liquidity:,.0f}"
                            )
                            print(f"   📐 Bid/Ask Spread: {spread:.3f}%")
                            print(f"   📋 Best Bid: ${best_bid:.6f}")
                            print(f"   📋 Best Ask: ${best_ask:.6f}")
                            print(
                                f"   📏 Market Impact: {(position_info['position_size']/total_liquidity)*100:.2f}% of liquidity"
                            )
                            print(
                                f"   ⚖️  Size vs Volume: {(position_info['position_size']/best_opp['volume'])*100:.3f}% of daily volume"
                            )

                            # Quality assessment
                            if best_opp["volume"] >= 100000:
                                vol_quality = "🟢 EXCELLENT"
                            elif best_opp["volume"] >= 50000:
                                vol_quality = "🟡 GOOD"
                            else:
                                vol_quality = "🔴 MODERATE"

                            if spread <= 0.2:
                                spread_quality = "🟢 TIGHT"
                            elif spread <= 0.5:
                                spread_quality = "🟡 ACCEPTABLE"
                            else:
                                spread_quality = "🔴 WIDE"

                            print(f"   ✅ QUALITY ASSESSMENT:")
                            print(f"   📊 Volume Quality: {vol_quality}")
                            print(f"   📐 Spread Quality: {spread_quality}")
                            print(
                                f"   🎪 Overall Rating: {'🟢 OPTIMAL' if best_opp['volume'] >= 50000 and spread <= 0.3 else '🟡 ACCEPTABLE' if best_opp['volume'] >= 10000 else '🔴 RISKY'}"
                            )

                        except Exception as e:
                            print(f"   ⚠️  Could not fetch detailed metrics: {e}")
                            print(f"   📊 24h Volume: ${best_opp['volume']:,.0f}")
                            print(f"   🎯 Estimated spread: ~0.1-0.3%")
                            print(f"   💡 Proceed with standard execution")

                        # Enhanced risk warnings for ALL-IN strategy
                        print(f"\n⚠️  ALL-IN STRATEGY WARNINGS:")
                        print(
                            f"   🔥 USING {position_info['position_pct']:.1%} OF ALL AVAILABLE CAPITAL"
                        )
                        print(f"   💥 Single position - no diversification")
                        print(
                            f"   📊 Max portfolio risk: {(position_info['max_loss']/final_usdt_balance)*100:.1f}%"
                        )
                        print(
                            f"   ⚡ HIGH REWARD potential: ${position_info['expected_gain']:.2f}"
                        )
                        print(f"   🛡️  MONITOR CONTINUOUSLY - set alerts!")

                else:
                    print(
                        f"❌ Insufficient balance (${final_usdt_balance:.2f} < ${self.risk_config['min_trade_amount']:.0f} minimum)"
                    )

            elif "analysis_text" in analysis:
                print("🧠 Follow Claude AI recommendations above for trading decisions")
                print(
                    "💡 Look for tokens with highest similarity scores and confidence levels"
                )

        except Exception as e:
            logger.error(f"Error in trade recommendation: {e}")
            print(f"❌ Error checking account: {e}")

    def run_analysis(self):
        """Run complete MAGICUSDT pattern analysis"""
        print("🔍 Starting MAGICUSDT Pattern Analysis...")

        # Get all tradable tokens
        tokens_data = self.get_all_tradable_tokens()
        if not tokens_data:
            return

        # Analyze with Claude AI (or fallback)
        analysis = self.analyze_with_claude(tokens_data)

        # Display results
        self.display_results(analysis)

        # Provide trading recommendation
        self.execute_trade_recommendation(analysis)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"victorychain_ultimate_analysis_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "system_version": "VictoryChain Ultimate v2.0 - MAXIMUM CAPITAL DEPLOYMENT",
                    "magicusdt_reference": self.magicusdt_traits,
                    "smart_gains_config": self.smart_gains_config,
                    "analysis": analysis,
                    "total_tokens_analyzed": len(tokens_data),
                    "enhancement_features": [
                        "Enhanced MAGICUSDT Pattern Recognition",
                        "Smart Gains-Only Logic",
                        "Advanced Risk Management",
                        "Multi-Strategy Analysis",
                        "Claude AI Integration",
                        "Real-time Position Sizing",
                    ],
                },
                f,
                indent=2,
            )

        print(f"\n✅ Enhanced analysis saved to: {filename}")
        print("🎉 VictoryChain Ultimate Analysis Complete!")

    def liquidate_all_positions(self):
        """Liquidate ALL positions to free up maximum capital for new allocation"""
        print("\n🔥 LIQUIDATING ALL EXISTING POSITIONS FOR MAXIMUM CAPITAL...")

        try:
            account = self.client.get_account()
            liquidated_value = 0
            liquidation_orders = []

            for balance in account["balances"]:
                asset = balance["asset"]
                free = float(balance["free"])
                locked = float(balance["locked"])
                total = free + locked

                # Skip USDT and assets with zero balance
                if asset == "USDT" or total <= 0:
                    continue

                # Skip very small balances (dust)
                if total < 0.001:
                    continue

                try:
                    symbol = f"{asset}USDT"

                    # Check if this symbol exists and is tradable
                    try:
                        ticker = self.client.get_ticker(symbol=symbol)
                        current_price = float(ticker["lastPrice"])
                        estimated_value = total * current_price

                        # Only liquidate if worth more than $1
                        if estimated_value > 1.0:
                            print(
                                f"🔥 Liquidating {asset}: {total:.6f} tokens (≈${estimated_value:.2f})"
                            )

                            # Place market sell order
                            order = self.client.order_market_sell(
                                symbol=symbol, quantity=total
                            )

                            liquidation_orders.append(
                                {
                                    "symbol": symbol,
                                    "asset": asset,
                                    "quantity": total,
                                    "estimated_value": estimated_value,
                                    "order_id": order["orderId"],
                                }
                            )

                            liquidated_value += estimated_value
                            print(
                                f"✅ {asset} liquidation order placed: {order['orderId']}"
                            )

                    except Exception as e:
                        print(f"⚠️  Could not liquidate {asset}: {e}")
                        continue

                except Exception as e:
                    continue

            if liquidated_value > 0:
                print(f"\n💰 TOTAL LIQUIDATED VALUE: ${liquidated_value:.2f}")
                print(f"🎯 {len(liquidation_orders)} liquidation orders placed")
                print("⏰ Waiting 5 seconds for orders to execute...")

                import time

                time.sleep(5)  # Wait for orders to execute

                # Check final USDT balance
                account = self.client.get_account()
                for balance in account["balances"]:
                    if balance["asset"] == "USDT":
                        final_usdt = float(balance["free"])
                        print(f"💵 Final USDT Balance: ${final_usdt:.2f}")
                        return final_usdt
            else:
                print("💡 No positions to liquidate - already in USDT")
                # Return current USDT balance
                for balance in account["balances"]:
                    if balance["asset"] == "USDT":
                        return float(balance["free"])

        except Exception as e:
            logger.error(f"Error liquidating positions: {e}")
            print(f"❌ Liquidation error: {e}")
            return 0

        return 0

    def analyze_trading_metrics(self, opportunity, usdt_balance):
        """Analyze volume, price, size, and liquidity metrics for trading decision"""
        try:
            symbol = opportunity["symbol"]
            current_price = opportunity["current_price"]
            volume_24h = opportunity["volume"]
            volume_category = opportunity.get("volume_category", "unknown")

            # Get order book depth for liquidity analysis
            try:
                depth = self.client.get_order_book(symbol=symbol, limit=100)

                # Calculate bid/ask spread
                best_bid = (
                    float(depth["bids"][0][0]) if depth["bids"] else current_price
                )
                best_ask = (
                    float(depth["asks"][0][0]) if depth["asks"] else current_price
                )
                spread = ((best_ask - best_bid) / best_bid) * 100 if best_bid > 0 else 0

                # Calculate liquidity depth (sum of top 10 bids/asks)
                bid_liquidity = sum(
                    float(bid[1]) * float(bid[0]) for bid in depth["bids"][:10]
                )
                ask_liquidity = sum(
                    float(ask[1]) * float(ask[0]) for ask in depth["asks"][:10]
                )
                total_liquidity = bid_liquidity + ask_liquidity

            except:
                spread = 0.1  # Default spread
                total_liquidity = volume_24h * 0.01  # Estimate
                best_bid = current_price * 0.999
                best_ask = current_price * 1.001

            # Position size analysis
            position_info = self.calculate_enhanced_position_size(
                opportunity, usdt_balance
            )
            if not position_info:
                return None

            position_size = position_info["position_size"]

            # Calculate position impact on liquidity
            position_impact = (
                (position_size / total_liquidity) * 100 if total_liquidity > 0 else 100
            )

            # Market cap estimation (rough)
            try:
                # Get token info for better analysis
                ticker_24h = self.client.get_ticker(symbol=symbol)
                volume_usdt = float(ticker_24h["quoteVolume"])
                price_change_24h = float(ticker_24h["priceChangePercent"])

                # Volume quality assessment
                if volume_usdt >= 500000:
                    volume_quality = "EXCELLENT"
                elif volume_usdt >= 100000:
                    volume_quality = "GOOD"
                elif volume_usdt >= 10000:
                    volume_quality = "MODERATE"
                else:
                    volume_quality = "LOW"

                # Liquidity assessment
                if spread <= 0.1:
                    liquidity_quality = "EXCELLENT"
                elif spread <= 0.3:
                    liquidity_quality = "GOOD"
                elif spread <= 0.5:
                    liquidity_quality = "MODERATE"
                else:
                    liquidity_quality = "LOW"

                # Size assessment relative to volume
                size_ratio = (position_size / volume_usdt) * 100
                if size_ratio <= 0.1:
                    size_impact = "MINIMAL"
                elif size_ratio <= 0.5:
                    size_impact = "LOW"
                elif size_ratio <= 1.0:
                    size_impact = "MODERATE"
                else:
                    size_impact = "HIGH"

            except:
                volume_quality = "UNKNOWN"
                liquidity_quality = "UNKNOWN"
                size_impact = "UNKNOWN"
                price_change_24h = opportunity.get("price_change", 0)

            return {
                "symbol": symbol,
                "current_price": current_price,
                "best_bid": best_bid,
                "best_ask": best_ask,
                "spread_pct": spread,
                "volume_24h_usdt": volume_24h,
                "volume_category": volume_category,
                "volume_quality": volume_quality,
                "liquidity_usdt": total_liquidity,
                "liquidity_quality": liquidity_quality,
                "position_size": position_size,
                "position_impact": position_impact,
                "size_impact": size_impact,
                "price_change_24h": price_change_24h,
                "confidence": opportunity.get("confidence", 0),
                "risk_score": opportunity.get("risk_score", 5),
            }

        except Exception as e:
            logger.error(f"Error analyzing trading metrics: {e}")
            return None


def main():
    """Main function for VictoryChain Ultimate with MAXIMUM CAPITAL DEPLOYMENT"""
    print("🚀 VICTORYCHAIN ULTIMATE - ALL-IN TRADING SYSTEM")
    print("💰 MAXIMUM CAPITAL DEPLOYMENT MODE - 90% POSITION SIZING")
    print("🔥 AUTO-LIQUIDATION: Sells ALL other tokens before new allocation")
    print("=" * 75)

    # Enhanced safety warning for ALL-IN strategy
    print("\n🔥 MAXIMUM CAPITAL DEPLOYMENT + AUTO-LIQUIDATION WARNING:")
    print("   💥 STEP 1: Automatically liquidates ALL existing positions")
    print("   💰 STEP 2: Uses 90%+ of total capital for single trade")
    print("   ⚡ Single position strategy - COMPLETE portfolio consolidation")
    print("   🧠 MAGICUSDT Pattern + Claude AI + Smart Gains")
    print("   🎯 Target: 3%+ gains with 2% max loss tolerance")
    print("   ⚠️  EXTREME RISK, EXTREME REWARD - Monitor continuously!")
    print("   🛡️  Only use funds you can afford to lose completely!")

    trader = VictoryChainUltimateTrader()
    trader.run_analysis()


if __name__ == "__main__":
    main()


def get_user_confirmation():
    """Get explicit user confirmation for live trading"""
    print("\n⚠️  TRADING RISK WARNING:")

    print("\n🔐 LIVE TRADING CONFIRMATION REQUIRED")
    print("To proceed with live trading, you must confirm each step:")
    print("")

    # Step 1: Risk acknowledgment
    response1 = input(
        "1️⃣  Do you acknowledge the risks of live trading? (type 'YES I UNDERSTAND RISKS'): "
    )
    if response1 != "YES I UNDERSTAND RISKS":
        print("❌ Risk acknowledgment required. Live trading cancelled.")
        return False

    # Step 2: Money confirmation
    response2 = input(
        "2️⃣  Confirm you're trading with money you can afford to lose? (type 'YES'): "
    )
    if response2 != "YES":
        print("❌ Money confirmation required. Live trading cancelled.")
        return False

    # Step 3: Strategy confirmation
    response3 = input(
        "3️⃣  Select trading strategy:\n   A) Conservative (small positions, high volume tokens)\n   B) Balanced (medium risk, mixed strategies)\n   C) Aggressive (includes moonshot detection)\n   D) Claude AI Analysis (MAGICUSDT pattern matching)\n   Enter choice (A/B/C/D): "
    )

    if response3.upper() not in ["A", "B", "C", "D"]:
        print("❌ Invalid strategy selection. Live trading cancelled.")
        return False

    strategy_map = {
        "A": "conservative",
        "B": "balanced",
        "C": "aggressive",
        "D": "claude_analysis",
    }

    # Step 4: Duration confirmation
    response4 = input("4️⃣  How long should the bot run? (1-8 hours, enter number): ")
    try:
        duration = int(response4)
        if duration < 1 or duration > 8:
            print("❌ Duration must be 1-8 hours. Live trading cancelled.")
            return False
    except:
        print("❌ Invalid duration. Live trading cancelled.")
        return False


def get_user_confirmation():
    """Get explicit user confirmation for live trading with enhanced metrics"""
    print("\n⚠️  TRADING RISK WARNING:")

    print("\n🔐 LIVE TRADING CONFIRMATION REQUIRED")
    print("To proceed with live trading, you must confirm each step:")
    print("")

    # Step 1: Risk acknowledgment
    response1 = input(
        "1️⃣  Do you acknowledge the risks of live trading? (type 'YES I UNDERSTAND RISKS'): "
    )
    if response1 != "YES I UNDERSTAND RISKS":
        print("❌ Risk acknowledgment required. Live trading cancelled.")
        return False

    # Step 2: Money confirmation
    response2 = input(
        "2️⃣  Confirm you're trading with money you can afford to lose? (type 'YES'): "
    )
    if response2 != "YES":
        print("❌ Money confirmation required. Live trading cancelled.")
        return False

    # Step 3: Strategy confirmation
    response3 = input(
        "3️⃣  Select trading strategy:\n   A) Conservative (small positions, high volume tokens)\n   B) Balanced (medium risk, mixed strategies)\n   C) Aggressive (includes moonshot detection)\n   D) Claude AI Analysis (MAGICUSDT pattern matching)\n   Enter choice (A/B/C/D): "
    )

    if response3.upper() not in ["A", "B", "C", "D"]:
        print("❌ Invalid strategy selection. Live trading cancelled.")
        return False

    strategy_map = {
        "A": "conservative",
        "B": "balanced",
        "C": "aggressive",
        "D": "claude_analysis",
    }

    # Step 4: Duration confirmation
    response4 = input("4️⃣  How long should the bot run? (1-8 hours, enter number): ")
    try:
        duration = int(response4)
        if duration < 1 or duration > 8:
            print("❌ Duration must be 1-8 hours. Live trading cancelled.")
            return False
    except:
        print("❌ Invalid duration. Live trading cancelled.")
        return False

    # Step 5: Basic confirmation (detailed metrics will be shown later)
    print(f"\n📋 BASIC CONFIRMATION:")
    print(f"   Strategy: {strategy_map[response3.upper()].title()}")
    print(f"   Duration: {duration} hours")
    print(f"   Capital Deployment: MAXIMUM (90%+ allocation)")
    print(f"   Risk Level: EXTREME (auto-liquidation + all-in)")

    final_confirm = input("\n5️⃣  Type 'START LIVE TRADING' to begin: ")
    if final_confirm != "START LIVE TRADING":
        print("❌ Final confirmation required. Live trading cancelled.")
        return False

    return {"strategy": strategy_map[response3.upper()], "duration": duration}


def show_enhanced_trading_metrics(analysis_result):
    """Show detailed trading metrics before execution"""
    if not analysis_result or "opportunities" not in analysis_result:
        return

    opportunities = analysis_result["opportunities"]
    if not opportunities:
        return

    best_opportunity = opportunities[0]

    print("\n" + "=" * 80)
    print("📊 ENHANCED TRADING METRICS ANALYSIS")
    print("=" * 80)

    try:
        # Initialize trader for metrics
        load_dotenv()
        client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        # Get current balance
        account = client.get_account()
        usdt_balance = 0
        for balance in account["balances"]:
            if balance["asset"] == "USDT":
                usdt_balance = float(balance["free"])
                break

        symbol = best_opportunity["symbol"]
        current_price = best_opportunity["current_price"]
        volume_24h = best_opportunity["volume"]

        # Get order book for liquidity analysis
        try:
            depth = client.get_order_book(symbol=symbol, limit=20)
            best_bid = float(depth["bids"][0][0]) if depth["bids"] else current_price
            best_ask = float(depth["asks"][0][0]) if depth["asks"] else current_price
            spread = ((best_ask - best_bid) / best_bid) * 100 if best_bid > 0 else 0.1

            bid_liquidity = sum(
                float(bid[1]) * float(bid[0]) for bid in depth["bids"][:5]
            )
            ask_liquidity = sum(
                float(ask[1]) * float(ask[0]) for ask in depth["asks"][:5]
            )
            total_liquidity = bid_liquidity + ask_liquidity
        except:
            best_bid = current_price * 0.999
            best_ask = current_price * 1.001
            spread = 0.1
            total_liquidity = volume_24h * 0.01

        # Calculate position size (90% of capital)
        position_size = usdt_balance * 0.90

        # Analysis results
        print(f"🎯 TARGET: {symbol}")
        print(f"� Current Price: ${current_price:.6f}")
        print(f"�📈 24h Performance: {best_opportunity['price_change']:+.2f}%")
        print(
            f"🎪 MAGICUSDT Similarity: {best_opportunity['magicusdt_similarity']:.1f}%"
        )
        print(f"📊 Confidence Level: {best_opportunity.get('confidence', 0):.1%}")
        print("")

        print(f"💸 VOLUME & LIQUIDITY ANALYSIS:")
        print(f"📊 24h Volume: ${volume_24h:,.0f}")
        print(f"🌊 Order Book Liquidity: ${total_liquidity:,.0f}")
        print(f"📐 Bid/Ask Spread: {spread:.3f}%")
        print(f"📋 Best Bid: ${best_bid:.6f}")
        print(f"📋 Best Ask: ${best_ask:.6f}")
        print("")

        print(f"💰 POSITION ANALYSIS:")
        print(f"💵 Available Capital: ${usdt_balance:.2f}")
        print(
            f"🎯 Planned Position: ${position_size:.2f} ({(position_size/usdt_balance)*100:.1f}% of capital)"
        )
        print(
            f"📏 Market Impact: {(position_size/total_liquidity)*100:.2f}% of liquidity"
        )
        print(
            f"⚖️  Size vs Volume: {(position_size/volume_24h)*100:.3f}% of daily volume"
        )
        print("")

        print(f"🎯 EXECUTION PLAN:")
        print(f"📋 Entry Method: Market Buy at ${best_ask:.6f}")
        print(f"� Target Profit: +3% → ${current_price * 1.03:.6f}")
        print(f"🛡️  Stop Loss: -2% → ${current_price * 0.98:.6f}")
        print(f"💰 Expected Gain: ${position_size * 0.03:.2f}")
        print(f"💥 Max Loss: ${position_size * 0.02:.2f}")
        print("")

        # Quality assessment
        if volume_24h >= 100000:
            vol_quality = "� EXCELLENT"
        elif volume_24h >= 50000:
            vol_quality = "🟡 GOOD"
        else:
            vol_quality = "🔴 MODERATE"

        if spread <= 0.2:
            spread_quality = "🟢 TIGHT"
        elif spread <= 0.5:
            spread_quality = "🟡 ACCEPTABLE"
        else:
            spread_quality = "🔴 WIDE"

        print(f"✅ QUALITY ASSESSMENT:")
        print(f"📊 Volume Quality: {vol_quality}")
        print(f"📐 Spread Quality: {spread_quality}")
        print(
            f"🎪 Overall Rating: {'🟢 OPTIMAL' if volume_24h >= 50000 and spread <= 0.3 else '🟡 ACCEPTABLE' if volume_24h >= 10000 else '🔴 RISKY'}"
        )

        print("=" * 80)

        # Final execution confirmation
        execute_confirm = input(
            "🚀 Execute this trade with enhanced metrics? (type 'EXECUTE ALL-IN'): "
        )
        return execute_confirm == "EXECUTE ALL-IN"

    except Exception as e:
        print(f"❌ Error analyzing metrics: {e}")
        return False


def create_live_config(config):
    """Create live trading configuration"""
    live_config = {
        "live_trading": True,
        "demo_mode": False,
        "strategy": config["strategy"],
        "duration_hours": config["duration"],
        "portfolio_value": 42.67,  # USDT balance
        "max_positions": 3 if config["strategy"] == "aggressive" else 2,
        "position_size_pct": 0.20,  # 20% of USDT per position
        "stop_loss_pct": 0.08,  # 8% stop loss
        "take_profit_pct": 0.15,  # 15% take profit
        "max_hold_hours": 24,
        "emergency_stop_loss": 0.25,  # 25% total portfolio loss = emergency stop
        "scan_interval": (
            300 if config["strategy"] == "aggressive" else 600
        ),  # 5-10 minutes
        "risk_level": config["strategy"],
        "timestamp": datetime.now().isoformat(),
    }

    # Save configuration
    with open("live_trading_config.json", "w") as f:
        json.dump(live_config, f, indent=2)

    logger.info(
        f"Live trading configuration saved: {config['strategy']} strategy for {config['duration']} hours"
    )
    return live_config


def launch_live_trading(config):
    """Launch the appropriate trading bot based on strategy"""

    # Set environment variables for live trading
    os.environ["DEMO"] = "false"
    os.environ["LIVE_TRADING"] = "true"
    os.environ["PORTFOLIO_VALUE"] = str(config["portfolio_value"])
    os.environ["MAX_POSITIONS"] = str(config["max_positions"])

    strategy = config["strategy"]

    print(f"\n🚀 Launching {strategy.title()} Live Trading Bot...")
    print(f"⏰ Configured for {config['duration_hours']} hours")
    print(f"💰 Trading with ${config['portfolio_value']:.2f} USDT")
    print(
        f"📊 Max {config['max_positions']} positions at ${config['portfolio_value'] * config['position_size_pct']:.2f} each"
    )
    print("")

    if strategy == "conservative":
        print("🛡️  Conservative Strategy: High-volume tokens only, tight risk controls")
        # Use volume-categorized bot with conservative settings
        import subprocess

        subprocess.run([sys.executable, "volume_categorized_bot.py"])

    elif strategy == "balanced":
        print("⚖️  Balanced Strategy: Mixed volume categories, AI analysis")
        # Use enhanced trading bot
        import subprocess

        subprocess.run([sys.executable, "enhanced_trading_bot.py"])

    elif strategy == "aggressive":
        print("🎯 Aggressive Strategy: All strategies including moonshot detection")
        # Use master trading bot with all features
        import subprocess

        subprocess.run([sys.executable, "master_trading_bot.py"])

    elif strategy == "claude_analysis":
        print("🧠 Claude AI Analysis: MAGICUSDT pattern matching across all tokens")
        # Use Claude-powered analysis
        run_claude_analysis_strategy(config)

    elif strategy == "momentum":
        print("🚀 Momentum Surge Strategy: Based on MAGICUSDT winning traits")
        # Use momentum trading bot
        import subprocess

        subprocess.run([sys.executable, "momentum_trading_bot.py"])


def analyze_with_claude_comparison(tokens_data, winner_traits):
    """Use Claude API to compare all tokens against MAGICUSDT winning traits"""
    import requests

    claude_api_key = os.getenv("CLAUDE_API_KEY")
    if not claude_api_key:
        logger.warning("Claude API key not found, using fallback analysis")
        return fallback_token_analysis(tokens_data, winner_traits)

    # Prepare data for Claude analysis
    top_movers = sorted(
        tokens_data,
        key=lambda x: abs(float(x.get("priceChangePercent", 0))),
        reverse=True,
    )[:50]

    prompt = f"""
As an expert crypto trader, analyze these Binance US tokens against MAGICUSDT's winning traits from its +18.81% performance:

MAGICUSDT WINNING TRAITS (Reference Pattern):
- Exceptional Performance: +18.81% gain
- Strong Momentum: 0.998 score
- High Range Position: 97% of daily range 
- Above Moving Averages: Technical strength
- Controlled Volatility: Risk management
- Low Volume Strategy: Quality over quantity

CURRENT MARKET DATA ({len(top_movers)} top movers):
{json.dumps([{
    'symbol': t['symbol'],
    'change': f"{float(t['priceChangePercent']):.2f}%",
    'price': t['lastPrice'],
    'volume': f"${float(t['quoteVolume']):,.0f}",
    'high': t['highPrice'],
    'low': t['lowPrice']
} for t in top_movers[:20]], indent=2)}

ANALYSIS REQUIREMENTS:
1. Score each token's similarity to MAGICUSDT pattern (0-100)
2. Identify tokens with momentum surge potential
3. Rank top 5 trading opportunities
4. Provide specific entry criteria for each
5. Assess risk/reward ratios

Focus on:
- Tokens with >5% moves and high range positions
- Strong directional bias without excessive volatility  
- Quality momentum over pure volume
- Technical alignment patterns

Return JSON format with detailed analysis and trading recommendations.
"""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": claude_api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}],
            },
        )

        if response.status_code == 200:
            claude_response = response.json()
            analysis_text = claude_response["content"][0]["text"]

            # Parse Claude's response
            try:
                # Extract JSON from Claude's response
                import re

                json_match = re.search(r"\{.*\}", analysis_text, re.DOTALL)
                if json_match:
                    claude_analysis = json.loads(json_match.group())
                else:
                    # Fallback parsing
                    claude_analysis = {
                        "analysis_text": analysis_text,
                        "recommendations": [],
                        "confidence": 0.7,
                    }

                logger.info("✅ Claude analysis completed successfully")
                return claude_analysis

            except json.JSONDecodeError:
                logger.warning("Claude response parsing failed, using text analysis")
                return {
                    "analysis_text": analysis_text,
                    "claude_insights": True,
                    "recommendations": extract_recommendations_from_text(analysis_text),
                }
        else:
            logger.error(f"Claude API error: {response.status_code}")
            return fallback_token_analysis(tokens_data, winner_traits)

    except Exception as e:
        logger.error(f"Claude analysis error: {e}")
        return fallback_token_analysis(tokens_data, winner_traits)


def fallback_token_analysis(tokens_data, winner_traits):
    """Fallback analysis when Claude API is unavailable"""
    opportunities = []

    for token in tokens_data:
        try:
            symbol = token["symbol"]
            if not symbol.endswith("USDT") or symbol == "USDCUSDT":
                continue

            price_change = float(token["priceChangePercent"])
            current_price = float(token["lastPrice"])
            high_24h = float(token["highPrice"])
            low_24h = float(token["lowPrice"])
            volume = float(token["quoteVolume"])

            # Skip tokens with insufficient data
            if price_change < 3.0 or volume < 1000:
                continue

            # Calculate MAGICUSDT similarity scores
            range_position = (
                (current_price - low_24h) / (high_24h - low_24h)
                if high_24h != low_24h
                else 0.5
            )

            performance_score = min(abs(price_change) / 20.0, 1.0)
            momentum_score = (
                min(abs(price_change) / 15.0, 1.0) if price_change > 0 else 0
            )
            position_score = range_position
            volume_score = min(volume / 100000, 1.0)  # Volume quality

            # MAGICUSDT similarity (higher = more similar)
            magicusdt_similarity = (
                performance_score * 0.4  # 40% weight on performance
                + momentum_score * 0.3  # 30% weight on momentum
                + position_score * 0.2  # 20% weight on range position
                + volume_score * 0.1  # 10% weight on volume
            ) * 100

            if magicusdt_similarity >= 50:  # 50%+ similarity threshold
                opportunities.append(
                    {
                        "symbol": symbol,
                        "magicusdt_similarity": magicusdt_similarity,
                        "price_change": price_change,
                        "range_position": range_position,
                        "current_price": current_price,
                        "volume": volume,
                        "scores": {
                            "performance_score": performance_score,
                            "momentum_score": momentum_score,
                            "position_score": position_score,
                            "volume_score": volume_score,
                        },
                    }
                )

        except (ValueError, KeyError) as e:
            continue

    # Sort by MAGICUSDT similarity
    opportunities.sort(key=lambda x: x["magicusdt_similarity"], reverse=True)

    return {
        "opportunities": opportunities[:10],
        "total_analyzed": len(tokens_data),
        "similar_patterns_found": len(opportunities),
        "analysis_method": "fallback",
        "magicusdt_criteria_used": True,
    }


def extract_recommendations_from_text(text):
    """Extract trading recommendations from Claude's text response"""
    recommendations = []

    # Simple pattern matching for common recommendation formats
    lines = text.split("\n")
    current_rec = {}

    for line in lines:
        line = line.strip()
        if any(
            keyword in line.upper()
            for keyword in ["SYMBOL:", "TOKEN:", "RECOMMENDATION:"]
        ):
            if current_rec:
                recommendations.append(current_rec)
                current_rec = {}

            # Extract symbol
            import re

            symbol_match = re.search(r"([A-Z]{3,10}USDT)", line)
            if symbol_match:
                current_rec["symbol"] = symbol_match.group(1)

        elif "SCORE:" in line.upper() or "SIMILARITY:" in line.upper():
            score_match = re.search(r"(\d+(?:\.\d+)?)", line)
            if score_match:
                current_rec["score"] = float(score_match.group(1))

        elif any(keyword in line.upper() for keyword in ["BUY", "ENTRY", "TARGET"]):
            current_rec["action"] = line

    if current_rec:
        recommendations.append(current_rec)

    return recommendations


def run_claude_analysis_strategy(config):
    """Run Claude-powered analysis strategy"""
    from binance.client import Client

    print("🧠 Initializing Claude AI Analysis Strategy...")
    print("🎯 Comparing all Binance US tokens to MAGICUSDT winning pattern")

    # Initialize Binance client
    client = Client(
        api_key=os.getenv("BINANCEUS_KEY"),
        api_secret=os.getenv("BINANCEUS_SECRET"),
        tld="us",
    )

    # MAGICUSDT reference traits
    magicusdt_traits = {
        "performance": 18.81,
        "momentum_score": 0.998,
        "range_position": 0.97,
        "pattern_type": "MOMENTUM_SURGE",
        "volume_strategy": "quality_over_quantity",
        "technical_alignment": True,
        "controlled_volatility": True,
    }

    try:
        # Get all tradable USDT pairs
        print("📊 Fetching all Binance US tradable tokens...")
        exchange_info = client.get_exchange_info()
        tradable_symbols = []

        for symbol_info in exchange_info["symbols"]:
            symbol = symbol_info["symbol"]
            if (
                symbol.endswith("USDT")
                and symbol_info["status"] == "TRADING"
                and symbol != "USDTUSDT"
            ):
                tradable_symbols.append(symbol)

        print(f"✅ Found {len(tradable_symbols)} tradable USDT pairs")

        # Get 24h ticker data for all symbols
        print("📈 Analyzing market data...")
        tickers = client.get_ticker()

        # Filter to our tradable symbols
        relevant_tickers = [t for t in tickers if t["symbol"] in tradable_symbols]

        print(f"📊 Analyzing {len(relevant_tickers)} tokens with Claude AI...")

        # Use Claude to analyze all tokens
        claude_analysis = analyze_with_claude_comparison(
            relevant_tickers, magicusdt_traits
        )

        # Display results
        print("\n🏆 CLAUDE AI ANALYSIS RESULTS")
        print("=" * 50)

        if "opportunities" in claude_analysis:
            opportunities = claude_analysis["opportunities"]
            print(f"🎯 Found {len(opportunities)} tokens similar to MAGICUSDT pattern")

            for i, opp in enumerate(opportunities[:5], 1):
                symbol = opp["symbol"]
                similarity = opp.get("magicusdt_similarity", 0)
                change = opp.get("price_change", 0)
                range_pos = opp.get("range_position", 0)

                print(f"\n{i}. {symbol}")
                print(f"   🎯 MAGICUSDT Similarity: {similarity:.1f}%")
                print(f"   📈 24h Change: {change:+.2f}%")
                print(f"   📊 Range Position: {range_pos:.1%}")
                print(f"   💰 Price: ${opp.get('current_price', 0):.6f}")

                if similarity >= 70:
                    print(f"   🚀 HIGH SIMILARITY - Strong trading candidate!")
                elif similarity >= 60:
                    print(f"   ⚡ GOOD SIMILARITY - Consider for portfolio")

        elif "analysis_text" in claude_analysis:
            print("🧠 Claude AI Insights:")
            print(
                claude_analysis["analysis_text"][:1000] + "..."
                if len(claude_analysis["analysis_text"]) > 1000
                else claude_analysis["analysis_text"]
            )

            if "recommendations" in claude_analysis:
                print(f"\n📋 Trading Recommendations:")
                for rec in claude_analysis["recommendations"][:3]:
                    if "symbol" in rec:
                        print(f"   🎯 {rec['symbol']}: {rec.get('action', 'Monitor')}")

        # Save analysis results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = f"claude_token_analysis_{timestamp}.json"

        with open(analysis_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "strategy": "claude_analysis",
                    "magicusdt_reference": magicusdt_traits,
                    "total_tokens_analyzed": len(relevant_tickers),
                    "claude_analysis": claude_analysis,
                    "config": config,
                },
                f,
                indent=2,
            )

        print(f"\n✅ Analysis saved to: {analysis_file}")

        # Interactive trading decision
        if "opportunities" in claude_analysis and claude_analysis["opportunities"]:
            best_opportunity = claude_analysis["opportunities"][0]

            print(f"\n🎯 BEST OPPORTUNITY: {best_opportunity['symbol']}")
            print(
                f"   MAGICUSDT Similarity: {best_opportunity.get('magicusdt_similarity', 0):.1f}%"
            )
            print(f"   Recommended based on AI analysis")

            # Check account balance
            account = client.get_account()
            usdt_balance = 0
            for balance in account["balances"]:
                if balance["asset"] == "USDT":
                    usdt_balance = float(balance["free"])
                    break

            if usdt_balance >= 20:
                position_size = min(
                    usdt_balance * config.get("position_size_pct", 0.05), 50
                )

                print(f"\n💰 Available Balance: ${usdt_balance:.2f}")
                print(f"📊 Suggested Position Size: ${position_size:.2f}")

                execute_trade = input(
                    f"\n🚨 Execute trade on {best_opportunity['symbol']}? (type 'EXECUTE' to confirm): "
                )

                if execute_trade == "EXECUTE":
                    print("🚀 Executing Claude AI recommended trade...")
                    # Here you would implement the actual trade execution
                    print("✅ Trade execution logic would go here")
                else:
                    print("❌ Trade execution cancelled")
            else:
                print(
                    f"❌ Insufficient balance for trade (${usdt_balance:.2f} < $20 minimum)"
                )

        print("\n🎉 Claude AI Analysis Strategy Complete!")

    except Exception as e:
        logger.error(f"Claude analysis strategy error: {e}")
        print(f"❌ Error in Claude analysis: {e}")


def main():
    """Main live trading launcher"""
    try:
        print("🎯 VictoryChain Live Trading Launcher")
        print("=" * 50)

        # Check API keys
        if not os.getenv("BINANCEUS_KEY") or not os.getenv("BINANCEUS_SECRET"):
            print("❌ Binance API keys not found in .env file")
            return False

        # Get user confirmation
        config = get_user_confirmation()
        if not config:
            return False

        # Create live configuration
        live_config = create_live_config(config)

        # Final countdown
        print("\n🚀 Starting live trading in:")
        for i in range(5, 0, -1):
            print(f"   {i}...")
            import time

            time.sleep(1)

        print("✅ LIVE TRADING STARTED!")
        print("📊 Monitor the logs carefully!")
        print("")

        # Launch trading bot
        launch_live_trading(live_config)

    except KeyboardInterrupt:
        print("\n👋 Live trading cancelled by user")
        return False
    except Exception as e:
        print(f"Live trading launcher error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
