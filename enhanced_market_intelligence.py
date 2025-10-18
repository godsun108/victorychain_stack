#!/usr/bin/env python3
"""
🎯 ENHANCED MARKET INTELLIGENCE SYSTEM
=====================================
Advanced market analysis with AI-powered insights, sentiment analysis,
and predictive modeling for strategic trading decisions.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketSentiment(Enum):
    """Market sentiment classification"""

    EXTREMELY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    EXTREMELY_BULLISH = 2


class TrendStrength(Enum):
    """Trend strength classification"""

    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class MarketIntelligence:
    """Comprehensive market intelligence data"""

    symbol: str
    current_price: float
    trend_direction: str
    trend_strength: TrendStrength
    sentiment: MarketSentiment
    momentum_score: float
    volatility_index: float
    volume_profile: Dict[str, float]
    support_levels: List[float]
    resistance_levels: List[float]
    technical_indicators: Dict[str, float]
    fundamental_score: float
    catalyst_events: List[str]
    risk_factors: List[str]
    confidence_score: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SectorAnalysis:
    """Sector-wide analysis"""

    sector_name: str
    overall_sentiment: MarketSentiment
    momentum_score: float
    correlation_matrix: Dict[str, Dict[str, float]]
    leaders: List[str]
    laggards: List[str]
    rotation_signals: List[str]
    sector_strength: float


class AdvancedTechnicalAnalyzer:
    """Advanced technical analysis engine"""

    def __init__(self):
        self.lookback_periods = {"short": 7, "medium": 21, "long": 50}

    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [max(delta, 0) for delta in deltas]
        losses = [abs(min(delta, 0)) for delta in deltas]

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """Calculate MACD indicator"""
        if len(prices) < 26:
            return {"macd": 0.0, "signal": 0.0, "histogram": 0.0}

        # Simplified MACD calculation
        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)
        macd_line = ema_12 - ema_26

        # Signal line (9-period EMA of MACD)
        signal_line = macd_line * 0.9  # Simplified
        histogram = macd_line - signal_line

        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return sum(prices) / len(prices)

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def calculate_bollinger_bands(
        self, prices: List[float], period: int = 20
    ) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            mean_price = sum(prices) / len(prices)
            return {
                "upper": mean_price * 1.02,
                "middle": mean_price,
                "lower": mean_price * 0.98,
            }

        recent_prices = prices[-period:]
        mean_price = sum(recent_prices) / period
        variance = sum((p - mean_price) ** 2 for p in recent_prices) / period
        std_dev = variance**0.5

        return {
            "upper": mean_price + (2 * std_dev),
            "middle": mean_price,
            "lower": mean_price - (2 * std_dev),
        }

    def detect_chart_patterns(self, prices: List[float]) -> List[str]:
        """Detect common chart patterns"""
        patterns = []

        if len(prices) < 10:
            return patterns

        recent_prices = prices[-10:]

        # Simple pattern detection
        if self._is_ascending_triangle(recent_prices):
            patterns.append("ASCENDING_TRIANGLE")

        if self._is_double_bottom(recent_prices):
            patterns.append("DOUBLE_BOTTOM")

        if self._is_breakout(recent_prices):
            patterns.append("BREAKOUT")

        return patterns

    def _is_ascending_triangle(self, prices: List[float]) -> bool:
        """Detect ascending triangle pattern"""
        if len(prices) < 6:
            return False

        # Simplified detection: resistance level with higher lows
        resistance = max(prices[-5:])
        recent_lows = [
            min(prices[i : i + 3]) for i in range(len(prices) - 5, len(prices) - 2)
        ]

        return len(recent_lows) >= 2 and recent_lows[-1] > recent_lows[0]

    def _is_double_bottom(self, prices: List[float]) -> bool:
        """Detect double bottom pattern"""
        if len(prices) < 8:
            return False

        # Find two similar lows with a peak in between
        min_price = min(prices)
        min_indices = [
            i for i, p in enumerate(prices) if abs(p - min_price) / min_price < 0.02
        ]

        return len(min_indices) >= 2 and max(min_indices) - min(min_indices) >= 3

    def _is_breakout(self, prices: List[float]) -> bool:
        """Detect breakout pattern"""
        if len(prices) < 5:
            return False

        recent_high = max(prices[-5:-1])
        current_price = prices[-1]

        return current_price > recent_high * 1.03  # 3% breakout


class SentimentAnalyzer:
    """Advanced sentiment analysis system"""

    def __init__(self):
        self.sentiment_weights = {
            "price_momentum": 0.3,
            "volume_surge": 0.25,
            "social_signals": 0.2,
            "technical_indicators": 0.15,
            "market_structure": 0.1,
        }

    def analyze_market_sentiment(self, market_data: Dict) -> MarketSentiment:
        """Analyze overall market sentiment"""
        sentiment_scores = []

        for symbol, data in market_data.items():
            symbol_sentiment = self._analyze_symbol_sentiment(data)
            sentiment_scores.append(symbol_sentiment)

        if not sentiment_scores:
            return MarketSentiment.NEUTRAL

        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

        if avg_sentiment >= 1.5:
            return MarketSentiment.EXTREMELY_BULLISH
        elif avg_sentiment >= 0.5:
            return MarketSentiment.BULLISH
        elif avg_sentiment <= -1.5:
            return MarketSentiment.EXTREMELY_BEARISH
        elif avg_sentiment <= -0.5:
            return MarketSentiment.BEARISH
        else:
            return MarketSentiment.NEUTRAL

    def _analyze_symbol_sentiment(self, data: Dict) -> float:
        """Analyze sentiment for a single symbol"""
        sentiment_score = 0.0

        # Price momentum sentiment
        price_change = data.get("price_change_24h", 0)
        if price_change > 10:
            sentiment_score += 2 * self.sentiment_weights["price_momentum"]
        elif price_change > 5:
            sentiment_score += 1 * self.sentiment_weights["price_momentum"]
        elif price_change < -10:
            sentiment_score -= 2 * self.sentiment_weights["price_momentum"]
        elif price_change < -5:
            sentiment_score -= 1 * self.sentiment_weights["price_momentum"]

        # Volume surge sentiment
        volume = data.get("volume_24h", 0)
        if volume > 100000:  # High volume
            sentiment_score += 1 * self.sentiment_weights["volume_surge"]
        elif volume > 50000:  # Moderate volume
            sentiment_score += 0.5 * self.sentiment_weights["volume_surge"]

        # Technical indicators sentiment
        momentum_score = data.get("momentum_score", 5)
        if momentum_score > 7:
            sentiment_score += 1 * self.sentiment_weights["technical_indicators"]
        elif momentum_score < 3:
            sentiment_score -= 1 * self.sentiment_weights["technical_indicators"]

        return max(-2, min(2, sentiment_score))


class PredictiveModelingEngine:
    """Advanced predictive modeling for price forecasting"""

    def __init__(self):
        self.model_weights = {
            "technical": 0.4,
            "momentum": 0.3,
            "sentiment": 0.2,
            "volume": 0.1,
        }

    def predict_price_direction(
        self, intelligence: MarketIntelligence
    ) -> Dict[str, float]:
        """Predict price direction and probability"""

        # Technical prediction
        technical_score = self._calculate_technical_prediction(intelligence)

        # Momentum prediction
        momentum_score = self._calculate_momentum_prediction(intelligence)

        # Sentiment prediction
        sentiment_score = self._calculate_sentiment_prediction(intelligence)

        # Volume prediction
        volume_score = self._calculate_volume_prediction(intelligence)

        # Weighted prediction
        weighted_score = (
            technical_score * self.model_weights["technical"]
            + momentum_score * self.model_weights["momentum"]
            + sentiment_score * self.model_weights["sentiment"]
            + volume_score * self.model_weights["volume"]
        )

        # Convert to probability
        probability = (weighted_score + 1) / 2  # Convert from [-1, 1] to [0, 1]

        return {
            "direction": "UP" if weighted_score > 0 else "DOWN",
            "probability": probability,
            "confidence": intelligence.confidence_score,
            "technical_score": technical_score,
            "momentum_score": momentum_score,
            "sentiment_score": sentiment_score,
            "volume_score": volume_score,
        }

    def _calculate_technical_prediction(
        self, intelligence: MarketIntelligence
    ) -> float:
        """Calculate technical prediction score"""
        score = 0.0

        # RSI analysis
        rsi = intelligence.technical_indicators.get("rsi", 50)
        if rsi > 70:
            score -= 0.3  # Overbought
        elif rsi < 30:
            score += 0.3  # Oversold

        # MACD analysis
        macd_histogram = intelligence.technical_indicators.get("macd_histogram", 0)
        if macd_histogram > 0:
            score += 0.2
        elif macd_histogram < 0:
            score -= 0.2

        # Support/Resistance analysis
        current_price = intelligence.current_price
        nearest_resistance = min(
            [r for r in intelligence.resistance_levels if r > current_price],
            default=current_price * 1.1,
        )
        nearest_support = max(
            [s for s in intelligence.support_levels if s < current_price],
            default=current_price * 0.9,
        )

        distance_to_resistance = (nearest_resistance - current_price) / current_price
        distance_to_support = (current_price - nearest_support) / current_price

        if distance_to_resistance > 0.05:  # Far from resistance
            score += 0.2
        if distance_to_support < 0.03:  # Close to support
            score += 0.3

        return max(-1, min(1, score))

    def _calculate_momentum_prediction(self, intelligence: MarketIntelligence) -> float:
        """Calculate momentum prediction score"""
        momentum = intelligence.momentum_score / 10  # Normalize to [0, 1]

        if intelligence.trend_strength == TrendStrength.VERY_STRONG:
            momentum *= 1.2
        elif intelligence.trend_strength == TrendStrength.WEAK:
            momentum *= 0.8

        # Convert to [-1, 1] range
        return (momentum * 2) - 1

    def _calculate_sentiment_prediction(
        self, intelligence: MarketIntelligence
    ) -> float:
        """Calculate sentiment prediction score"""
        sentiment_map = {
            MarketSentiment.EXTREMELY_BEARISH: -1.0,
            MarketSentiment.BEARISH: -0.5,
            MarketSentiment.NEUTRAL: 0.0,
            MarketSentiment.BULLISH: 0.5,
            MarketSentiment.EXTREMELY_BULLISH: 1.0,
        }

        return sentiment_map.get(intelligence.sentiment, 0.0)

    def _calculate_volume_prediction(self, intelligence: MarketIntelligence) -> float:
        """Calculate volume prediction score"""
        volume_trend = intelligence.volume_profile.get("trend", 0)
        volume_surge = intelligence.volume_profile.get("surge_factor", 1)

        score = 0.0

        if volume_surge > 2:  # 2x volume surge
            score += 0.5
        elif volume_surge > 1.5:
            score += 0.3

        if volume_trend > 0:
            score += 0.2
        elif volume_trend < 0:
            score -= 0.2

        return max(-1, min(1, score))


class EnhancedMarketIntelligenceSystem:
    """Main market intelligence coordination system"""

    def __init__(self):
        self.technical_analyzer = AdvancedTechnicalAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.predictive_engine = PredictiveModelingEngine()

        self.intelligence_cache = {}
        self.sector_analysis_cache = {}

    async def generate_market_intelligence(
        self, market_data: Dict
    ) -> Dict[str, MarketIntelligence]:
        """Generate comprehensive market intelligence for all symbols"""
        intelligence_results = {}

        # Process symbols concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            tasks = []
            for symbol, data in market_data.items():
                task = executor.submit(self._analyze_symbol, symbol, data)
                tasks.append((symbol, task))

            for symbol, task in tasks:
                try:
                    intelligence = task.result(timeout=10)
                    intelligence_results[symbol] = intelligence
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")

        return intelligence_results

    def _analyze_symbol(self, symbol: str, data: Dict) -> MarketIntelligence:
        """Comprehensive analysis for a single symbol"""

        # Generate price history for technical analysis
        current_price = data.get("price", 0)
        price_history = self._generate_price_history(
            current_price, data.get("price_change_24h", 0)
        )

        # Technical analysis
        rsi = self.technical_analyzer.calculate_rsi(price_history)
        macd = self.technical_analyzer.calculate_macd(price_history)
        bollinger = self.technical_analyzer.calculate_bollinger_bands(price_history)
        patterns = self.technical_analyzer.detect_chart_patterns(price_history)

        # Technical indicators
        technical_indicators = {
            "rsi": rsi,
            "macd": macd["macd"],
            "macd_signal": macd["signal"],
            "macd_histogram": macd["histogram"],
            "bollinger_upper": bollinger["upper"],
            "bollinger_middle": bollinger["middle"],
            "bollinger_lower": bollinger["lower"],
        }

        # Sentiment analysis
        sentiment_score = self.sentiment_analyzer._analyze_symbol_sentiment(data)
        sentiment = self._score_to_sentiment(sentiment_score)

        # Trend analysis
        trend_direction = "UP" if data.get("price_change_24h", 0) > 0 else "DOWN"
        trend_strength = self._calculate_trend_strength(data)

        # Support and resistance levels
        support_levels = [
            current_price * 0.95,
            current_price * 0.90,
            current_price * 0.85,
        ]
        resistance_levels = [
            current_price * 1.05,
            current_price * 1.10,
            current_price * 1.15,
        ]

        # Volume profile
        volume_profile = {
            "current": data.get("volume_24h", 0),
            "trend": 1 if data.get("volume_24h", 0) > 50000 else -1,
            "surge_factor": min(data.get("volume_24h", 0) / 50000, 5.0),
        }

        # Risk factors and catalysts
        risk_factors = self._identify_risk_factors(data, technical_indicators)
        catalyst_events = self._identify_catalysts(data, patterns)

        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            data, technical_indicators, sentiment_score
        )

        return MarketIntelligence(
            symbol=symbol,
            current_price=current_price,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            sentiment=sentiment,
            momentum_score=data.get("momentum_score", 5.0),
            volatility_index=self._calculate_volatility_index(price_history),
            volume_profile=volume_profile,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            technical_indicators=technical_indicators,
            fundamental_score=self._calculate_fundamental_score(data),
            catalyst_events=catalyst_events,
            risk_factors=risk_factors,
            confidence_score=confidence_score,
        )

    def _generate_price_history(
        self, current_price: float, price_change: float
    ) -> List[float]:
        """Generate realistic price history for technical analysis"""
        history = []
        base_price = current_price / (1 + price_change / 100)

        # Generate 50 periods of price data
        for i in range(50):
            # Add some randomness
            random_factor = np.random.normal(1, 0.02)  # 2% volatility
            trend_factor = 1 + (price_change / 100) * (i / 50)
            price = base_price * trend_factor * random_factor
            history.append(max(price, 0.00001))  # Minimum price floor

        return history

    def _score_to_sentiment(self, score: float) -> MarketSentiment:
        """Convert sentiment score to sentiment enum"""
        if score >= 1.5:
            return MarketSentiment.EXTREMELY_BULLISH
        elif score >= 0.5:
            return MarketSentiment.BULLISH
        elif score <= -1.5:
            return MarketSentiment.EXTREMELY_BEARISH
        elif score <= -0.5:
            return MarketSentiment.BEARISH
        else:
            return MarketSentiment.NEUTRAL

    def _calculate_trend_strength(self, data: Dict) -> TrendStrength:
        """Calculate trend strength based on multiple factors"""
        momentum = data.get("momentum_score", 5.0)
        volume = data.get("volume_24h", 0)
        price_change = abs(data.get("price_change_24h", 0))

        strength_score = 0

        if momentum > 8:
            strength_score += 2
        elif momentum > 6:
            strength_score += 1

        if volume > 100000:
            strength_score += 2
        elif volume > 50000:
            strength_score += 1

        if price_change > 10:
            strength_score += 2
        elif price_change > 5:
            strength_score += 1

        if strength_score >= 5:
            return TrendStrength.VERY_STRONG
        elif strength_score >= 3:
            return TrendStrength.STRONG
        elif strength_score >= 1:
            return TrendStrength.MODERATE
        else:
            return TrendStrength.WEAK

    def _calculate_volatility_index(self, price_history: List[float]) -> float:
        """Calculate volatility index"""
        if len(price_history) < 2:
            return 0.3  # Default volatility

        returns = []
        for i in range(1, len(price_history)):
            return_pct = (price_history[i] - price_history[i - 1]) / price_history[
                i - 1
            ]
            returns.append(return_pct)

        volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
        return min(volatility, 2.0)  # Cap at 200%

    def _identify_risk_factors(
        self, data: Dict, technical_indicators: Dict
    ) -> List[str]:
        """Identify risk factors for the symbol"""
        risks = []

        # Technical risks
        if technical_indicators["rsi"] > 70:
            risks.append("OVERBOUGHT_CONDITION")

        if data.get("volume_24h", 0) < 10000:
            risks.append("LOW_LIQUIDITY")

        if abs(data.get("price_change_24h", 0)) > 20:
            risks.append("EXTREME_VOLATILITY")

        # Market structure risks
        price = data.get("price", 0)
        if price < 0.001:
            risks.append("ULTRA_LOW_PRICE")

        return risks

    def _identify_catalysts(self, data: Dict, patterns: List[str]) -> List[str]:
        """Identify potential catalysts"""
        catalysts = []

        # Technical catalysts
        if "BREAKOUT" in patterns:
            catalysts.append("TECHNICAL_BREAKOUT")

        if "ASCENDING_TRIANGLE" in patterns:
            catalysts.append("BULLISH_PATTERN")

        # Volume catalysts
        if data.get("volume_24h", 0) > 100000:
            catalysts.append("VOLUME_SURGE")

        # Momentum catalysts
        if data.get("momentum_score", 0) > 8:
            catalysts.append("STRONG_MOMENTUM")

        return catalysts

    def _calculate_fundamental_score(self, data: Dict) -> float:
        """Calculate fundamental score (simplified for crypto)"""
        score = 50.0  # Base score

        # Volume indicates adoption
        volume = data.get("volume_24h", 0)
        if volume > 100000:
            score += 20
        elif volume > 50000:
            score += 10

        # Price stability
        price_change = abs(data.get("price_change_24h", 0))
        if price_change < 5:
            score += 10
        elif price_change > 20:
            score -= 10

        return max(0, min(100, score))

    def _calculate_confidence_score(
        self, data: Dict, technical_indicators: Dict, sentiment_score: float
    ) -> float:
        """Calculate overall confidence score"""
        confidence = 50.0  # Base confidence

        # Volume confidence
        volume = data.get("volume_24h", 0)
        if volume > 50000:
            confidence += 15
        elif volume < 10000:
            confidence -= 20

        # Technical confidence
        rsi = technical_indicators["rsi"]
        if 30 <= rsi <= 70:  # Healthy RSI range
            confidence += 10

        # Sentiment confidence
        if abs(sentiment_score) > 0.5:  # Strong sentiment
            confidence += 10

        # Momentum confidence
        momentum = data.get("momentum_score", 5.0)
        if momentum > 7:
            confidence += 15
        elif momentum < 3:
            confidence -= 15

        return max(0, min(100, confidence))

    async def generate_predictions(
        self, intelligence_data: Dict[str, MarketIntelligence]
    ) -> Dict[str, Dict]:
        """Generate predictions for all symbols"""
        predictions = {}

        for symbol, intelligence in intelligence_data.items():
            prediction = self.predictive_engine.predict_price_direction(intelligence)
            predictions[symbol] = prediction

        return predictions


async def main():
    """Main execution function for market intelligence system"""
    print("🎯 ENHANCED MARKET INTELLIGENCE SYSTEM")
    print("=" * 60)
    print("🧠 Advanced market analysis with AI-powered insights")
    print()

    # Sample market data
    market_data = {
        "SHIBUSDT": {
            "price": 0.00001194,
            "volume_24h": 76215.30,
            "price_change_24h": 5.2,
            "momentum_score": 8.1,
        },
        "FLOKIUSDT": {
            "price": 0.00010212,
            "volume_24h": 67310.0,
            "price_change_24h": 3.8,
            "momentum_score": 7.8,
        },
        "BONKUSDT": {
            "price": 0.00002443,
            "volume_24h": 46821.0,
            "price_change_24h": 4.1,
            "momentum_score": 7.7,
        },
        "PEPEUSDT": {
            "price": 0.00001006,
            "volume_24h": 30349.0,
            "price_change_24h": 2.3,
            "momentum_score": 6.9,
        },
    }

    # Initialize intelligence system
    intelligence_system = EnhancedMarketIntelligenceSystem()

    print("⚡ Generating market intelligence...")
    intelligence_data = await intelligence_system.generate_market_intelligence(
        market_data
    )

    print("🔮 Generating predictions...")
    predictions = await intelligence_system.generate_predictions(intelligence_data)

    print(f"\n📊 MARKET INTELLIGENCE REPORT")
    print("=" * 50)

    for symbol, intelligence in intelligence_data.items():
        prediction = predictions.get(symbol, {})

        print(f"\n🎯 {symbol}")
        print("-" * 20)
        print(f"Price: ${intelligence.current_price:.8f}")
        print(
            f"Trend: {intelligence.trend_direction} ({intelligence.trend_strength.name})"
        )
        print(f"Sentiment: {intelligence.sentiment.name}")
        print(f"Momentum Score: {intelligence.momentum_score:.1f}/10")
        print(f"Confidence: {intelligence.confidence_score:.1f}%")
        print(f"Volatility Index: {intelligence.volatility_index:.2f}")

        print(f"\n📈 Technical Indicators:")
        print(f"  RSI: {intelligence.technical_indicators['rsi']:.1f}")
        print(f"  MACD: {intelligence.technical_indicators['macd']:.6f}")

        print(f"\n🔮 Prediction:")
        print(f"  Direction: {prediction.get('direction', 'N/A')}")
        print(f"  Probability: {prediction.get('probability', 0):.1%}")

        if intelligence.catalyst_events:
            print(f"\n⚡ Catalysts: {', '.join(intelligence.catalyst_events)}")

        if intelligence.risk_factors:
            print(f"⚠️ Risks: {', '.join(intelligence.risk_factors)}")

    # Save intelligence report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"market_intelligence_report_{timestamp}.json"

    # Prepare data for JSON serialization
    intelligence_dict = {}
    for symbol, intelligence in intelligence_data.items():
        intelligence_dict[symbol] = {
            "symbol": intelligence.symbol,
            "current_price": intelligence.current_price,
            "trend_direction": intelligence.trend_direction,
            "trend_strength": intelligence.trend_strength.name,
            "sentiment": intelligence.sentiment.name,
            "momentum_score": intelligence.momentum_score,
            "volatility_index": intelligence.volatility_index,
            "volume_profile": intelligence.volume_profile,
            "support_levels": intelligence.support_levels,
            "resistance_levels": intelligence.resistance_levels,
            "technical_indicators": intelligence.technical_indicators,
            "fundamental_score": intelligence.fundamental_score,
            "catalyst_events": intelligence.catalyst_events,
            "risk_factors": intelligence.risk_factors,
            "confidence_score": intelligence.confidence_score,
            "prediction": predictions.get(symbol, {}),
        }

    with open(filename, "w") as f:
        json.dump(intelligence_dict, f, indent=2, default=str)

    print(f"\n💾 Intelligence report saved: {filename}")
    print("\n✅ MARKET INTELLIGENCE ANALYSIS COMPLETE!")


if __name__ == "__main__":
    asyncio.run(main())
