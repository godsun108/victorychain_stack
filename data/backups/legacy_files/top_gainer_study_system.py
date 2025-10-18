#!/usr/bin/env python3
"""
Top Gainer Analysis & Learning System
Study the highest performing token to learn winning characteristics and patterns
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from binance.client import Client
from dotenv import load_dotenv


class TopGainerStudySystem:
    def __init__(self):
        load_dotenv()

        # Initialize Binance client
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        print("🏆 Top Gainer Analysis & Learning System initialized")
        print("📊 Ready to identify and study winning patterns...")

    def get_top_gainers(self, limit: int = 50) -> List[Dict]:
        """Get top gainers from current market data"""

        print("🚀 Identifying top gainers...")

        # Get all tickers
        tickers = self.client.get_ticker()

        # Filter USDT pairs and sort by price change
        usdt_tickers = [
            t
            for t in tickers
            if t["symbol"].endswith("USDT") and float(t["priceChangePercent"]) > 0
        ]

        # Sort by price change percentage
        usdt_tickers.sort(key=lambda x: float(x["priceChangePercent"]), reverse=True)

        top_gainers = []
        for ticker in usdt_tickers[:limit]:
            top_gainers.append(
                {
                    "symbol": ticker["symbol"],
                    "price_change_percent": float(ticker["priceChangePercent"]),
                    "price_change": float(ticker["priceChange"]),
                    "last_price": float(ticker["lastPrice"]),
                    "volume": float(ticker["volume"]),
                    "quote_volume": float(ticker["quoteVolume"]),
                    "high_24h": float(ticker["highPrice"]),
                    "low_24h": float(ticker["lowPrice"]),
                    "open_price": float(ticker["openPrice"]),
                    "weighted_avg_price": float(ticker["weightedAvgPrice"]),
                    "trade_count": int(ticker["count"]),
                }
            )

        print(f"✅ Found {len(top_gainers)} gainers")
        return top_gainers

    def analyze_historical_data(self, symbol: str, days: int = 7) -> Dict:
        """Get detailed historical analysis for a symbol"""

        print(f"📈 Analyzing historical data for {symbol}...")

        try:
            # Get multiple timeframes
            klines_1h = self.client.get_klines(
                symbol=symbol, interval="1h", limit=24 * days
            )
            klines_4h = self.client.get_klines(
                symbol=symbol, interval="4h", limit=6 * days
            )
            klines_1d = self.client.get_klines(symbol=symbol, interval="1d", limit=days)

            # Parse data
            def parse_klines(klines):
                df = pd.DataFrame(
                    klines,
                    columns=[
                        "timestamp",
                        "open",
                        "high",
                        "low",
                        "close",
                        "volume",
                        "close_time",
                        "quote_volume",
                        "count",
                        "taker_buy_volume",
                        "taker_buy_quote_volume",
                        "ignore",
                    ],
                )

                for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
                    df[col] = pd.to_numeric(df[col])

                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                return df

            df_1h = parse_klines(klines_1h)
            df_4h = parse_klines(klines_4h)
            df_1d = parse_klines(klines_1d)

            # Calculate advanced metrics
            analysis = {
                "price_metrics": self.calculate_price_metrics(df_1h, df_4h, df_1d),
                "volume_analysis": self.analyze_volume_patterns(df_1h, df_4h),
                "momentum_indicators": self.calculate_momentum_indicators(df_1h),
                "volatility_analysis": self.analyze_volatility(df_1h, df_4h),
                "pattern_recognition": self.identify_patterns(df_1h, df_4h, df_1d),
                "breakout_analysis": self.analyze_breakouts(df_1h, df_4h),
                "support_resistance": self.find_support_resistance(df_1h),
            }

            return analysis

        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {str(e)}")
            return {}

    def calculate_price_metrics(
        self, df_1h: pd.DataFrame, df_4h: pd.DataFrame, df_1d: pd.DataFrame
    ) -> Dict:
        """Calculate comprehensive price metrics"""

        current_price = df_1h["close"].iloc[-1]

        # Price changes over different periods
        price_1h_ago = df_1h["close"].iloc[-2] if len(df_1h) > 1 else current_price
        price_4h_ago = df_1h["close"].iloc[-5] if len(df_1h) > 4 else current_price
        price_24h_ago = df_1h["close"].iloc[-25] if len(df_1h) > 24 else current_price
        price_7d_ago = df_1d["close"].iloc[0] if len(df_1d) > 0 else current_price

        # Calculate returns
        return_1h = (current_price - price_1h_ago) / price_1h_ago * 100
        return_4h = (current_price - price_4h_ago) / price_4h_ago * 100
        return_24h = (current_price - price_24h_ago) / price_24h_ago * 100
        return_7d = (current_price - price_7d_ago) / price_7d_ago * 100

        # High/Low analysis
        high_24h = df_1h["high"].tail(24).max()
        low_24h = df_1h["low"].tail(24).min()
        high_7d = df_1h["high"].max()
        low_7d = df_1h["low"].min()

        # Position in range
        range_position_24h = (
            (current_price - low_24h) / (high_24h - low_24h)
            if high_24h != low_24h
            else 0.5
        )
        range_position_7d = (
            (current_price - low_7d) / (high_7d - low_7d) if high_7d != low_7d else 0.5
        )

        return {
            "current_price": current_price,
            "returns": {
                "1h": return_1h,
                "4h": return_4h,
                "24h": return_24h,
                "7d": return_7d,
            },
            "highs_lows": {
                "high_24h": high_24h,
                "low_24h": low_24h,
                "high_7d": high_7d,
                "low_7d": low_7d,
            },
            "range_positions": {"24h": range_position_24h, "7d": range_position_7d},
            "price_velocity": return_1h,  # Rate of change
            "momentum_strength": abs(return_4h),
        }

    def analyze_volume_patterns(self, df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> Dict:
        """Analyze volume patterns and trends"""

        # Volume metrics
        current_volume = df_1h["volume"].iloc[-1]
        avg_volume_24h = df_1h["volume"].tail(24).mean()
        avg_volume_7d = df_1h["volume"].mean()

        # Volume ratios
        volume_ratio_24h = current_volume / avg_volume_24h if avg_volume_24h > 0 else 1
        volume_ratio_7d = current_volume / avg_volume_7d if avg_volume_7d > 0 else 1

        # Volume trend
        recent_volume = df_1h["volume"].tail(6).mean()  # Last 6 hours
        earlier_volume = df_1h["volume"].tail(12).head(6).mean()  # 6-12 hours ago
        volume_trend = (
            (recent_volume - earlier_volume) / earlier_volume
            if earlier_volume > 0
            else 0
        )

        # Volume spikes
        volume_threshold = avg_volume_24h * 2
        volume_spikes = (df_1h["volume"].tail(24) > volume_threshold).sum()

        # Price-volume correlation
        price_changes = df_1h["close"].pct_change().tail(24)
        volume_changes = df_1h["volume"].pct_change().tail(24)
        price_volume_corr = price_changes.corr(volume_changes)

        return {
            "current_volume": current_volume,
            "volume_ratios": {"24h": volume_ratio_24h, "7d": volume_ratio_7d},
            "volume_trend": volume_trend,
            "volume_spikes_24h": volume_spikes,
            "avg_volumes": {"24h": avg_volume_24h, "7d": avg_volume_7d},
            "price_volume_correlation": price_volume_corr,
            "volume_pattern": (
                "SURGE"
                if volume_ratio_24h > 3
                else "HIGH" if volume_ratio_24h > 1.5 else "NORMAL"
            ),
        }

    def calculate_momentum_indicators(self, df_1h: pd.DataFrame) -> Dict:
        """Calculate momentum and technical indicators"""

        close = df_1h["close"]
        high = df_1h["high"]
        low = df_1h["low"]

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        macd_histogram = macd - macd_signal

        # Stochastic
        lowest_low = low.rolling(window=14).min()
        highest_high = high.rolling(window=14).max()
        stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        stoch_d = stoch_k.rolling(window=3).mean()

        # Moving averages
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        ema_20 = close.ewm(span=20).mean()

        current_price = close.iloc[-1]

        return {
            "rsi": current_rsi,
            "macd": {
                "macd": macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else 0,
                "signal": (
                    macd_signal.iloc[-1] if not pd.isna(macd_signal.iloc[-1]) else 0
                ),
                "histogram": (
                    macd_histogram.iloc[-1]
                    if not pd.isna(macd_histogram.iloc[-1])
                    else 0
                ),
            },
            "stochastic": {
                "k": stoch_k.iloc[-1] if not pd.isna(stoch_k.iloc[-1]) else 50,
                "d": stoch_d.iloc[-1] if not pd.isna(stoch_d.iloc[-1]) else 50,
            },
            "moving_averages": {
                "sma_20": (
                    sma_20.iloc[-1] if not pd.isna(sma_20.iloc[-1]) else current_price
                ),
                "sma_50": (
                    sma_50.iloc[-1] if not pd.isna(sma_50.iloc[-1]) else current_price
                ),
                "ema_20": (
                    ema_20.iloc[-1] if not pd.isna(ema_20.iloc[-1]) else current_price
                ),
            },
            "ma_positions": {
                "above_sma_20": (
                    current_price > sma_20.iloc[-1]
                    if not pd.isna(sma_20.iloc[-1])
                    else False
                ),
                "above_sma_50": (
                    current_price > sma_50.iloc[-1]
                    if not pd.isna(sma_50.iloc[-1])
                    else False
                ),
                "above_ema_20": (
                    current_price > ema_20.iloc[-1]
                    if not pd.isna(ema_20.iloc[-1])
                    else False
                ),
            },
        }

    def analyze_volatility(self, df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> Dict:
        """Analyze volatility patterns"""

        # Price volatility
        returns_1h = df_1h["close"].pct_change()
        volatility_1h = returns_1h.std()
        volatility_24h = returns_1h.tail(24).std()

        returns_4h = df_4h["close"].pct_change()
        volatility_4h = returns_4h.std()

        # Bollinger Bands
        sma_20 = df_1h["close"].rolling(window=20).mean()
        std_20 = df_1h["close"].rolling(window=20).std()
        bb_upper = sma_20 + (std_20 * 2)
        bb_lower = sma_20 - (std_20 * 2)
        current_price = df_1h["close"].iloc[-1]

        bb_position = (
            (current_price - bb_lower.iloc[-1])
            / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
            if not pd.isna(bb_upper.iloc[-1])
            else 0.5
        )
        bb_squeeze = (
            (bb_upper.iloc[-1] - bb_lower.iloc[-1]) / sma_20.iloc[-1]
            if not pd.isna(sma_20.iloc[-1])
            else 0
        )

        return {
            "volatility_metrics": {
                "1h": volatility_1h,
                "24h": volatility_24h,
                "4h": volatility_4h,
            },
            "bollinger_bands": {
                "position": bb_position,
                "squeeze": bb_squeeze,
                "upper": (
                    bb_upper.iloc[-1]
                    if not pd.isna(bb_upper.iloc[-1])
                    else current_price
                ),
                "lower": (
                    bb_lower.iloc[-1]
                    if not pd.isna(bb_lower.iloc[-1])
                    else current_price
                ),
            },
            "volatility_regime": (
                "HIGH"
                if volatility_24h > 0.05
                else "MEDIUM" if volatility_24h > 0.02 else "LOW"
            ),
        }

    def identify_patterns(
        self, df_1h: pd.DataFrame, df_4h: pd.DataFrame, df_1d: pd.DataFrame
    ) -> Dict:
        """Identify chart patterns and trends"""

        patterns = []

        # Trend analysis
        close_1d = df_1d["close"]
        if len(close_1d) >= 3:
            if close_1d.iloc[-1] > close_1d.iloc[-2] > close_1d.iloc[-3]:
                patterns.append("UPTREND_DAILY")
            elif close_1d.iloc[-1] < close_1d.iloc[-2] < close_1d.iloc[-3]:
                patterns.append("DOWNTREND_DAILY")

        # Breakout patterns
        close_1h = df_1h["close"]
        high_1h = df_1h["high"]
        low_1h = df_1h["low"]

        # Recent high breakout
        recent_high = high_1h.tail(24).max()
        previous_high = high_1h.tail(48).head(24).max()
        if recent_high > previous_high * 1.02:
            patterns.append("HIGH_BREAKOUT")

        # Volume confirmation
        current_volume = df_1h["volume"].iloc[-1]
        avg_volume = df_1h["volume"].tail(24).mean()
        if current_volume > avg_volume * 2:
            patterns.append("VOLUME_BREAKOUT")

        # Consolidation break
        recent_range = high_1h.tail(12).max() - low_1h.tail(12).min()
        earlier_range = high_1h.tail(24).head(12).max() - low_1h.tail(24).head(12).min()
        if recent_range > earlier_range * 1.5:
            patterns.append("RANGE_EXPANSION")

        return {
            "identified_patterns": patterns,
            "trend_strength": len([p for p in patterns if "TREND" in p]),
            "breakout_signals": len([p for p in patterns if "BREAKOUT" in p]),
            "pattern_score": len(patterns),
        }

    def analyze_breakouts(self, df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> Dict:
        """Analyze breakout characteristics"""

        close = df_1h["close"]
        high = df_1h["high"]
        low = df_1h["low"]
        volume = df_1h["volume"]

        # Price breakout analysis
        current_price = close.iloc[-1]

        # Resistance levels (recent highs)
        resistance_levels = []
        for i in range(12, len(high) - 12):
            if high.iloc[i] == high.iloc[i - 12 : i + 13].max():
                resistance_levels.append(high.iloc[i])

        # Support levels (recent lows)
        support_levels = []
        for i in range(12, len(low) - 12):
            if low.iloc[i] == low.iloc[i - 12 : i + 13].min():
                support_levels.append(low.iloc[i])

        # Find nearest levels
        nearest_resistance = min(
            [r for r in resistance_levels if r > current_price],
            default=current_price * 1.1,
        )
        nearest_support = max(
            [s for s in support_levels if s < current_price],
            default=current_price * 0.9,
        )

        # Breakout strength
        breakout_strength = 0
        if resistance_levels:
            recent_resistance = max(
                [r for r in resistance_levels if r < current_price * 1.05], default=0
            )
            if recent_resistance > 0:
                breakout_strength = (
                    current_price - recent_resistance
                ) / recent_resistance

        return {
            "resistance_levels": resistance_levels[-5:] if resistance_levels else [],
            "support_levels": support_levels[-5:] if support_levels else [],
            "nearest_resistance": nearest_resistance,
            "nearest_support": nearest_support,
            "breakout_strength": breakout_strength,
            "distance_to_resistance": (nearest_resistance - current_price)
            / current_price,
            "distance_to_support": (current_price - nearest_support) / current_price,
        }

    def find_support_resistance(self, df_1h: pd.DataFrame) -> Dict:
        """Find key support and resistance levels"""

        close = df_1h["close"]
        high = df_1h["high"]
        low = df_1h["low"]

        # Pivot points
        current_price = close.iloc[-1]

        # Recent pivot highs and lows
        pivot_highs = []
        pivot_lows = []

        for i in range(5, len(df_1h) - 5):
            # Pivot high
            if high.iloc[i] == high.iloc[i - 5 : i + 6].max():
                pivot_highs.append((i, high.iloc[i]))

            # Pivot low
            if low.iloc[i] == low.iloc[i - 5 : i + 6].min():
                pivot_lows.append((i, low.iloc[i]))

        # Key levels (price levels that appear multiple times)
        price_levels = [p[1] for p in pivot_highs] + [p[1] for p in pivot_lows]

        # Group similar prices
        key_levels = []
        tolerance = current_price * 0.02  # 2% tolerance

        for level in price_levels:
            if not any(abs(level - kl) < tolerance for kl in key_levels):
                key_levels.append(level)

        key_levels.sort()

        return {
            "pivot_highs": pivot_highs[-10:],  # Last 10 pivot highs
            "pivot_lows": pivot_lows[-10:],  # Last 10 pivot lows
            "key_levels": key_levels,
            "current_level_position": (
                sum(1 for level in key_levels if level < current_price)
                / len(key_levels)
                if key_levels
                else 0.5
            ),
        }

    def calculate_winner_traits(
        self, symbol: str, gainer_data: Dict, historical_analysis: Dict
    ) -> Dict:
        """Calculate and identify the winning traits of the top gainer"""

        print(f"🧠 Analyzing winning traits for {symbol}...")

        traits = {}
        trait_scores = {}

        # Price performance traits
        price_change = gainer_data["price_change_percent"]
        traits["exceptional_performance"] = price_change > 8
        trait_scores["performance_score"] = min(price_change / 10, 1.0)

        # Volume traits
        volume_analysis = historical_analysis.get("volume_analysis", {})
        volume_ratio = volume_analysis.get("volume_ratios", {}).get("24h", 1)
        traits["high_volume_surge"] = volume_ratio > 2
        trait_scores["volume_score"] = min(volume_ratio / 3, 1.0)

        # Momentum traits
        momentum = historical_analysis.get("momentum_indicators", {})
        rsi = momentum.get("rsi", 50)
        traits["momentum_confirmation"] = 50 < rsi < 80  # Not overbought but strong
        trait_scores["momentum_score"] = 1.0 - abs(rsi - 65) / 65 if rsi > 50 else 0

        # Breakout traits
        breakout_analysis = historical_analysis.get("breakout_analysis", {})
        breakout_strength = breakout_analysis.get("breakout_strength", 0)
        traits["clean_breakout"] = breakout_strength > 0.05
        trait_scores["breakout_score"] = min(breakout_strength * 10, 1.0)

        # Pattern traits
        patterns = historical_analysis.get("pattern_recognition", {})
        pattern_score = patterns.get("pattern_score", 0)
        traits["multiple_bullish_patterns"] = pattern_score >= 2
        trait_scores["pattern_score"] = min(pattern_score / 3, 1.0)

        # Volatility traits
        volatility = historical_analysis.get("volatility_analysis", {})
        volatility_regime = volatility.get("volatility_regime", "LOW")
        traits["controlled_volatility"] = volatility_regime in ["MEDIUM", "HIGH"]
        trait_scores["volatility_score"] = (
            0.8
            if volatility_regime == "MEDIUM"
            else 0.6 if volatility_regime == "HIGH" else 0.3
        )

        # Technical position traits
        price_metrics = historical_analysis.get("price_metrics", {})
        range_position = price_metrics.get("range_positions", {}).get("24h", 0.5)
        traits["strong_position_in_range"] = range_position > 0.7
        trait_scores["position_score"] = range_position

        # Moving average traits
        ma_positions = momentum.get("ma_positions", {})
        above_ma_count = sum(ma_positions.values())
        traits["above_key_moving_averages"] = above_ma_count >= 2
        trait_scores["ma_score"] = above_ma_count / 3

        # Calculate overall winner score
        overall_score = np.mean(list(trait_scores.values()))

        return {
            "symbol": symbol,
            "winning_traits": traits,
            "trait_scores": trait_scores,
            "overall_winner_score": overall_score,
            "key_success_factors": [trait for trait, value in traits.items() if value],
            "improvement_areas": [
                trait for trait, value in traits.items() if not value
            ],
        }

    def generate_learning_insights(
        self, winner_analysis: Dict, all_gainers: List[Dict]
    ) -> Dict:
        """Generate actionable learning insights from the top performer"""

        symbol = winner_analysis["symbol"]
        traits = winner_analysis["winning_traits"]
        scores = winner_analysis["trait_scores"]

        insights = {
            "primary_success_pattern": self.identify_primary_pattern(winner_analysis),
            "replicable_strategies": self.extract_strategies(winner_analysis),
            "market_timing_lessons": self.analyze_timing(winner_analysis),
            "risk_management_insights": self.extract_risk_insights(winner_analysis),
            "screening_criteria": self.generate_screening_criteria(winner_analysis),
            "action_plan": self.create_action_plan(winner_analysis),
        }

        return insights

    def identify_primary_pattern(self, winner_analysis: Dict) -> Dict:
        """Identify the primary success pattern"""

        scores = winner_analysis["trait_scores"]
        traits = winner_analysis["winning_traits"]

        # Find highest scoring traits
        top_traits = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]

        # Determine pattern type
        if (
            scores.get("breakout_score", 0) > 0.7
            and scores.get("volume_score", 0) > 0.7
        ):
            pattern_type = "VOLUME_BREAKOUT"
        elif (
            scores.get("momentum_score", 0) > 0.7
            and scores.get("performance_score", 0) > 0.8
        ):
            pattern_type = "MOMENTUM_SURGE"
        elif scores.get("pattern_score", 0) > 0.7:
            pattern_type = "TECHNICAL_PATTERN"
        else:
            pattern_type = "MIXED_BULLISH"

        return {
            "pattern_type": pattern_type,
            "key_indicators": [trait[0] for trait in top_traits],
            "strength_scores": dict(top_traits),
            "confidence": winner_analysis["overall_winner_score"],
        }

    def extract_strategies(self, winner_analysis: Dict) -> List[Dict]:
        """Extract replicable trading strategies"""

        strategies = []
        traits = winner_analysis["winning_traits"]
        scores = winner_analysis["trait_scores"]

        # Volume breakout strategy
        if traits.get("high_volume_surge") and traits.get("clean_breakout"):
            strategies.append(
                {
                    "name": "Volume Breakout Strategy",
                    "entry_criteria": [
                        "Volume surge > 2x average",
                        "Price breaks resistance with >5% strength",
                        "RSI between 50-80",
                    ],
                    "success_probability": (
                        scores.get("volume_score", 0) + scores.get("breakout_score", 0)
                    )
                    / 2,
                }
            )

        # Momentum continuation strategy
        if traits.get("momentum_confirmation") and traits.get(
            "above_key_moving_averages"
        ):
            strategies.append(
                {
                    "name": "Momentum Continuation Strategy",
                    "entry_criteria": [
                        "Price above key moving averages",
                        "RSI showing strength (50-80)",
                        "Multiple bullish pattern confirmation",
                    ],
                    "success_probability": (
                        scores.get("momentum_score", 0) + scores.get("ma_score", 0)
                    )
                    / 2,
                }
            )

        # Pattern breakout strategy
        if traits.get("multiple_bullish_patterns") and traits.get(
            "strong_position_in_range"
        ):
            strategies.append(
                {
                    "name": "Pattern Breakout Strategy",
                    "entry_criteria": [
                        "Multiple bullish patterns identified",
                        "Strong position in trading range (>70%)",
                        "Volume confirmation",
                    ],
                    "success_probability": scores.get("pattern_score", 0),
                }
            )

        return strategies

    def analyze_timing(self, winner_analysis: Dict) -> Dict:
        """Analyze market timing lessons"""

        return {
            "optimal_entry_timing": "Early breakout confirmation with volume",
            "market_conditions": "Medium to high volatility with clear directional bias",
            "time_of_day_factors": "High activity periods with institutional participation",
            "confluence_factors": "Multiple technical confirmations aligned",
        }

    def extract_risk_insights(self, winner_analysis: Dict) -> Dict:
        """Extract risk management insights"""

        traits = winner_analysis["winning_traits"]

        return {
            "risk_characteristics": {
                "volatility_managed": traits.get("controlled_volatility", False),
                "strong_momentum": traits.get("momentum_confirmation", False),
                "technical_support": traits.get("above_key_moving_averages", False),
            },
            "risk_mitigation": [
                "Use controlled position sizing during high volatility",
                "Set stop losses below key support levels",
                "Take partial profits at resistance levels",
                "Monitor volume for continuation signals",
            ],
        }

    def generate_screening_criteria(self, winner_analysis: Dict) -> List[str]:
        """Generate screening criteria based on winner traits"""

        scores = winner_analysis["trait_scores"]

        criteria = []

        if scores.get("performance_score", 0) > 0.5:
            criteria.append("Price change > 5% in 24h")

        if scores.get("volume_score", 0) > 0.5:
            criteria.append("Volume > 1.5x average")

        if scores.get("momentum_score", 0) > 0.5:
            criteria.append("RSI between 50-80")

        if scores.get("breakout_score", 0) > 0.3:
            criteria.append("Recent breakout above resistance")

        if scores.get("ma_score", 0) > 0.5:
            criteria.append("Price above 20-period moving average")

        criteria.append("Multiple timeframe alignment")
        criteria.append("Strong technical pattern formation")

        return criteria

    def create_action_plan(self, winner_analysis: Dict) -> Dict:
        """Create actionable trading plan based on analysis"""

        return {
            "immediate_actions": [
                f"Study {winner_analysis['symbol']} setup in detail",
                "Create alerts for similar setups",
                "Backtest identified patterns",
                "Set up screening filters",
            ],
            "monitoring_plan": [
                "Track volume patterns hourly",
                "Monitor breakout confirmations",
                "Watch for similar setups in other tokens",
                "Document pattern outcomes",
            ],
            "implementation_strategy": [
                "Start with small position sizes",
                "Use multiple confirmation signals",
                "Set clear risk parameters",
                "Maintain trading journal",
            ],
        }

    def run_complete_top_gainer_study(self) -> Dict:
        """Run complete top gainer analysis and learning system"""

        print("🏆 STARTING TOP GAINER ANALYSIS & LEARNING SYSTEM")
        print("=" * 70)

        start_time = time.time()

        # Step 1: Get top gainers
        top_gainers = self.get_top_gainers(20)

        if not top_gainers:
            print("❌ No gainers found")
            return {}

        # Step 2: Select the top performer
        best_performer = top_gainers[0]
        symbol = best_performer["symbol"]

        print(f"\n🎯 TOP PERFORMER IDENTIFIED: {symbol}")
        print(f"📈 Performance: +{best_performer['price_change_percent']:.2f}%")
        print(f"💰 Price: ${best_performer['last_price']:.4f}")
        print(f"📊 Volume: {best_performer['quote_volume']:,.0f} USDT")

        # Step 3: Deep historical analysis
        historical_analysis = self.analyze_historical_data(symbol, days=7)

        # Step 4: Calculate winner traits
        winner_analysis = self.calculate_winner_traits(
            symbol, best_performer, historical_analysis
        )

        # Step 5: Generate learning insights
        learning_insights = self.generate_learning_insights(
            winner_analysis, top_gainers
        )

        # Compile final results
        results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_duration": time.time() - start_time,
            "top_performer": {
                "symbol": symbol,
                "performance_data": best_performer,
                "historical_analysis": historical_analysis,
            },
            "winner_analysis": winner_analysis,
            "learning_insights": learning_insights,
            "top_gainers_context": top_gainers[:10],  # Top 10 for context
            "market_summary": {
                "total_gainers_analyzed": len(top_gainers),
                "average_gain": np.mean(
                    [g["price_change_percent"] for g in top_gainers]
                ),
                "median_gain": np.median(
                    [g["price_change_percent"] for g in top_gainers]
                ),
                "top_performance": best_performer["price_change_percent"],
            },
        }

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"top_gainer_study_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Print detailed analysis
        self.print_winner_analysis(results)

        print(f"\n✅ Top Gainer Study completed!")
        print(f"📁 Results saved to: {filename}")
        print(f"⏱️  Analysis duration: {results['analysis_duration']:.1f} seconds")

        return results

    def print_winner_analysis(self, results: Dict):
        """Print detailed winner analysis"""

        print("\n" + "=" * 80)
        print("🏆 TOP GAINER WINNER ANALYSIS")
        print("=" * 80)

        top_performer = results["top_performer"]
        winner_analysis = results["winner_analysis"]
        learning_insights = results["learning_insights"]

        symbol = top_performer["symbol"]
        performance = top_performer["performance_data"]

        print(f"\n🎯 WINNER: {symbol}")
        print(f"   Performance: +{performance['price_change_percent']:.2f}%")
        print(f"   Current Price: ${performance['last_price']:.4f}")
        print(f"   24h Volume: {performance['quote_volume']:,.0f} USDT")
        print(f"   24h High: ${performance['high_24h']:.4f}")
        print(f"   24h Low: ${performance['low_24h']:.4f}")

        print(
            f"\n🧠 WINNING TRAITS (Score: {winner_analysis['overall_winner_score']:.2f}):"
        )
        for trait, value in winner_analysis["winning_traits"].items():
            status = "✅" if value else "❌"
            score = winner_analysis["trait_scores"].get(trait.replace("_", "_"), 0)
            print(f"   {status} {trait.replace('_', ' ').title()}: {score:.2f}")

        print(f"\n🎯 KEY SUCCESS FACTORS:")
        for factor in winner_analysis["key_success_factors"]:
            print(f"   • {factor.replace('_', ' ').title()}")

        print(f"\n📈 PRIMARY SUCCESS PATTERN:")
        primary_pattern = learning_insights["primary_success_pattern"]
        print(f"   Pattern Type: {primary_pattern['pattern_type']}")
        print(f"   Confidence: {primary_pattern['confidence']:.2f}")
        print(f"   Key Indicators: {', '.join(primary_pattern['key_indicators'])}")

        print(f"\n🚀 REPLICABLE STRATEGIES:")
        for i, strategy in enumerate(learning_insights["replicable_strategies"], 1):
            print(
                f"   {i}. {strategy['name']} (Success Prob: {strategy['success_probability']:.2f})"
            )
            for criteria in strategy["entry_criteria"]:
                print(f"      • {criteria}")

        print(f"\n🔍 SCREENING CRITERIA FOR SIMILAR SETUPS:")
        for criteria in learning_insights["screening_criteria"]:
            print(f"   • {criteria}")

        print(f"\n💡 ACTION PLAN:")
        action_plan = learning_insights["action_plan"]
        print(f"   📋 Immediate Actions:")
        for action in action_plan["immediate_actions"]:
            print(f"      • {action}")

        print(f"   📊 Implementation Strategy:")
        for strategy in action_plan["implementation_strategy"]:
            print(f"      • {strategy}")


def main():
    """Main execution function"""

    print("🏆 TOP GAINER ANALYSIS & LEARNING SYSTEM 🏆")
    print("=" * 60)

    system = TopGainerStudySystem()

    # Run complete analysis
    results = system.run_complete_top_gainer_study()

    print("\n🎉 Analysis complete! Study the winner and replicate success!")


if __name__ == "__main__":
    main()
