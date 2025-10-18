#!/usr/bin/env python3
"""
VictoryChain Moonshot Detector
Specialized bot for finding 30-50%+ opportunities in micro and low volume tokens
Uses AI analysis to identify breakout patterns and momentum shifts
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
    handlers=[logging.StreamHandler(), logging.FileHandler("moonshot_detector.log")],
)
logger = logging.getLogger(__name__)


class MoonshotDetector:
    def __init__(self):
        # API Configuration
        self.binance_us_base = "https://api.binance.us"
        self.claude_api_key = os.getenv("CLAUDE_API_KEY")

        # Moonshot criteria
        self.moonshot_criteria = {
            "volume_threshold": 50000,  # Max $50K volume for moonshots
            "min_momentum": 5.0,  # Minimum 5% momentum
            "max_positions": 3,  # Max moonshot positions
            "position_size": 0.03,  # 3% of portfolio per moonshot
            "profit_target": 0.30,  # 30% profit target
            "stop_loss": 0.15,  # 15% stop loss
            "max_hold_hours": 48,  # 48 hour max hold
            "volume_surge_multiplier": 2.0,  # Volume surge detection
        }

        # Tracking
        self.moonshot_positions = {}
        self.moonshot_watchlist = {}
        self.portfolio_value = 10000.0
        self.moonshot_allocation = 500.0  # $500 for moonshots

        # Historical tracking for volume surge detection
        self.volume_history = {}

        logger.info("🚀 Moonshot Detector initialized")
        logger.info(f"🎯 Target: 30-50% gains from micro-volume tokens")

    async def get_micro_volume_tokens(self) -> List[Dict]:
        """Get tokens with micro volume (<$50K) that show momentum"""
        try:
            # Get 24h ticker data
            url = f"{self.binance_us_base}/api/v3/ticker/24hr"
            response = requests.get(url)

            if response.status_code != 200:
                logger.error(f"Failed to get ticker data: {response.status_code}")
                return []

            tickers = response.json()
            micro_tokens = []

            for ticker in tickers:
                symbol = ticker["symbol"]
                if not symbol.endswith("USDT") or symbol == "USDT":
                    continue

                volume_usdt = float(ticker["quoteVolume"])
                price_change = float(ticker["priceChangePercent"])

                # Filter for micro volume tokens with momentum
                if (
                    volume_usdt <= self.moonshot_criteria["volume_threshold"]
                    and price_change >= self.moonshot_criteria["min_momentum"]
                ):

                    token_data = {
                        "symbol": symbol,
                        "price": float(ticker["lastPrice"]),
                        "change_24h": price_change,
                        "volume_24h": volume_usdt,
                        "high_24h": float(ticker["highPrice"]),
                        "low_24h": float(ticker["lowPrice"]),
                        "volume_change": float(ticker["priceChangePercent"]),
                        "bid_ask_spread": self._calculate_spread(ticker),
                        "volatility": self._calculate_volatility(ticker),
                    }

                    # Check for volume surge
                    token_data["volume_surge"] = self._detect_volume_surge(
                        symbol, volume_usdt
                    )

                    micro_tokens.append(token_data)

            # Sort by momentum and volume surge
            micro_tokens.sort(
                key=lambda x: (x["volume_surge"], x["change_24h"]), reverse=True
            )

            logger.info(
                f"🔍 Found {len(micro_tokens)} micro-volume moonshot candidates"
            )
            return micro_tokens[:50]  # Top 50 candidates

        except Exception as e:
            logger.error(f"Error getting micro volume tokens: {e}")
            return []

    def _calculate_spread(self, ticker: Dict) -> float:
        """Calculate bid-ask spread percentage"""
        try:
            bid = float(ticker.get("bidPrice", 0))
            ask = float(ticker.get("askPrice", 0))
            if bid > 0 and ask > 0:
                return ((ask - bid) / ((ask + bid) / 2)) * 100
        except:
            pass
        return 0.0

    def _calculate_volatility(self, ticker: Dict) -> float:
        """Calculate 24h volatility"""
        try:
            high = float(ticker["highPrice"])
            low = float(ticker["lowPrice"])
            close = float(ticker["lastPrice"])
            return ((high - low) / close) * 100
        except:
            return 0.0

    def _detect_volume_surge(self, symbol: str, current_volume: float) -> bool:
        """Detect if there's a volume surge compared to historical average"""
        if symbol not in self.volume_history:
            self.volume_history[symbol] = []

        # Store volume history (keep last 7 days)
        self.volume_history[symbol].append(current_volume)
        if len(self.volume_history[symbol]) > 7:
            self.volume_history[symbol] = self.volume_history[symbol][-7:]

        # Need at least 3 days of history
        if len(self.volume_history[symbol]) < 3:
            return False

        avg_volume = np.mean(self.volume_history[symbol][:-1])  # Exclude current day
        surge_threshold = avg_volume * self.moonshot_criteria["volume_surge_multiplier"]

        return current_volume > surge_threshold

    async def analyze_moonshot_batch(self, tokens: List[Dict]) -> Dict[str, Dict]:
        """Use Claude to identify the best moonshot opportunities"""
        if not tokens or not self.claude_api_key:
            return self._fallback_moonshot_analysis(tokens)

        try:
            prompt = f"""Analyze these micro-volume tokens for MOONSHOT opportunities (30-50%+ gains):

MOONSHOT CRITERIA:
- Volume: <$50K (looking for breakouts before mainstream attention)
- Target: 30-50% gains within 24-48 hours
- Risk: High (15% stop loss acceptable)
- Focus: Breakout patterns, volume surges, momentum shifts

TOKENS:
"""

            for token in tokens:
                surge_indicator = "🚀 VOLUME SURGE" if token["volume_surge"] else ""
                prompt += f"""
{token['symbol']} {surge_indicator}:
- Price: ${token['price']:.6f}
- 24h Change: {token['change_24h']:.2f}%
- Volume: ${token['volume_24h']:,.0f}
- Volatility: {token['volatility']:.1f}%
- High/Low: ${token['high_24h']:.6f}/${token['low_24h']:.6f}
"""

            prompt += """
For each token, analyze:
1. Breakout potential from technical patterns
2. Volume surge significance  
3. Risk/reward for 30-50% target
4. Probability of moonshot within 48h

Respond with JSON only:
{
  "TOKEN1USDT": {"moonshot_score": 0-100, "breakout_probability": 0-100, "target_gain": 30-50, "risk_level": "high/extreme", "action": "moonshot/watch/avoid"},
  "TOKEN2USDT": {"moonshot_score": 0-100, "breakout_probability": 0-100, "target_gain": 30-50, "risk_level": "high/extreme", "action": "moonshot/watch/avoid"}
}"""

            # Make Claude API call
            headers = {
                "x-api-key": self.claude_api_key,
                "content-type": "application/json",
            }

            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 3000,
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
                    logger.info(f"🤖 Claude analyzed {len(tokens)} moonshot candidates")
                    return claude_results
            else:
                logger.error(f"Claude API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Claude moonshot analysis failed: {e}")

        # Fallback analysis
        return self._fallback_moonshot_analysis(tokens)

    def _fallback_moonshot_analysis(self, tokens: List[Dict]) -> Dict[str, Dict]:
        """Fallback moonshot analysis without Claude"""
        results = {}

        for token in tokens:
            # Score based on momentum and volume surge
            momentum_score = min(100, max(0, token["change_24h"] * 8 + 20))
            volume_surge_bonus = 30 if token["volume_surge"] else 0
            volatility_bonus = min(20, token["volatility"] * 2)

            moonshot_score = momentum_score + volume_surge_bonus + volatility_bonus
            moonshot_score = min(100, moonshot_score)

            # Breakout probability based on technical factors
            breakout_prob = moonshot_score * 0.8  # Conservative estimate

            # Target gain based on current momentum
            if token["change_24h"] > 15:
                target_gain = 45
            elif token["change_24h"] > 10:
                target_gain = 35
            else:
                target_gain = 30

            action = (
                "moonshot"
                if moonshot_score > 70 and token["change_24h"] > 8
                else "avoid"
            )
            if moonshot_score > 50 and action == "avoid":
                action = "watch"

            results[token["symbol"]] = {
                "moonshot_score": round(moonshot_score, 1),
                "breakout_probability": round(breakout_prob, 1),
                "target_gain": target_gain,
                "risk_level": "extreme" if token["volume_24h"] < 10000 else "high",
                "action": action,
            }

        return results

    async def execute_moonshot_trades(self, opportunities: Dict[str, Dict]) -> None:
        """Execute moonshot trades for highest probability opportunities"""
        if not opportunities:
            return

        # Filter for moonshot actions only
        moonshot_opportunities = {
            symbol: analysis
            for symbol, analysis in opportunities.items()
            if analysis["action"] == "moonshot"
        }

        if not moonshot_opportunities:
            logger.info("🌙 No moonshot opportunities found")
            return

        # Sort by moonshot score
        sorted_opportunities = sorted(
            moonshot_opportunities.items(),
            key=lambda x: x[1]["moonshot_score"],
            reverse=True,
        )

        executed_count = 0
        max_positions = self.moonshot_criteria["max_positions"]

        for symbol, analysis in sorted_opportunities:
            if executed_count >= max_positions:
                break

            if symbol in self.moonshot_positions:
                continue  # Already have position

            try:
                # Get current price
                ticker_url = f"{self.binance_us_base}/api/v3/ticker/price"
                response = requests.get(ticker_url, params={"symbol": symbol})

                if response.status_code != 200:
                    continue

                current_price = float(response.json()["price"])

                # Calculate position size
                position_value = (
                    self.moonshot_allocation * self.moonshot_criteria["position_size"]
                )
                position_size = position_value / current_price

                if position_value < 50:  # Minimum $50 moonshot position
                    continue

                # Execute moonshot trade (DEMO MODE)
                logger.info(f"🚀 MOONSHOT OPPORTUNITY DETECTED:")
                logger.info(f"   Symbol: {symbol}")
                logger.info(f"   Price: ${current_price:.6f}")
                logger.info(f"   Moonshot Score: {analysis['moonshot_score']:.1f}/100")
                logger.info(
                    f"   Breakout Probability: {analysis['breakout_probability']:.1f}%"
                )
                logger.info(f"   Target Gain: {analysis['target_gain']}%")
                logger.info(f"   Position Size: {position_size:.4f}")
                logger.info(f"   Position Value: ${position_value:.2f}")

                # Track moonshot position
                self.moonshot_positions[symbol] = {
                    "entry_price": current_price,
                    "position_size": position_size,
                    "entry_time": time.time(),
                    "analysis": analysis,
                    "stop_loss": current_price
                    * (1 - self.moonshot_criteria["stop_loss"]),
                    "take_profit": current_price
                    * (1 + (analysis["target_gain"] / 100)),
                }

                executed_count += 1
                logger.info(f"✅ Moonshot position opened: {symbol}")

            except Exception as e:
                logger.error(f"Failed to execute moonshot trade for {symbol}: {e}")

        if executed_count > 0:
            logger.info(f"🚀 Executed {executed_count} moonshot trades")

    async def monitor_moonshot_positions(self) -> None:
        """Monitor moonshot positions for profit taking or stop loss"""
        if not self.moonshot_positions:
            return

        logger.info(f"🌙 Monitoring {len(self.moonshot_positions)} moonshot positions")

        positions_to_close = []

        for symbol, position in self.moonshot_positions.items():
            try:
                # Get current price
                ticker_url = f"{self.binance_us_base}/api/v3/ticker/price"
                response = requests.get(ticker_url, params={"symbol": symbol})

                if response.status_code != 200:
                    continue

                current_price = float(response.json()["price"])
                entry_price = position["entry_price"]
                current_pnl = (current_price - entry_price) / entry_price * 100
                position_age = (time.time() - position["entry_time"]) / 3600  # hours

                # Check exit conditions
                should_close = False
                close_reason = ""

                if current_price <= position["stop_loss"]:
                    should_close = True
                    close_reason = (
                        f"Stop Loss (-{self.moonshot_criteria['stop_loss']*100:.0f}%)"
                    )
                elif current_price >= position["take_profit"]:
                    should_close = True
                    close_reason = f"🎯 MOONSHOT TARGET HIT (+{position['analysis']['target_gain']}%)"
                elif position_age >= self.moonshot_criteria["max_hold_hours"]:
                    should_close = True
                    close_reason = f"Time Exit ({position_age:.1f}h)"
                elif current_pnl > 20:  # Take profit at 20%+ even if target not hit
                    should_close = True
                    close_reason = f"Profit Lock (+{current_pnl:.1f}%)"

                if should_close:
                    positions_to_close.append((symbol, close_reason, current_pnl))
                    if "MOONSHOT TARGET HIT" in close_reason:
                        logger.info(
                            f"🎉 {close_reason}: {symbol} - PnL: {current_pnl:+.2f}%"
                        )
                    else:
                        logger.info(
                            f"🔄 MOONSHOT EXIT: {symbol} - {close_reason} - PnL: {current_pnl:+.2f}%"
                        )
                else:
                    status = (
                        "🚀" if current_pnl > 10 else "📈" if current_pnl > 0 else "📉"
                    )
                    logger.info(
                        f"{status} MOONSHOT: {symbol} - PnL: {current_pnl:+.2f}% - Age: {position_age:.1f}h"
                    )

            except Exception as e:
                logger.error(f"Error monitoring moonshot {symbol}: {e}")

        # Close positions
        for symbol, reason, pnl in positions_to_close:
            position = self.moonshot_positions[symbol]
            position_value = position["position_size"] * position["entry_price"]
            realized_pnl = position_value * (pnl / 100)

            del self.moonshot_positions[symbol]

            if "MOONSHOT TARGET HIT" in reason:
                logger.info(
                    f"🎊 MOONSHOT SUCCESS: {symbol} - {reason} - Realized PnL: ${realized_pnl:+.2f}"
                )
            else:
                logger.info(
                    f"✅ Moonshot closed: {symbol} - {reason} - Realized PnL: ${realized_pnl:+.2f}"
                )

    async def update_watchlist(self, opportunities: Dict[str, Dict]) -> None:
        """Update moonshot watchlist for future opportunities"""
        watch_opportunities = {
            symbol: analysis
            for symbol, analysis in opportunities.items()
            if analysis["action"] == "watch"
        }

        if watch_opportunities:
            self.moonshot_watchlist.update(watch_opportunities)
            logger.info(
                f"👀 Added {len(watch_opportunities)} tokens to moonshot watchlist"
            )

    async def run_moonshot_detection(self):
        """Main moonshot detection loop"""
        logger.info("🚀 Starting Moonshot Detector")
        logger.info(f"🎯 Scanning for 30-50% opportunities in micro-volume tokens")

        scan_count = 0

        while True:
            try:
                current_time = datetime.now()
                scan_count += 1

                logger.info(
                    f"🔍 Moonshot scan #{scan_count} at {current_time.strftime('%H:%M:%S')}"
                )

                # Monitor existing positions
                await self.monitor_moonshot_positions()

                # Get micro volume candidates
                micro_tokens = await self.get_micro_volume_tokens()
                if not micro_tokens:
                    await asyncio.sleep(600)  # Wait 10 minutes on error
                    continue

                logger.info(f"🔍 Analyzing {len(micro_tokens)} micro-volume candidates")

                # Analyze with Claude for moonshot potential
                analysis_results = await self.analyze_moonshot_batch(micro_tokens)

                # Execute moonshot trades
                await self.execute_moonshot_trades(analysis_results)

                # Update watchlist
                await self.update_watchlist(analysis_results)

                # Summary
                active_moonshots = len(self.moonshot_positions)
                watchlist_size = len(self.moonshot_watchlist)

                logger.info(
                    f"🌙 Moonshot Summary: {active_moonshots} active positions, {watchlist_size} on watchlist"
                )

                # Wait 30 minutes between scans (moonshots need time to develop)
                await asyncio.sleep(1800)

            except KeyboardInterrupt:
                logger.info("👋 Moonshot detector stopped by user")
                break
            except Exception as e:
                logger.error(f"Moonshot detection error: {e}")
                await asyncio.sleep(600)  # Wait 10 minutes on error


# Main execution
async def main():
    """Main function"""
    try:
        # Check for demo mode
        if "DEMO" in os.environ or not os.getenv("BINANCEUS_KEY"):
            logger.info("📝 DEMO MODE - No real trading will occur")
            logger.info("This moonshot detector is for analysis only")
        else:
            logger.info(
                "⚠️  WARNING: This moonshot detector will execute HIGH-RISK trades!"
            )
            logger.info(
                "🚀 Moonshot trading involves extreme risk with micro-volume tokens"
            )
            response = input("Type 'MOONSHOT' to start live moonshot detection: ")
            if response != "MOONSHOT":
                logger.info("❌ Moonshot detection cancelled")
                return

        # Initialize and run detector
        detector = MoonshotDetector()
        await detector.run_moonshot_detection()

    except KeyboardInterrupt:
        logger.info("👋 Moonshot detector stopped")
    except Exception as e:
        logger.error(f"Detector error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
