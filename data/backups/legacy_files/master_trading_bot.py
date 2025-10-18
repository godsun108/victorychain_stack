#!/usr/bin/env python3
"""
VictoryChain Master Trading Bot
Combines all strategies and adapts to market conditions:
- Volume-categorized trading
- Moonshot detection
- Statistical momentum
- AI-enhanced analysis
- Market regime detection
"""

import asyncio
import os
import json
import time
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("master_trading_bot.log")],
)
logger = logging.getLogger(__name__)


class MasterTradingBot:
    def __init__(self):
        # API Configuration
        self.binance_us_base = "https://api.binance.us"
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")

        # Market regime detection
        self.market_regimes = ["bullish", "bearish", "sideways", "volatile"]
        self.current_regime = "sideways"
        self.regime_confidence = 0.5

        # Strategy allocation based on market regime
        self.strategy_allocations = {
            "bullish": {
                "high_volume": 0.3,  # 30% in high volume momentum
                "medium_volume": 0.3,  # 30% in medium volume
                "low_volume": 0.25,  # 25% in low volume
                "moonshot": 0.15,  # 15% in moonshots
            },
            "bearish": {
                "high_volume": 0.6,  # 60% in safe high volume
                "medium_volume": 0.25,  # 25% in medium volume
                "low_volume": 0.1,  # 10% in low volume
                "moonshot": 0.05,  # 5% in moonshots
            },
            "sideways": {
                "high_volume": 0.4,  # 40% in high volume
                "medium_volume": 0.35,  # 35% in medium volume
                "low_volume": 0.15,  # 15% in low volume
                "moonshot": 0.1,  # 10% in moonshots
            },
            "volatile": {
                "high_volume": 0.2,  # 20% in high volume
                "medium_volume": 0.3,  # 30% in medium volume
                "low_volume": 0.3,  # 30% in low volume
                "moonshot": 0.2,  # 20% in moonshots
            },
        }

        # Volume categories
        self.volume_categories = {
            "high": {"min": 1000000, "max": float("inf")},
            "medium": {"min": 100000, "max": 1000000},
            "low": {"min": 10000, "max": 100000},
            "micro": {"min": 0, "max": 10000},
        }

        # Dynamic trading parameters based on regime
        self.regime_params = {
            "bullish": {
                "momentum_threshold": 2.0,
                "position_hold_hours": 6,
                "take_profit_multiplier": 1.2,
                "stop_loss_multiplier": 0.8,
                "scan_frequency": 300,  # 5 minutes
            },
            "bearish": {
                "momentum_threshold": 5.0,
                "position_hold_hours": 2,
                "take_profit_multiplier": 0.8,
                "stop_loss_multiplier": 1.2,
                "scan_frequency": 180,  # 3 minutes
            },
            "sideways": {
                "momentum_threshold": 3.0,
                "position_hold_hours": 8,
                "take_profit_multiplier": 1.0,
                "stop_loss_multiplier": 1.0,
                "scan_frequency": 600,  # 10 minutes
            },
            "volatile": {
                "momentum_threshold": 4.0,
                "position_hold_hours": 4,
                "take_profit_multiplier": 1.5,
                "stop_loss_multiplier": 0.7,
                "scan_frequency": 120,  # 2 minutes
            },
        }

        # MAGICUSDT Momentum Surge Strategy (learned from +18.81% winner)
        self.momentum_surge_params = {
            "min_performance_score": 0.8,
            "min_momentum_score": 0.95,
            "min_position_score": 0.8,
            "min_price_change_pct": 5.0,
            "rsi_range": (50, 80),
            "take_profit_target": 0.15,  # 15% like MAGICUSDT
            "trailing_stop": 0.05,  # 5%
            "position_size_pct": 0.03,  # 3% of portfolio
            "pattern_type": "MOMENTUM_SURGE",
        }

        # Portfolio tracking
        self.portfolio_value = 10000.0
        self.available_balance = 10000.0

        # Positions by strategy
        self.positions = {
            "high_volume": {},
            "medium_volume": {},
            "low_volume": {},
            "moonshot": {},
        }

        # Performance tracking
        self.performance_stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "regime_accuracy": {},
        }

        logger.info("🎯 Master Trading Bot initialized")
        logger.info(f"🧠 Market regime detection enabled")
        logger.info(f"🔄 Adaptive strategy allocation")

    async def detect_market_regime(self) -> Tuple[str, float]:
        """Detect current market regime using multiple indicators"""
        try:
            # Get market-wide data for regime detection
            url = f"{self.binance_us_base}/api/v3/ticker/24hr"
            response = requests.get(url)

            if response.status_code != 200:
                return self.current_regime, self.regime_confidence

            tickers = response.json()

            # Filter for major USDT pairs for regime analysis
            major_pairs = [
                "BTCUSDT",
                "ETHUSDT",
                "BNBUSDT",
                "ADAUSDT",
                "XRPUSDT",
                "SOLUSDT",
                "DOTUSDT",
                "MATICUSDT",
                "AVAXUSDT",
                "LINKUSDT",
            ]

            major_data = []
            for ticker in tickers:
                if ticker["symbol"] in major_pairs:
                    major_data.append(
                        {
                            "symbol": ticker["symbol"],
                            "change": float(ticker["priceChangePercent"]),
                            "volume": float(ticker["quoteVolume"]),
                        }
                    )

            if len(major_data) < 5:
                return self.current_regime, self.regime_confidence

            # Calculate regime indicators
            changes = [d["change"] for d in major_data]
            avg_change = np.mean(changes)
            change_std = np.std(changes)
            positive_ratio = len([c for c in changes if c > 0]) / len(changes)

            # Regime detection logic
            regime_scores = {
                "bullish": 0.0,
                "bearish": 0.0,
                "sideways": 0.0,
                "volatile": 0.0,
            }

            # Bullish indicators
            if avg_change > 2.0 and positive_ratio > 0.7:
                regime_scores["bullish"] += 0.4
            if avg_change > 0 and change_std < 3.0:
                regime_scores["bullish"] += 0.3
            if positive_ratio > 0.6:
                regime_scores["bullish"] += 0.3

            # Bearish indicators
            if avg_change < -2.0 and positive_ratio < 0.3:
                regime_scores["bearish"] += 0.4
            if avg_change < 0 and change_std < 3.0:
                regime_scores["bearish"] += 0.3
            if positive_ratio < 0.4:
                regime_scores["bearish"] += 0.3

            # Sideways indicators
            if -1.0 < avg_change < 1.0 and change_std < 2.0:
                regime_scores["sideways"] += 0.5
            if 0.4 < positive_ratio < 0.6:
                regime_scores["sideways"] += 0.3
            if change_std < 1.5:
                regime_scores["sideways"] += 0.2

            # Volatile indicators
            if change_std > 4.0:
                regime_scores["volatile"] += 0.4
            if change_std > 3.0 and abs(avg_change) > 2.0:
                regime_scores["volatile"] += 0.3
            if change_std > 5.0:
                regime_scores["volatile"] += 0.3

            # Determine regime
            best_regime = max(regime_scores, key=regime_scores.get)
            confidence = regime_scores[best_regime]

            # Smooth regime transitions (require confidence > 0.6 to change)
            if best_regime != self.current_regime and confidence > 0.6:
                logger.info(
                    f"🔄 Market regime change: {self.current_regime} → {best_regime} (confidence: {confidence:.1f})"
                )
                self.current_regime = best_regime
                self.regime_confidence = confidence
            elif best_regime == self.current_regime:
                self.regime_confidence = max(
                    0.1, min(1.0, (self.regime_confidence + confidence) / 2)
                )

            return self.current_regime, self.regime_confidence

        except Exception as e:
            logger.error(f"Market regime detection error: {e}")
            return self.current_regime, self.regime_confidence

    def get_dynamic_parameters(self, category: str) -> Dict:
        """Get trading parameters adjusted for current market regime and category"""
        base_params = self.regime_params[self.current_regime].copy()

        # Category-specific adjustments
        category_multipliers = {
            "high_volume": {"momentum": 0.8, "profit": 0.8, "loss": 1.2, "hold": 0.8},
            "medium_volume": {"momentum": 1.0, "profit": 1.0, "loss": 1.0, "hold": 1.0},
            "low_volume": {"momentum": 1.2, "profit": 1.5, "loss": 0.8, "hold": 1.2},
            "moonshot": {"momentum": 1.5, "profit": 2.0, "loss": 0.6, "hold": 2.0},
        }

        multipliers = category_multipliers.get(
            category, category_multipliers["medium_volume"]
        )

        return {
            "momentum_threshold": base_params["momentum_threshold"]
            * multipliers["momentum"],
            "position_hold_hours": base_params["position_hold_hours"]
            * multipliers["hold"],
            "take_profit_pct": 0.1
            * base_params["take_profit_multiplier"]
            * multipliers["profit"],
            "stop_loss_pct": 0.08
            * base_params["stop_loss_multiplier"]
            * multipliers["loss"],
            "scan_frequency": base_params["scan_frequency"],
        }

    async def get_categorized_opportunities(self) -> Dict[str, List[Dict]]:
        """Get trading opportunities categorized by volume"""
        try:
            # Get 24h ticker data
            url = f"{self.binance_us_base}/api/v3/ticker/24hr"
            response = requests.get(url)

            if response.status_code != 200:
                return {}

            tickers = response.json()
            categorized_tokens = {
                "high_volume": [],
                "medium_volume": [],
                "low_volume": [],
                "moonshot": [],
            }

            # Current regime parameters
            regime_params = self.regime_params[self.current_regime]

            for ticker in tickers:
                symbol = ticker["symbol"]
                if not symbol.endswith("USDT") or symbol == "USDT":
                    continue

                volume_usdt = float(ticker["quoteVolume"])
                price_change = float(ticker["priceChangePercent"])

                # Check for MAGICUSDT-style momentum surge first
                momentum_surge = self.detect_momentum_surge(ticker)
                if momentum_surge:
                    # Priority placement for momentum surge patterns
                    category = "high_volume"  # Treat as high priority
                    token_data = {
                        "symbol": symbol,
                        "price": float(ticker["lastPrice"]),
                        "change_24h": price_change,
                        "volume_24h": volume_usdt,
                        "high_24h": float(ticker["highPrice"]),
                        "low_24h": float(ticker["lowPrice"]),
                        "momentum_surge": momentum_surge,
                        "priority": "MOMENTUM_SURGE",
                    }
                    categorized_tokens[category].append(token_data)
                    continue

                # Skip if doesn't meet momentum threshold for regular analysis
                if price_change < regime_params["momentum_threshold"]:
                    continue

                # Categorize by volume
                category = None
                if volume_usdt >= self.volume_categories["high"]["min"]:
                    category = "high_volume"
                elif volume_usdt >= self.volume_categories["medium"]["min"]:
                    category = "medium_volume"
                elif volume_usdt >= self.volume_categories["low"]["min"]:
                    category = "low_volume"
                else:
                    category = "moonshot"

                token_data = {
                    "symbol": symbol,
                    "price": float(ticker["lastPrice"]),
                    "change_24h": price_change,
                    "volume_24h": volume_usdt,
                    "high_24h": float(ticker["highPrice"]),
                    "low_24h": float(ticker["lowPrice"]),
                    "volatility": (
                        (float(ticker["highPrice"]) - float(ticker["lowPrice"]))
                        / float(ticker["lastPrice"])
                    )
                    * 100,
                }

                categorized_tokens[category].append(token_data)

            # Sort each category by momentum
            for category in categorized_tokens:
                categorized_tokens[category].sort(
                    key=lambda x: x["change_24h"], reverse=True
                )
                # Limit to top opportunities per category
                limit = 20 if category == "moonshot" else 15
                categorized_tokens[category] = categorized_tokens[category][:limit]

            return categorized_tokens

        except Exception as e:
            logger.error(f"Error getting categorized opportunities: {e}")
            return {}

    async def analyze_with_claude(
        self, tokens: List[Dict], category: str
    ) -> Dict[str, Dict]:
        """Use Claude to analyze trading opportunities"""
        if not tokens or not self.claude_api_key:
            return self._fallback_analysis(tokens, category)

        try:
            params = self.get_dynamic_parameters(category)

            prompt = f"""Analyze these {category.replace('_', ' ')} tokens in {self.current_regime.upper()} market regime:

MARKET REGIME: {self.current_regime.upper()} (confidence: {self.regime_confidence:.1f})
STRATEGY: {category.replace('_', ' ').title()}
- Momentum Threshold: {params['momentum_threshold']:.1f}%
- Take Profit: {params['take_profit_pct']*100:.1f}%
- Stop Loss: {params['stop_loss_pct']*100:.1f}%
- Hold Duration: {params['position_hold_hours']:.1f}h

TOKENS:
"""

            for token in tokens:
                prompt += f"""
{token['symbol']}:
- Price: ${token['price']:.6f}
- 24h Change: {token['change_24h']:.2f}%
- Volume: ${token['volume_24h']:,.0f}
- Volatility: {token['volatility']:.1f}%
"""

            prompt += f"""
In {self.current_regime} markets, focus on:
- Bullish: Strong momentum continuation, longer holds
- Bearish: Quick scalps, tight stops, high-volume safety
- Sideways: Range trading, mean reversion opportunities
- Volatile: Breakout plays, wider stops, shorter holds

Respond with JSON only:
{{
  "TOKEN1USDT": {{"trade_score": 0-100, "entry_probability": 0-100, "regime_fit": 0-100, "action": "buy/hold/avoid"}},
  "TOKEN2USDT": {{"trade_score": 0-100, "entry_probability": 0-100, "regime_fit": 0-100, "action": "buy/hold/avoid"}}
}}"""

            # Make Claude API call
            headers = {
                "x-api-key": self.claude_api_key,
                "content-type": "application/json",
            }

            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 2500,
                "messages": [{"role": "user", "content": prompt}],
            }

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["content"][0]["text"]

                # Parse JSON response
                import re

                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    claude_results = json.loads(json_match.group())
                    return claude_results

        except Exception as e:
            logger.error(f"Claude analysis failed for {category}: {e}")

        return self._fallback_analysis(tokens, category)

    def _fallback_analysis(self, tokens: List[Dict], category: str) -> Dict[str, Dict]:
        """Fallback analysis without Claude"""
        results = {}
        params = self.get_dynamic_parameters(category)

        for token in tokens:
            momentum = token["change_24h"]
            volume_score = min(100, token["volume_24h"] / 100000 * 20)
            volatility_score = min(100, token["volatility"] * 5)

            # Base score from momentum
            trade_score = max(0, min(100, momentum * 8 + 30))

            # Adjust for regime
            if self.current_regime == "bullish":
                trade_score += 10 if momentum > 5 else 0
            elif self.current_regime == "bearish":
                trade_score -= 20
            elif self.current_regime == "volatile":
                trade_score += volatility_score * 0.2

            entry_prob = max(0, min(100, trade_score - 20))
            regime_fit = max(50, min(100, trade_score))

            action = (
                "buy"
                if entry_prob > 60 and momentum > params["momentum_threshold"]
                else "avoid"
            )

            results[token["symbol"]] = {
                "trade_score": round(trade_score, 1),
                "entry_probability": round(entry_prob, 1),
                "regime_fit": round(regime_fit, 1),
                "action": action,
            }

        return results

    def calculate_position_size(self, category: str, price: float) -> float:
        """Calculate position size based on regime and category allocation"""
        regime_allocation = self.strategy_allocations[self.current_regime]
        category_allocation = regime_allocation.get(category, 0.1)

        # Adjust allocation based on regime confidence
        confidence_factor = 0.5 + (self.regime_confidence * 0.5)
        adjusted_allocation = category_allocation * confidence_factor

        category_balance = self.available_balance * adjusted_allocation
        position_value = category_balance * 0.2  # 20% per position within category

        return position_value / price

    async def execute_trades(
        self, category: str, opportunities: Dict[str, Dict]
    ) -> None:
        """Execute trades for a category"""
        if not opportunities:
            return

        params = self.get_dynamic_parameters(category)

        # Filter for buy actions
        buy_opportunities = {
            symbol: analysis
            for symbol, analysis in opportunities.items()
            if analysis["action"] == "buy"
        }

        if not buy_opportunities:
            return

        # Sort by trade score
        sorted_opportunities = sorted(
            buy_opportunities.items(), key=lambda x: x[1]["trade_score"], reverse=True
        )

        executed_count = 0
        max_positions = 3 if category == "moonshot" else 2

        for symbol, analysis in sorted_opportunities:
            if executed_count >= max_positions:
                break

            if symbol in self.positions[category]:
                continue

            try:
                # Get current price
                ticker_url = f"{self.binance_us_base}/api/v3/ticker/price"
                response = requests.get(ticker_url, params={"symbol": symbol})

                if response.status_code != 200:
                    continue

                current_price = float(response.json()["price"])
                position_size = self.calculate_position_size(category, current_price)
                position_value = position_size * current_price

                if position_value < 20:  # Minimum position size
                    continue

                # Execute trade (DEMO MODE)
                logger.info(
                    f"🎯 {self.current_regime.upper()} REGIME - {category.upper()} TRADE:"
                )
                logger.info(f"   Symbol: {symbol}")
                logger.info(f"   Price: ${current_price:.6f}")
                logger.info(f"   Trade Score: {analysis['trade_score']:.1f}/100")
                logger.info(f"   Regime Fit: {analysis['regime_fit']:.1f}/100")
                logger.info(f"   Position Value: ${position_value:.2f}")

                # Track position
                self.positions[category][symbol] = {
                    "entry_price": current_price,
                    "position_size": position_size,
                    "entry_time": time.time(),
                    "category": category,
                    "analysis": analysis,
                    "stop_loss": current_price * (1 - params["stop_loss_pct"]),
                    "take_profit": current_price * (1 + params["take_profit_pct"]),
                    "regime": self.current_regime,
                }

                self.available_balance -= position_value
                executed_count += 1
                self.performance_stats["total_trades"] += 1

                logger.info(f"✅ {category} position opened: {symbol}")

            except Exception as e:
                logger.error(f"Failed to execute {category} trade for {symbol}: {e}")

    async def monitor_all_positions(self) -> None:
        """Monitor all positions across categories"""
        total_positions = sum(len(positions) for positions in self.positions.values())

        if total_positions == 0:
            return

        logger.info(
            f"📊 Monitoring {total_positions} positions in {self.current_regime} regime"
        )

        for category, positions in self.positions.items():
            if not positions:
                continue

            params = self.get_dynamic_parameters(category)
            positions_to_close = []

            for symbol, position in positions.items():
                try:
                    # Get current price
                    ticker_url = f"{self.binance_us_base}/api/v3/ticker/price"
                    response = requests.get(ticker_url, params={"symbol": symbol})

                    if response.status_code != 200:
                        continue

                    current_price = float(response.json()["price"])
                    entry_price = position["entry_price"]
                    current_pnl = (current_price - entry_price) / entry_price * 100
                    position_age = (time.time() - position["entry_time"]) / 3600

                    # Check exit conditions
                    should_close = False
                    close_reason = ""

                    if current_price <= position["stop_loss"]:
                        should_close = True
                        close_reason = f"Stop Loss ({current_pnl:+.1f}%)"
                    elif current_price >= position["take_profit"]:
                        should_close = True
                        close_reason = f"Take Profit ({current_pnl:+.1f}%)"
                    elif position_age >= params["position_hold_hours"]:
                        should_close = True
                        close_reason = f"Time Exit ({position_age:.1f}h)"
                    elif (
                        position["regime"] != self.current_regime
                        and abs(current_pnl) > 2
                    ):
                        should_close = True
                        close_reason = f"Regime Change ({position['regime']}→{self.current_regime})"

                    if should_close:
                        positions_to_close.append((symbol, close_reason, current_pnl))
                    else:
                        status = (
                            "🚀"
                            if current_pnl > 5
                            else "📈" if current_pnl > 0 else "📉"
                        )
                        logger.info(
                            f"{status} {category.upper()}: {symbol} - PnL: {current_pnl:+.2f}% - Age: {position_age:.1f}h"
                        )

                except Exception as e:
                    logger.error(f"Error monitoring {symbol}: {e}")

            # Close positions
            for symbol, reason, pnl in positions_to_close:
                position = positions[symbol]
                position_value = position["position_size"] * position["entry_price"]
                realized_pnl = position_value * (pnl / 100)

                self.available_balance += position_value + realized_pnl
                self.performance_stats["total_pnl"] += realized_pnl

                if pnl > 0:
                    self.performance_stats["winning_trades"] += 1

                if pnl > self.performance_stats["best_trade"]:
                    self.performance_stats["best_trade"] = pnl
                if pnl < self.performance_stats["worst_trade"]:
                    self.performance_stats["worst_trade"] = pnl

                del positions[symbol]

                logger.info(
                    f"✅ {category} closed: {symbol} - {reason} - PnL: ${realized_pnl:+.2f}"
                )

    async def run_master_trading(self):
        """Main master trading loop"""
        logger.info("🚀 Starting Master Trading Bot")
        logger.info(f"🧠 Adaptive regime-based trading with AI analysis")

        while True:
            try:
                current_time = datetime.now()

                # Detect market regime
                regime, confidence = await self.detect_market_regime()

                # Log regime status
                logger.info(
                    f"🧠 Market Regime: {regime.upper()} (confidence: {confidence:.1f})"
                )

                # Monitor existing positions
                await self.monitor_all_positions()

                # Get categorized opportunities
                categorized_opportunities = await self.get_categorized_opportunities()

                if not categorized_opportunities:
                    await asyncio.sleep(300)
                    continue

                # Process each category based on regime allocation
                regime_allocation = self.strategy_allocations[regime]

                for category, tokens in categorized_opportunities.items():
                    if not tokens or regime_allocation.get(category, 0) == 0:
                        continue

                    allocation_pct = regime_allocation[category] * 100

                    # Count momentum surge opportunities
                    momentum_surge_count = sum(
                        1
                        for token in tokens
                        if token.get("priority") == "MOMENTUM_SURGE"
                    )

                    if momentum_surge_count > 0:
                        logger.info(
                            f"🏆 {category.replace('_', ' ').title()}: {len(tokens)} opportunities ({allocation_pct:.0f}% allocation) - {momentum_surge_count} MOMENTUM SURGE patterns detected!"
                        )
                    else:
                        logger.info(
                            f"🎯 {category.replace('_', ' ').title()}: {len(tokens)} opportunities ({allocation_pct:.0f}% allocation)"
                        )

                    # Log momentum surge details
                    for token in tokens:
                        if token.get("priority") == "MOMENTUM_SURGE":
                            surge_data = token["momentum_surge"]
                            logger.info(
                                f"   🚀 MAGICUSDT-STYLE: {token['symbol']} - {token['change_24h']:+.2f}% - Score: {surge_data['scores']['overall_score']:.3f}"
                            )

                    # Analyze with Claude
                    analysis_results = await self.analyze_with_claude(tokens, category)

                    # Execute trades
                    await self.execute_trades(category, analysis_results)

                # Portfolio summary
                total_positions = sum(
                    len(positions) for positions in self.positions.values()
                )
                win_rate = (
                    self.performance_stats["winning_trades"]
                    / max(1, self.performance_stats["total_trades"])
                ) * 100

                logger.info(
                    f"💼 Portfolio: ${self.portfolio_value:.2f} | Available: ${self.available_balance:.2f}"
                )
                logger.info(
                    f"📊 Positions: {total_positions} | Trades: {self.performance_stats['total_trades']} | Win Rate: {win_rate:.1f}%"
                )
                logger.info(
                    f"💰 Total PnL: ${self.performance_stats['total_pnl']:+.2f}"
                )

                # Dynamic scan frequency based on regime
                scan_frequency = self.regime_params[regime]["scan_frequency"]
                await asyncio.sleep(scan_frequency)

            except KeyboardInterrupt:
                logger.info("👋 Master trading bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Master trading error: {e}")
                await asyncio.sleep(300)

    def detect_momentum_surge(self, ticker_data: Dict) -> Optional[Dict]:
        """
        Detect MAGICUSDT-style momentum surge patterns
        Based on winning traits: EXCEPTIONAL_PERFORMANCE_WITH_MOMENTUM
        """
        try:
            symbol = ticker_data["symbol"]
            price_change_pct = float(ticker_data["priceChangePercent"])
            current_price = float(ticker_data["lastPrice"])
            volume_24h = float(ticker_data["volume"])
            quote_volume_24h = float(ticker_data["quoteVolume"])
            high_24h = float(ticker_data["highPrice"])
            low_24h = float(ticker_data["lowPrice"])

            # Skip if doesn't meet minimum performance threshold
            if price_change_pct < self.momentum_surge_params["min_price_change_pct"]:
                return None

            # Calculate range position (MAGICUSDT was at 97%)
            range_position = (
                (current_price - low_24h) / (high_24h - low_24h)
                if high_24h != low_24h
                else 0.5
            )

            # Calculate momentum surge scores
            performance_score = min(
                abs(price_change_pct) / 20.0, 1.0
            )  # Normalize to 20%
            momentum_score = (
                min(abs(price_change_pct) / 15.0, 1.0) if price_change_pct > 0 else 0
            )
            position_score = range_position

            # Check if meets MAGICUSDT criteria
            meets_performance = (
                performance_score >= self.momentum_surge_params["min_performance_score"]
            )
            meets_momentum = (
                momentum_score >= self.momentum_surge_params["min_momentum_score"]
            )
            meets_position = (
                position_score >= self.momentum_surge_params["min_position_score"]
            )

            if meets_performance and meets_momentum and meets_position:
                return {
                    "symbol": symbol,
                    "pattern_type": "MOMENTUM_SURGE",
                    "current_price": current_price,
                    "price_change_pct": price_change_pct,
                    "range_position": range_position,
                    "scores": {
                        "performance_score": performance_score,
                        "momentum_score": momentum_score,
                        "position_score": position_score,
                        "overall_score": (
                            performance_score + momentum_score + position_score
                        )
                        / 3,
                    },
                    "magicusdt_similarity": True,
                    "confidence": "HIGH",
                }

            return None

        except Exception as e:
            logger.error(
                f"Error in momentum surge detection for {ticker_data.get('symbol', 'unknown')}: {e}"
            )
            return None


# Main execution
async def main():
    """Main function"""
    try:
        # Check for demo mode
        if "DEMO" in os.environ or not os.getenv("BINANCEUS_KEY"):
            logger.info("📝 DEMO MODE - No real trading will occur")
            logger.info("Master bot running in analysis mode")
        else:
            logger.info(
                "⚠️  WARNING: Master bot will execute REAL trades across ALL strategies!"
            )
            logger.info(
                "🧠 This includes regime detection, volume categorization, and moonshot trading"
            )
            response = input("Type 'MASTER' to start master trading bot: ")
            if response != "MASTER":
                logger.info("❌ Master trading cancelled")
                return

        # Initialize and run master bot
        bot = MasterTradingBot()
        await bot.run_master_trading()

    except KeyboardInterrupt:
        logger.info("👋 Master bot stopped")
    except Exception as e:
        logger.error(f"Master bot error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
