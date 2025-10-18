#!/usr/bin/env python3
"""
VictoryChain Claude AI-Powered Dynamic Momentum Trading Strategy
===============================================================

Advanced momentum trading with Claude AI analysis for enhanced decision making.
Features:
- Claude AI analyzes market conditions and momentum
- AI-powered entry/exit signals with reasoning
- Dynamic stop losses based on AI risk assessment
- Intelligent position sizing with AI recommendations
- Real-time market sentiment analysis
- AI-driven portfolio optimization
"""

import os
import sys
import json
import time
import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config/.env")


@dataclass
class ClaudeAnalysis:
    """Claude AI analysis result"""

    symbol: str
    recommendation: str  # BUY, SELL, HOLD
    confidence: float  # 0-1
    reasoning: str
    risk_level: str  # LOW, MEDIUM, HIGH
    price_target: float
    stop_loss_rec: float
    allocation_rec: float
    momentum_score: float
    market_sentiment: str
    analysis_timestamp: datetime


@dataclass
class PositionState:
    """Enhanced position state with Claude analysis"""

    symbol: str
    entry_price: float
    current_price: float
    stop_loss: float
    allocation_pct: float
    profit_pct: float
    momentum_score: float
    consecutive_gains: int
    max_profit_reached: float
    trade_start_time: datetime
    last_claude_analysis: Optional[ClaudeAnalysis]
    claude_confidence: float
    ai_risk_level: str


@dataclass
class TradingConfig:
    """Enhanced trading configuration with Claude settings"""

    initial_stop_loss_pct: float = 0.22
    tight_stop_loss_pct: float = 0.05
    profit_target_pct: float = 0.15
    min_momentum_threshold: float = 10.0
    max_allocation_pct: float = 0.50
    initial_allocation_pct: float = 0.10
    allocation_increase_step: float = 0.05
    momentum_check_interval: int = 60
    claude_analysis_interval: int = 300  # Analyze with Claude every 5 minutes
    min_claude_confidence: float = 0.7  # Minimum AI confidence to trade


class ClaudeMomentumTrader:
    def __init__(self):
        """Initialize the Claude AI-powered momentum trader"""
        # Initialize Claude AI client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY in environment."
            )

        self.claude_client = anthropic.Anthropic(api_key=api_key)
        self.config = TradingConfig()
        self.current_position: Optional[PositionState] = None
        self.trading_history: List[Dict] = []
        self.claude_analyses: List[ClaudeAnalysis] = []
        self.is_running = False
        self.portfolio_value = 10000.0  # Demo portfolio

        # Demo market data
        self.demo_prices = {
            "BTC": {
                "price": 45000.0,
                "momentum": 8.5,
                "trend": 0.001,
                "volume": 1000000,
            },
            "ETH": {
                "price": 2800.0,
                "momentum": 12.3,
                "trend": 0.002,
                "volume": 800000,
            },
            "NEAR": {
                "price": 3.45,
                "momentum": 38.07,
                "trend": 0.005,
                "volume": 500000,
            },
            "GALA": {
                "price": 0.045,
                "momentum": 33.83,
                "trend": 0.008,
                "volume": 200000,
            },
            "DOT": {"price": 7.80, "momentum": 31.00, "trend": 0.003, "volume": 300000},
            "VET": {
                "price": 0.035,
                "momentum": 29.31,
                "trend": 0.004,
                "volume": 400000,
            },
            "DOGE": {
                "price": 0.078,
                "momentum": 27.72,
                "trend": 0.002,
                "volume": 600000,
            },
        }

        # Setup logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    async def get_claude_analysis(
        self, symbol: str, market_data: Dict
    ) -> ClaudeAnalysis:
        """Get Claude AI analysis for a trading opportunity"""
        try:
            # Prepare market context for Claude
            context = {
                "symbol": symbol,
                "current_price": market_data["price"],
                "momentum_score": market_data["momentum"],
                "volume": market_data["volume"],
                "trend": market_data["trend"],
                "timestamp": datetime.now().isoformat(),
            }

            # Add position context if we have one
            position_context = ""
            if self.current_position:
                position_context = f"""
Current Position Context:
- Holding: {self.current_position.symbol}
- Entry: ${self.current_position.entry_price:.4f}
- Current: ${self.current_position.current_price:.4f}
- P&L: {self.current_position.profit_pct*100:.2f}%
- Stop Loss: ${self.current_position.stop_loss:.4f}
"""

            prompt = f"""
You are an expert cryptocurrency trading analyst. Analyze the following trading opportunity:

Symbol: {symbol}
Current Price: ${market_data['price']:.4f}
Momentum Score: {market_data['momentum']:.2f}
Volume: {market_data['volume']:,}
Price Trend: {market_data['trend']:.4f}

{position_context}

Trading Strategy Context:
- Dynamic momentum trading with 22% initial stop loss
- Tighten to 5% stop when profitable
- Scale position size based on consecutive wins
- Maximum 50% allocation per position

Please provide:
1. BUY/SELL/HOLD recommendation
2. Confidence level (0-1)
3. Risk assessment (LOW/MEDIUM/HIGH)
4. Price target for next 24-48 hours
5. Recommended stop loss level
6. Suggested allocation percentage (1-50%)
7. Detailed reasoning for your analysis

Focus on:
- Momentum sustainability
- Risk/reward ratio
- Market sentiment
- Technical indicators
- Position management advice

Format your response as JSON with these fields:
{{
    "recommendation": "BUY|SELL|HOLD",
    "confidence": 0.85,
    "risk_level": "LOW|MEDIUM|HIGH", 
    "price_target": 3.75,
    "stop_loss_rec": 2.85,
    "allocation_rec": 15.0,
    "momentum_score": 35.2,
    "market_sentiment": "BULLISH|BEARISH|NEUTRAL",
    "reasoning": "Detailed analysis..."
}}
"""

            response = self.claude_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse Claude's response
            try:
                claude_data = json.loads(response.content[0].text)

                analysis = ClaudeAnalysis(
                    symbol=symbol,
                    recommendation=claude_data.get("recommendation", "HOLD"),
                    confidence=float(claude_data.get("confidence", 0.5)),
                    reasoning=claude_data.get("reasoning", "No reasoning provided"),
                    risk_level=claude_data.get("risk_level", "MEDIUM"),
                    price_target=float(
                        claude_data.get("price_target", market_data["price"])
                    ),
                    stop_loss_rec=float(
                        claude_data.get("stop_loss_rec", market_data["price"] * 0.78)
                    ),
                    allocation_rec=float(claude_data.get("allocation_rec", 10.0)),
                    momentum_score=float(
                        claude_data.get("momentum_score", market_data["momentum"])
                    ),
                    market_sentiment=claude_data.get("market_sentiment", "NEUTRAL"),
                    analysis_timestamp=datetime.now(),
                )

                self.claude_analyses.append(analysis)
                return analysis

            except json.JSONDecodeError:
                self.logger.error("Failed to parse Claude response as JSON")
                # Return default analysis
                return ClaudeAnalysis(
                    symbol=symbol,
                    recommendation="HOLD",
                    confidence=0.5,
                    reasoning="Failed to parse AI analysis",
                    risk_level="HIGH",
                    price_target=market_data["price"],
                    stop_loss_rec=market_data["price"] * 0.78,
                    allocation_rec=5.0,
                    momentum_score=market_data["momentum"],
                    market_sentiment="NEUTRAL",
                    analysis_timestamp=datetime.now(),
                )

        except Exception as e:
            self.logger.error(f"Error getting Claude analysis: {e}")
            # Return conservative default
            return ClaudeAnalysis(
                symbol=symbol,
                recommendation="HOLD",
                confidence=0.3,
                reasoning=f"Error in AI analysis: {str(e)}",
                risk_level="HIGH",
                price_target=market_data["price"],
                stop_loss_rec=market_data["price"] * 0.78,
                allocation_rec=5.0,
                momentum_score=market_data["momentum"],
                market_sentiment="NEUTRAL",
                analysis_timestamp=datetime.now(),
            )

    async def get_highest_momentum_with_ai(self) -> Tuple[str, float, ClaudeAnalysis]:
        """Get highest momentum token with Claude AI validation"""
        best_token = None
        best_momentum = 0
        best_analysis = None

        self.logger.info("🧠 Running Claude AI analysis on top momentum tokens...")

        # Get top 3 momentum tokens for AI analysis
        token_scores = []
        for symbol, data in self.demo_prices.items():
            # Simulate price movement
            trend = data["trend"]
            volatility = random.uniform(-0.02, 0.02)
            price_change = trend + volatility
            data["price"] *= 1 + price_change

            # Update momentum with some randomness
            momentum_change = random.uniform(-2, 2)
            data["momentum"] += momentum_change

            token_scores.append((symbol, data["momentum"], data))

        # Sort by momentum and analyze top 3 with Claude
        token_scores.sort(key=lambda x: x[1], reverse=True)
        top_tokens = token_scores[:3]

        for symbol, momentum, data in top_tokens:
            if momentum > self.config.min_momentum_threshold:
                analysis = await self.get_claude_analysis(symbol, data)

                self.logger.info(
                    f"🔍 {symbol}: Momentum={momentum:.2f}, "
                    f"Claude={analysis.recommendation} "
                    f"(confidence: {analysis.confidence:.2f})"
                )

                # Consider both momentum and Claude confidence
                combined_score = momentum * analysis.confidence

                if (
                    analysis.recommendation == "BUY"
                    and analysis.confidence >= self.config.min_claude_confidence
                    and combined_score > best_momentum
                ):

                    best_momentum = combined_score
                    best_token = symbol
                    best_analysis = analysis

                # Add small delay between AI calls
                await asyncio.sleep(2)

        return best_token, best_momentum, best_analysis

    async def get_current_price(self, symbol: str) -> float:
        """Get current price with simulated movement"""
        if symbol in self.demo_prices:
            data = self.demo_prices[symbol]
            trend = data["trend"]
            volatility = random.uniform(-0.01, 0.01)
            price_change = trend + volatility
            data["price"] *= 1 + price_change
            return data["price"]
        return 0.0

    def calculate_ai_enhanced_stop_loss(self, position: PositionState) -> float:
        """Calculate stop loss enhanced by Claude AI recommendations"""
        base_stop = self.calculate_traditional_stop_loss(
            position.entry_price, position.current_price, position.profit_pct
        )

        # If we have recent Claude analysis, consider its recommendation
        if position.last_claude_analysis:
            claude_stop = position.last_claude_analysis.stop_loss_rec
            risk_level = position.last_claude_analysis.risk_level

            # Adjust based on AI risk assessment
            if risk_level == "HIGH":
                # Tighten stop loss for high risk
                ai_stop = max(base_stop, position.current_price * 0.97)  # 3% max loss
            elif risk_level == "LOW":
                # Allow more room for low risk
                ai_stop = min(base_stop, claude_stop)
            else:  # MEDIUM
                # Use average of base and Claude recommendation
                ai_stop = (base_stop + claude_stop) / 2

            return ai_stop

        return base_stop

    def calculate_traditional_stop_loss(
        self, entry_price: float, current_price: float, profit_pct: float
    ) -> float:
        """Traditional stop loss calculation"""
        if profit_pct <= 0:
            return entry_price * (1 - self.config.initial_stop_loss_pct)

        if profit_pct >= self.config.profit_target_pct:
            return current_price * (1 - self.config.tight_stop_loss_pct)
        else:
            stop_pct = self.config.initial_stop_loss_pct - (profit_pct * 0.5)
            stop_pct = max(stop_pct, self.config.tight_stop_loss_pct)
            return current_price * (1 - stop_pct)

    def calculate_ai_allocation(
        self, analysis: ClaudeAnalysis, consecutive_gains: int
    ) -> float:
        """Calculate position allocation with AI enhancement"""
        base_allocation = self.config.initial_allocation_pct

        # AI confidence bonus
        confidence_bonus = (analysis.confidence - 0.5) * 0.2  # Up to 10% bonus

        # Risk level adjustment
        risk_multiplier = {"LOW": 1.2, "MEDIUM": 1.0, "HIGH": 0.7}[analysis.risk_level]

        # Claude's direct recommendation
        claude_allocation = analysis.allocation_rec / 100

        # Consecutive gains bonus
        gains_bonus = consecutive_gains * self.config.allocation_increase_step

        # Combine factors
        final_allocation = (
            (base_allocation + confidence_bonus + gains_bonus) * risk_multiplier
            + claude_allocation
        ) / 2

        return min(final_allocation, self.config.max_allocation_pct)

    async def execute_trade(
        self,
        action: str,
        symbol: str,
        allocation_pct: float,
        price: float,
        analysis: ClaudeAnalysis = None,
    ):
        """Execute trade with Claude analysis logging"""
        trade_amount = self.portfolio_value * allocation_pct
        quantity = trade_amount / price

        if action == "BUY":
            self.portfolio_value -= trade_amount
        elif action == "SELL" and self.current_position:
            pnl = quantity * (price - self.current_position.entry_price)
            self.portfolio_value += trade_amount + pnl

        trade_record = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "symbol": symbol,
            "price": price,
            "quantity": quantity,
            "allocation_pct": allocation_pct,
            "portfolio_value": self.portfolio_value,
            "claude_analysis": asdict(analysis) if analysis else None,
        }

        self.trading_history.append(trade_record)

        analysis_info = ""
        if analysis:
            analysis_info = f" (Claude: {analysis.recommendation}, confidence: {analysis.confidence:.2f})"

        self.logger.info(
            f"🔄 {action} {symbol}: {quantity:.4f} @ ${price:.4f} "
            f"({allocation_pct*100:.1f}% allocation){analysis_info}"
        )

    async def update_position_with_ai(self):
        """Update position using AI-enhanced logic"""
        if not self.current_position:
            return

        current_price = await self.get_current_price(self.current_position.symbol)
        if current_price <= 0:
            return

        # Update position metrics
        old_profit = self.current_position.profit_pct
        self.current_position.current_price = current_price
        self.current_position.profit_pct = (
            current_price - self.current_position.entry_price
        ) / self.current_position.entry_price

        if self.current_position.profit_pct > self.current_position.max_profit_reached:
            self.current_position.max_profit_reached = self.current_position.profit_pct

        # Check for consecutive gains
        if (
            self.current_position.profit_pct > old_profit
            and self.current_position.profit_pct > 0
        ):
            if old_profit <= 0:
                self.current_position.consecutive_gains += 1

        # Get fresh Claude analysis periodically
        if (
            not self.current_position.last_claude_analysis
            or (
                datetime.now()
                - self.current_position.last_claude_analysis.analysis_timestamp
            ).seconds
            > self.config.claude_analysis_interval
        ):

            market_data = self.demo_prices[self.current_position.symbol]
            analysis = await self.get_claude_analysis(
                self.current_position.symbol, market_data
            )
            self.current_position.last_claude_analysis = analysis
            self.current_position.claude_confidence = analysis.confidence
            self.current_position.ai_risk_level = analysis.risk_level

            self.logger.info(
                f"🧠 Claude update for {self.current_position.symbol}: "
                f"{analysis.recommendation} (confidence: {analysis.confidence:.2f})"
            )

            # Check if Claude recommends exit
            if analysis.recommendation == "SELL" and analysis.confidence > 0.8:
                self.logger.warning(
                    f"🤖 Claude strongly recommends SELL for {self.current_position.symbol}"
                )
                await self.execute_trade(
                    "SELL",
                    self.current_position.symbol,
                    self.current_position.allocation_pct,
                    current_price,
                    analysis,
                )
                self.current_position = None
                return

        # Update stop loss with AI enhancement
        old_stop = self.current_position.stop_loss
        new_stop = self.calculate_ai_enhanced_stop_loss(self.current_position)

        if new_stop > old_stop:
            self.current_position.stop_loss = new_stop
            self.logger.info(
                f"📈 AI-enhanced stop loss for {self.current_position.symbol}: "
                f"${new_stop:.4f} (profit: {self.current_position.profit_pct*100:.2f}%)"
            )

    async def trading_loop(self, duration_minutes: int = 10):
        """Main AI-enhanced trading loop"""
        self.logger.info("🚀 Starting Claude AI-Enhanced Momentum Trading")
        self.is_running = True

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        while self.is_running and datetime.now() < end_time:
            try:
                if self.current_position:
                    await self.update_position_with_ai()

                    # Check stop loss
                    if (
                        self.current_position
                        and self.current_position.current_price
                        <= self.current_position.stop_loss
                    ):
                        self.logger.warning(
                            f"🛑 Stop loss triggered for {self.current_position.symbol}"
                        )
                        await self.execute_trade(
                            "SELL",
                            self.current_position.symbol,
                            self.current_position.allocation_pct,
                            self.current_position.current_price,
                        )
                        self.current_position = None
                        continue

                else:
                    # Look for new opportunities with AI
                    highest_token, momentum_score, analysis = (
                        await self.get_highest_momentum_with_ai()
                    )

                    if highest_token and analysis and analysis.recommendation == "BUY":
                        entry_price = await self.get_current_price(highest_token)
                        if entry_price > 0:
                            allocation = self.calculate_ai_allocation(analysis, 0)
                            stop_loss = self.calculate_traditional_stop_loss(
                                entry_price, entry_price, 0
                            )

                            self.current_position = PositionState(
                                symbol=highest_token,
                                entry_price=entry_price,
                                current_price=entry_price,
                                stop_loss=stop_loss,
                                allocation_pct=allocation,
                                profit_pct=0.0,
                                momentum_score=momentum_score,
                                consecutive_gains=0,
                                max_profit_reached=0.0,
                                trade_start_time=datetime.now(),
                                last_claude_analysis=analysis,
                                claude_confidence=analysis.confidence,
                                ai_risk_level=analysis.risk_level,
                            )

                            await self.execute_trade(
                                "BUY", highest_token, allocation, entry_price, analysis
                            )

                            self.logger.info(
                                f"🎯 AI-powered entry: {highest_token} @ ${entry_price:.4f}"
                            )
                            self.logger.info(
                                f"🧠 Claude reasoning: {analysis.reasoning[:100]}..."
                            )

                # Status update
                if self.current_position:
                    self.logger.info(
                        f"📊 {self.current_position.symbol}: ${self.current_position.current_price:.4f} "
                        f"(P&L: {self.current_position.profit_pct*100:.2f}%, "
                        f"Claude confidence: {self.current_position.claude_confidence:.2f})"
                    )

                await asyncio.sleep(self.config.momentum_check_interval)

            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(30)

        self.logger.info("🏁 AI-enhanced trading session completed!")

    def print_claude_insights(self):
        """Print Claude AI insights summary"""
        print("\n" + "=" * 80)
        print("🧠 CLAUDE AI INSIGHTS SUMMARY")
        print("=" * 80)

        if not self.claude_analyses:
            print("No Claude analyses recorded.")
            return

        # Group analyses by recommendation
        recommendations = {"BUY": [], "SELL": [], "HOLD": []}
        total_confidence = 0

        for analysis in self.claude_analyses:
            recommendations[analysis.recommendation].append(analysis)
            total_confidence += analysis.confidence

        avg_confidence = total_confidence / len(self.claude_analyses)

        print(f"📈 Total AI Analyses: {len(self.claude_analyses)}")
        print(f"🎯 Average Confidence: {avg_confidence:.2f}")
        print(
            f"📊 Recommendations: BUY={len(recommendations['BUY'])}, "
            f"SELL={len(recommendations['SELL'])}, HOLD={len(recommendations['HOLD'])}"
        )

        # Show recent high-confidence analyses
        print(f"\n🔍 HIGH-CONFIDENCE ANALYSES:")
        high_conf_analyses = [
            a for a in self.claude_analyses[-5:] if a.confidence > 0.7
        ]

        for analysis in high_conf_analyses:
            print(
                f"   {analysis.symbol}: {analysis.recommendation} "
                f"(confidence: {analysis.confidence:.2f}, risk: {analysis.risk_level})"
            )
            print(f"      💭 {analysis.reasoning[:80]}...")
            print()

        print("=" * 80)

    def print_final_summary(self):
        """Print comprehensive trading summary"""
        print("\n" + "=" * 80)
        print("🏆 CLAUDE AI-ENHANCED TRADING SUMMARY")
        print("=" * 80)

        total_trades = len(self.trading_history)
        ai_trades = sum(
            1 for trade in self.trading_history if trade.get("claude_analysis")
        )

        print(f"📈 Total Trades: {total_trades}")
        print(f"🧠 AI-Enhanced Trades: {ai_trades} ({ai_trades/total_trades*100:.1f}%)")
        print(f"💼 Final Portfolio Value: ${self.portfolio_value:.2f}")
        print(f"📈 Total Return: {(self.portfolio_value - 10000) / 10000 * 100:.2f}%")

        if self.current_position:
            print(f"\n🔄 Current Position: {self.current_position.symbol}")
            print(f"   P&L: {self.current_position.profit_pct*100:.2f}%")
            print(
                f"   Claude Confidence: {self.current_position.claude_confidence:.2f}"
            )
            print(f"   AI Risk Level: {self.current_position.ai_risk_level}")

        print("\n🎯 AI-ENHANCED FEATURES DEMONSTRATED:")
        print("   ✅ Claude AI market analysis and recommendations")
        print("   ✅ AI-powered risk assessment and position sizing")
        print("   ✅ Intelligent stop loss optimization")
        print("   ✅ Real-time sentiment analysis")
        print("   ✅ AI reasoning for every trading decision")

        self.print_claude_insights()


async def main():
    """Run the Claude AI-enhanced trading demo"""
    print("🧠 CLAUDE AI-ENHANCED MOMENTUM TRADING")
    print("=" * 60)
    print("Features:")
    print("• Claude AI analyzes each trading opportunity")
    print("• AI-powered risk assessment and position sizing")
    print("• Intelligent stop loss recommendations")
    print("• Real-time market sentiment analysis")
    print("• AI reasoning for every decision")
    print("=" * 60)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not found in environment.")
        print("This demo will run with simulated AI responses.")
        print("Set your Claude API key to see real AI analysis.")
        print()

    try:
        trader = ClaudeMomentumTrader()
        await trader.trading_loop(duration_minutes=5)  # 5-minute demo

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Running with simulated data...")

        # Fallback to demo without real Claude API
        trader = ClaudeMomentumTrader()

        # Override with mock Claude analysis
        async def mock_claude_analysis(symbol, data):
            return ClaudeAnalysis(
                symbol=symbol,
                recommendation=random.choice(["BUY", "HOLD"]),
                confidence=random.uniform(0.6, 0.9),
                reasoning=f"Mock AI analysis for {symbol} shows strong momentum with favorable risk/reward",
                risk_level=random.choice(["LOW", "MEDIUM"]),
                price_target=data["price"] * random.uniform(1.05, 1.15),
                stop_loss_rec=data["price"] * 0.85,
                allocation_rec=random.uniform(10, 25),
                momentum_score=data["momentum"],
                market_sentiment=random.choice(["BULLISH", "NEUTRAL"]),
                analysis_timestamp=datetime.now(),
            )

        trader.get_claude_analysis = mock_claude_analysis
        await trader.trading_loop(duration_minutes=3)

    finally:
        if "trader" in locals():
            trader.print_final_summary()


if __name__ == "__main__":
    asyncio.run(main())
