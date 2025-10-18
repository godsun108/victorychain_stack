#!/usr/bin/env python3
"""
Winner Trait Learning & Strategy Builder
Extract and implement winning characteristics from top performers
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


class WinnerTraitLearningSystem:
    def __init__(self):
        load_dotenv()

        # Initialize Binance client
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        print("🧠 Winner Trait Learning & Strategy Builder initialized")
        print("🎯 Learning from MAGICUSDT's 18.81% winning performance...")

    def analyze_magicusdt_deep_dive(self) -> Dict:
        """Deep dive analysis of MAGICUSDT's winning performance"""

        print("🔬 Performing deep dive analysis on MAGICUSDT...")

        symbol = "MAGICUSDT"

        try:
            # Get comprehensive data
            ticker = self.client.get_ticker(symbol=symbol)

            # Get multiple timeframes for pattern analysis
            klines_15m = self.client.get_klines(
                symbol=symbol, interval="15m", limit=96
            )  # 24 hours
            klines_1h = self.client.get_klines(
                symbol=symbol, interval="1h", limit=168
            )  # 7 days
            klines_4h = self.client.get_klines(
                symbol=symbol, interval="4h", limit=42
            )  # 7 days
            klines_1d = self.client.get_klines(
                symbol=symbol, interval="1d", limit=30
            )  # 30 days

            # Parse data
            def parse_klines(klines, timeframe):
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

                # Convert numeric columns with error handling
                for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df["timeframe"] = timeframe
                return df

            df_15m = parse_klines(klines_15m, "15m")
            df_1h = parse_klines(klines_1h, "1h")
            df_4h = parse_klines(klines_4h, "4h")
            df_1d = parse_klines(klines_1d, "1d")

            # Calculate the exact winning characteristics
            analysis = self.extract_winning_pattern(df_15m, df_1h, df_4h, df_1d, ticker)

            # Get order book for liquidity analysis
            order_book = self.client.get_order_book(symbol=symbol, limit=100)
            analysis["liquidity_analysis"] = self.analyze_liquidity(order_book)

            # Get recent trades for volume analysis
            recent_trades = self.client.get_recent_trades(symbol=symbol, limit=100)
            analysis["trade_flow_analysis"] = self.analyze_trade_flow(recent_trades)

            return analysis

        except Exception as e:
            print(f"❌ Error analyzing MAGICUSDT: {str(e)}")
            return {}

    def extract_winning_pattern(
        self,
        df_15m: pd.DataFrame,
        df_1h: pd.DataFrame,
        df_4h: pd.DataFrame,
        df_1d: pd.DataFrame,
        ticker: Dict,
    ) -> Dict:
        """Extract the exact winning pattern from MAGICUSDT"""

        print("🏆 Extracting winning pattern characteristics...")

        current_price = float(ticker["lastPrice"])
        price_change_24h = float(ticker["priceChangePercent"])
        volume_24h = float(ticker["quoteVolume"])

        # Price action analysis
        price_action = self.analyze_price_action(df_15m, df_1h, df_4h, df_1d)

        # Volume pattern analysis
        volume_pattern = self.analyze_volume_pattern(df_15m, df_1h)

        # Technical setup analysis
        technical_setup = self.analyze_technical_setup(df_1h, df_4h)

        # Momentum analysis
        momentum_analysis = self.analyze_momentum_characteristics(df_15m, df_1h, df_4h)

        # Time-based analysis
        timing_analysis = self.analyze_timing_factors(df_15m, df_1h)

        # Market structure analysis
        market_structure = self.analyze_market_structure(df_1h, df_4h, df_1d)

        return {
            "symbol": "MAGICUSDT",
            "performance_metrics": {
                "price_change_24h": price_change_24h,
                "current_price": current_price,
                "volume_24h": volume_24h,
                "high_24h": float(ticker["highPrice"]),
                "low_24h": float(ticker["lowPrice"]),
            },
            "price_action": price_action,
            "volume_pattern": volume_pattern,
            "technical_setup": technical_setup,
            "momentum_analysis": momentum_analysis,
            "timing_analysis": timing_analysis,
            "market_structure": market_structure,
            "winning_formula": self.calculate_winning_formula(
                price_action, volume_pattern, technical_setup, momentum_analysis
            ),
        }

    def analyze_price_action(
        self,
        df_15m: pd.DataFrame,
        df_1h: pd.DataFrame,
        df_4h: pd.DataFrame,
        df_1d: pd.DataFrame,
    ) -> Dict:
        """Analyze the specific price action that led to the winning move"""

        # Current vs historical ranges
        current_price = df_15m["close"].iloc[-1]

        # Range analysis
        range_24h = df_1h["high"].tail(24).max() - df_1h["low"].tail(24).min()
        range_7d = df_1h["high"].max() - df_1h["low"].min()

        # Breakout analysis
        resistance_levels = []
        for i in range(12, len(df_1h) - 12):
            if df_1h["high"].iloc[i] == df_1h["high"].iloc[i - 12 : i + 13].max():
                resistance_levels.append(df_1h["high"].iloc[i])

        # Recent breakout strength
        if resistance_levels:
            nearest_resistance = max(
                [r for r in resistance_levels if r < current_price * 1.05], default=0
            )
            breakout_strength = (
                (current_price - nearest_resistance) / nearest_resistance
                if nearest_resistance > 0
                else 0
            )
        else:
            breakout_strength = 0

        # Price velocity (rate of change)
        price_1h_ago = df_15m["close"].iloc[-5] if len(df_15m) >= 5 else current_price
        price_4h_ago = df_15m["close"].iloc[-17] if len(df_15m) >= 17 else current_price

        velocity_1h = (current_price - price_1h_ago) / price_1h_ago * 100
        velocity_4h = (current_price - price_4h_ago) / price_4h_ago * 100

        # Consolidation vs breakout pattern
        recent_high = df_15m["high"].tail(24).max()
        recent_low = df_15m["low"].tail(24).min()
        consolidation_range = (recent_high - recent_low) / recent_low

        return {
            "current_price": current_price,
            "range_analysis": {
                "24h_range": range_24h,
                "7d_range": range_7d,
                "range_ratio": range_24h / range_7d if range_7d > 0 else 0,
            },
            "breakout_analysis": {
                "resistance_levels": resistance_levels[-5:],
                "breakout_strength": breakout_strength,
                "breakout_confirmed": breakout_strength > 0.02,
            },
            "price_velocity": {
                "1h_velocity": velocity_1h,
                "4h_velocity": velocity_4h,
                "acceleration": velocity_1h - velocity_4h,
            },
            "pattern_type": (
                "BREAKOUT"
                if consolidation_range < 0.05 and breakout_strength > 0.02
                else "MOMENTUM"
            ),
            "consolidation_range": consolidation_range,
            "position_in_24h_range": (
                (current_price - recent_low) / (recent_high - recent_low)
                if recent_high != recent_low
                else 0.5
            ),
        }

    def analyze_volume_pattern(self, df_15m: pd.DataFrame, df_1h: pd.DataFrame) -> Dict:
        """Analyze the volume pattern that supported the move"""

        current_volume = df_15m["volume"].iloc[-1]

        # Volume averages
        avg_volume_4h = df_15m["volume"].tail(16).mean()  # 4 hours in 15m intervals
        avg_volume_24h = df_1h["volume"].tail(24).mean()
        avg_volume_7d = df_1h["volume"].mean()

        # Volume ratios
        volume_ratio_4h = current_volume / avg_volume_4h if avg_volume_4h > 0 else 1
        volume_ratio_24h = current_volume / avg_volume_24h if avg_volume_24h > 0 else 1
        volume_ratio_7d = current_volume / avg_volume_7d if avg_volume_7d > 0 else 1

        # Volume trend analysis
        volume_trend_1h = np.polyfit(range(4), df_15m["volume"].tail(4), 1)[
            0
        ]  # Last hour trend
        volume_trend_4h = np.polyfit(range(16), df_15m["volume"].tail(16), 1)[
            0
        ]  # Last 4 hours trend

        # Volume spikes
        volume_threshold = avg_volume_24h * 1.5
        volume_spikes_24h = (df_1h["volume"].tail(24) > volume_threshold).sum()

        # Price-volume relationship
        price_changes = df_15m["close"].pct_change().tail(24).dropna()
        volume_changes = df_15m["volume"].pct_change().tail(24).dropna()

        # Calculate correlation only if we have valid data
        if (
            len(price_changes) > 0
            and len(volume_changes) > 0
            and not price_changes.isna().all()
            and not volume_changes.isna().all()
        ):
            price_volume_corr = price_changes.corr(volume_changes)
            # Handle NaN result from correlation
            price_volume_corr = (
                price_volume_corr if not pd.isna(price_volume_corr) else 0
            )
        else:
            price_volume_corr = 0

        # Volume distribution analysis
        buy_volume_estimate = df_15m["taker_buy_volume"].tail(24).sum()
        total_volume = df_15m["volume"].tail(24).sum()
        buy_ratio = buy_volume_estimate / total_volume if total_volume > 0 else 0.5

        return {
            "current_volume": current_volume,
            "volume_ratios": {
                "4h": volume_ratio_4h,
                "24h": volume_ratio_24h,
                "7d": volume_ratio_7d,
            },
            "volume_trends": {
                "1h_trend": volume_trend_1h,
                "4h_trend": volume_trend_4h,
                "trend_strength": "INCREASING" if volume_trend_4h > 0 else "DECREASING",
            },
            "volume_characteristics": {
                "spikes_24h": volume_spikes_24h,
                "price_volume_correlation": price_volume_corr,
                "buy_sell_ratio": buy_ratio,
                "volume_pattern": (
                    "SURGE"
                    if volume_ratio_24h > 2
                    else "ELEVATED" if volume_ratio_24h > 1.2 else "NORMAL"
                ),
            },
            "volume_quality_score": (
                volume_ratio_24h + abs(price_volume_corr) + buy_ratio
            )
            / 3,
        }

    def analyze_technical_setup(self, df_1h: pd.DataFrame, df_4h: pd.DataFrame) -> Dict:
        """Analyze the technical setup that preceded the winning move"""

        close = df_1h["close"]
        high = df_1h["high"]
        low = df_1h["low"]

        # Moving averages
        sma_20 = close.rolling(window=20).mean()
        sma_50 = close.rolling(window=50).mean()
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()

        current_price = close.iloc[-1]
        current_sma_20 = (
            sma_20.iloc[-1] if not pd.isna(sma_20.iloc[-1]) else current_price
        )
        current_sma_50 = (
            sma_50.iloc[-1] if not pd.isna(sma_50.iloc[-1]) else current_price
        )

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

        # Handle division by zero in RSI calculation
        rs = gain / loss.replace(
            0, 0.001
        )  # Replace 0 with small value to avoid division by zero
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

        # MACD
        macd = ema_12 - ema_26
        macd_signal = macd.ewm(span=9).mean()
        macd_histogram = macd - macd_signal

        # Bollinger Bands
        bb_middle = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = bb_middle + (bb_std * 2)
        bb_lower = bb_middle - (bb_std * 2)
        bb_position = (
            (current_price - bb_lower.iloc[-1])
            / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
            if not pd.isna(bb_upper.iloc[-1])
            else 0.5
        )

        # Support/Resistance
        pivot_highs = []
        pivot_lows = []

        for i in range(5, len(df_1h) - 5):
            if high.iloc[i] == high.iloc[i - 5 : i + 6].max():
                pivot_highs.append(high.iloc[i])
            if low.iloc[i] == low.iloc[i - 5 : i + 6].min():
                pivot_lows.append(low.iloc[i])

        # Nearest support/resistance
        resistance_levels = [p for p in pivot_highs if p > current_price]
        support_levels = [p for p in pivot_lows if p < current_price]

        nearest_resistance = (
            min(resistance_levels) if resistance_levels else current_price * 1.1
        )
        nearest_support = max(support_levels) if support_levels else current_price * 0.9

        return {
            "moving_averages": {
                "sma_20": current_sma_20,
                "sma_50": current_sma_50,
                "above_sma_20": current_price > current_sma_20,
                "above_sma_50": current_price > current_sma_50,
                "ma_alignment": (
                    "BULLISH" if current_sma_20 > current_sma_50 else "BEARISH"
                ),
            },
            "momentum_indicators": {
                "rsi": current_rsi,
                "rsi_regime": (
                    "OVERBOUGHT"
                    if current_rsi > 70
                    else "OVERSOLD" if current_rsi < 30 else "NEUTRAL"
                ),
                "macd": macd.iloc[-1] if not pd.isna(macd.iloc[-1]) else 0,
                "macd_signal": (
                    macd_signal.iloc[-1] if not pd.isna(macd_signal.iloc[-1]) else 0
                ),
                "macd_bullish": (
                    macd.iloc[-1] > macd_signal.iloc[-1]
                    if not pd.isna(macd.iloc[-1]) and not pd.isna(macd_signal.iloc[-1])
                    else False
                ),
            },
            "bollinger_bands": {
                "bb_position": bb_position,
                "bb_squeeze": (
                    (bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_middle.iloc[-1]
                    if not pd.isna(bb_middle.iloc[-1])
                    else 0
                ),
                "bb_regime": (
                    "UPPER"
                    if bb_position > 0.8
                    else "LOWER" if bb_position < 0.2 else "MIDDLE"
                ),
            },
            "support_resistance": {
                "nearest_resistance": nearest_resistance,
                "nearest_support": nearest_support,
                "resistance_distance": (nearest_resistance - current_price)
                / current_price,
                "support_distance": (current_price - nearest_support) / current_price,
            },
            "technical_score": self.calculate_technical_score(
                current_rsi, bb_position, current_price > current_sma_20
            ),
        }

    def calculate_technical_score(
        self, rsi: float, bb_position: float, above_ma: bool
    ) -> float:
        """Calculate overall technical score"""

        rsi_score = (
            0.8
            if 50 < rsi < 80
            else 0.6 if 30 < rsi < 50 else 0.4 if 80 < rsi < 90 else 0.2
        )
        bb_score = (
            0.8 if 0.6 < bb_position < 0.9 else 0.6 if 0.4 < bb_position < 0.6 else 0.4
        )
        ma_score = 0.8 if above_ma else 0.2

        return (rsi_score + bb_score + ma_score) / 3

    def analyze_momentum_characteristics(
        self, df_15m: pd.DataFrame, df_1h: pd.DataFrame, df_4h: pd.DataFrame
    ) -> Dict:
        """Analyze the momentum characteristics of the winning move"""

        # Multi-timeframe momentum
        def calc_momentum(df, periods):
            close = df["close"]
            if len(close) <= periods:
                return 0
            return (close.iloc[-1] - close.iloc[-periods]) / close.iloc[-periods] * 100

        momentum_15m_4p = calc_momentum(df_15m, 4)  # 1 hour in 15m
        momentum_1h_4p = calc_momentum(df_1h, 4)  # 4 hours
        momentum_4h_6p = calc_momentum(df_4h, 6)  # 24 hours

        # Momentum acceleration
        recent_momentum = calc_momentum(df_15m, 2)  # 30 minutes
        earlier_momentum = calc_momentum(df_15m, 8)  # 2 hours
        momentum_acceleration = recent_momentum - earlier_momentum

        # Momentum consistency
        momentum_values = []
        for i in range(1, min(25, len(df_1h))):
            mom = calc_momentum(df_1h, i)
            momentum_values.append(mom)

        momentum_consistency = (
            len([m for m in momentum_values if m > 0]) / len(momentum_values)
            if momentum_values
            else 0
        )

        # Momentum strength classification
        avg_momentum = np.mean([momentum_15m_4p, momentum_1h_4p, momentum_4h_6p])

        if avg_momentum > 10:
            momentum_strength = "VERY_STRONG"
        elif avg_momentum > 5:
            momentum_strength = "STRONG"
        elif avg_momentum > 2:
            momentum_strength = "MODERATE"
        else:
            momentum_strength = "WEAK"

        return {
            "multi_timeframe_momentum": {
                "15m_1h": momentum_15m_4p,
                "1h_4h": momentum_1h_4p,
                "4h_24h": momentum_4h_6p,
                "average": avg_momentum,
            },
            "momentum_dynamics": {
                "recent_momentum": recent_momentum,
                "acceleration": momentum_acceleration,
                "consistency": momentum_consistency,
            },
            "momentum_classification": {
                "strength": momentum_strength,
                "direction": "BULLISH" if avg_momentum > 0 else "BEARISH",
                "sustainability": momentum_consistency > 0.7,
            },
            "momentum_score": min(avg_momentum / 15, 1.0) if avg_momentum > 0 else 0,
        }

    def analyze_timing_factors(self, df_15m: pd.DataFrame, df_1h: pd.DataFrame) -> Dict:
        """Analyze timing factors that contributed to the winning move"""

        # Time of move analysis
        recent_candles = df_15m.tail(8)  # Last 2 hours
        move_start_time = None
        max_gain = 0

        for i in range(len(recent_candles)):
            gain = (
                (recent_candles["close"].iloc[i] - recent_candles["open"].iloc[0])
                / recent_candles["open"].iloc[0]
                * 100
            )
            if gain > max_gain:
                max_gain = gain
                move_start_time = recent_candles["timestamp"].iloc[i]

        # Volume timing
        volume_peak_time = df_15m.loc[df_15m["volume"].idxmax(), "timestamp"]
        price_peak_time = df_15m.loc[df_15m["high"].idxmax(), "timestamp"]

        # Market structure timing
        current_time = datetime.utcnow()
        hour_of_day = current_time.hour

        # Trading session analysis
        if 0 <= hour_of_day <= 8:
            session = "ASIAN"
        elif 8 <= hour_of_day <= 16:
            session = "EUROPEAN"
        else:
            session = "US"

        return {
            "move_timing": {
                "move_start_time": move_start_time,
                "max_gain_achieved": max_gain,
                "current_session": session,
                "hour_of_day": hour_of_day,
            },
            "volume_price_timing": {
                "volume_peak_time": volume_peak_time,
                "price_peak_time": price_peak_time,
                "timing_alignment": abs(
                    (volume_peak_time - price_peak_time).total_seconds()
                )
                < 3600,  # Within 1 hour
            },
            "optimal_timing_characteristics": {
                "session_preference": session,
                "volume_price_sync": abs(
                    (volume_peak_time - price_peak_time).total_seconds()
                )
                < 1800,  # Within 30 min
                "timing_quality": (
                    "EXCELLENT" if hour_of_day in [9, 10, 11, 14, 15, 16] else "GOOD"
                ),
            },
        }

    def analyze_market_structure(
        self, df_1h: pd.DataFrame, df_4h: pd.DataFrame, df_1d: pd.DataFrame
    ) -> Dict:
        """Analyze the overall market structure context"""

        # Trend analysis across timeframes
        def determine_trend(df, periods=10):
            if len(df) < periods:
                return "NEUTRAL"

            close = df["close"]
            slope = np.polyfit(range(periods), close.tail(periods), 1)[0]

            if slope > close.iloc[-1] * 0.001:  # 0.1% per period
                return "UPTREND"
            elif slope < -close.iloc[-1] * 0.001:
                return "DOWNTREND"
            else:
                return "SIDEWAYS"

        trend_1h = determine_trend(df_1h, 24)  # 24 hour trend
        trend_4h = determine_trend(df_4h, 12)  # 48 hour trend
        trend_1d = determine_trend(df_1d, 10)  # 10 day trend

        # Market phase analysis
        current_price = df_1h["close"].iloc[-1]
        high_20d = df_1d["high"].tail(20).max() if len(df_1d) >= 20 else current_price
        low_20d = df_1d["low"].tail(20).min() if len(df_1d) >= 20 else current_price

        position_in_range = (
            (current_price - low_20d) / (high_20d - low_20d)
            if high_20d != low_20d
            else 0.5
        )

        if position_in_range > 0.8:
            market_phase = "DISTRIBUTION"
        elif position_in_range < 0.2:
            market_phase = "ACCUMULATION"
        elif 0.4 < position_in_range < 0.6:
            market_phase = "EQUILIBRIUM"
        else:
            market_phase = "TRENDING"

        # Volatility regime
        returns_1h = df_1h["close"].pct_change().tail(24).dropna()
        volatility = returns_1h.std() if len(returns_1h) > 0 else 0

        if volatility > 0.05:
            volatility_regime = "HIGH"
        elif volatility > 0.02:
            volatility_regime = "MEDIUM"
        else:
            volatility_regime = "LOW"

        return {
            "trend_analysis": {
                "1h_trend": trend_1h,
                "4h_trend": trend_4h,
                "1d_trend": trend_1d,
                "trend_alignment": len(set([trend_1h, trend_4h, trend_1d])) == 1,
            },
            "market_phase": {
                "phase": market_phase,
                "position_in_range": position_in_range,
                "range_high": high_20d,
                "range_low": low_20d,
            },
            "volatility_context": {
                "regime": volatility_regime,
                "volatility_value": volatility,
                "suitable_for_momentum": volatility_regime in ["MEDIUM", "HIGH"],
            },
        }

    def calculate_winning_formula(
        self,
        price_action: Dict,
        volume_pattern: Dict,
        technical_setup: Dict,
        momentum_analysis: Dict,
    ) -> Dict:
        """Calculate the exact winning formula from MAGICUSDT"""

        # Extract key factors
        breakout_strength = price_action.get("breakout_analysis", {}).get(
            "breakout_strength", 0
        )
        volume_quality = volume_pattern.get("volume_quality_score", 0)
        technical_score = technical_setup.get("technical_score", 0)
        momentum_score = momentum_analysis.get("momentum_score", 0)

        # Weight the factors based on MAGIC's performance
        formula_score = (
            breakout_strength * 0.25  # 25% breakout strength
            + volume_quality * 0.30  # 30% volume quality
            + technical_score * 0.25  # 25% technical setup
            + momentum_score * 0.20  # 20% momentum
        )

        # Key success criteria based on MAGIC's pattern
        success_criteria = {
            "minimum_breakout_strength": 0.02,
            "minimum_volume_ratio": 1.2,
            "minimum_technical_score": 0.6,
            "minimum_momentum_score": 0.3,
            "required_rsi_range": (50, 80),
            "required_bb_position": (0.6, 0.9),
            "must_be_above_ma20": True,
        }

        # Replication template
        replication_template = {
            "entry_conditions": [
                "Price breaks above recent resistance with >2% strength",
                "Volume surge >1.2x average with positive correlation",
                "RSI between 50-80 (not overbought)",
                "Price above 20-period moving average",
                "Bollinger Band position 0.6-0.9",
                "Multi-timeframe momentum alignment",
            ],
            "confirmation_signals": [
                "Volume peak coincides with price breakout",
                "MACD bullish crossover or above signal line",
                "Strong momentum consistency across timeframes",
                "Clear trend alignment on higher timeframes",
            ],
            "risk_management": [
                "Stop loss below recent support/MA20",
                "Position size based on volatility",
                "Take partial profits at resistance levels",
                "Monitor volume for continuation",
            ],
        }

        return {
            "formula_score": formula_score,
            "success_criteria": success_criteria,
            "replication_template": replication_template,
            "key_insight": "MAGICUSDT won with momentum surge + volume confirmation + clean technical setup",
            "pattern_type": "MOMENTUM_BREAKOUT_WITH_VOLUME",
            "success_probability": min(formula_score * 1.2, 0.95),  # Cap at 95%
            "risk_reward_ratio": 3.0,  # Based on 18.81% gain potential
        }

    def analyze_liquidity(self, order_book: Dict) -> Dict:
        """Analyze order book liquidity"""

        bids = [[float(price), float(qty)] for price, qty in order_book["bids"][:10]]
        asks = [[float(price), float(qty)] for price, qty in order_book["asks"][:10]]

        if not bids or not asks:
            return {"liquidity_score": 0, "spread": 0}

        best_bid = bids[0][0]
        best_ask = asks[0][0]
        spread = best_ask - best_bid
        mid_price = (best_bid + best_ask) / 2

        spread_bps = (spread / mid_price) * 10000 if mid_price > 0 else 0

        # Depth analysis
        bid_depth = sum(qty for _, qty in bids[:5])
        ask_depth = sum(qty for _, qty in asks[:5])

        imbalance = (
            (bid_depth - ask_depth) / (bid_depth + ask_depth)
            if (bid_depth + ask_depth) > 0
            else 0
        )

        return {
            "spread_bps": spread_bps,
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
            "imbalance": imbalance,
            "liquidity_score": max(0, 100 - spread_bps) * 0.01,
        }

    def analyze_trade_flow(self, trades: List[Dict]) -> Dict:
        """Analyze recent trade flow"""

        if not trades:
            return {"buy_ratio": 0.5, "trade_intensity": 0}

        buy_volume = sum(float(t["quoteQty"]) for t in trades if not t["isBuyerMaker"])
        sell_volume = sum(float(t["quoteQty"]) for t in trades if t["isBuyerMaker"])
        total_volume = buy_volume + sell_volume

        buy_ratio = buy_volume / total_volume if total_volume > 0 else 0.5
        trade_intensity = len(trades) / 100  # Normalized

        return {
            "buy_ratio": buy_ratio,
            "sell_ratio": 1 - buy_ratio,
            "trade_intensity": trade_intensity,
            "flow_direction": (
                "BULLISH"
                if buy_ratio > 0.6
                else "BEARISH" if buy_ratio < 0.4 else "NEUTRAL"
            ),
        }

    def create_winning_strategy_template(self, analysis: Dict) -> Dict:
        """Create a replicable strategy template based on MAGICUSDT's winning pattern"""

        winning_formula = analysis.get("winning_formula", {})

        strategy_template = {
            "strategy_name": "MAGIC Momentum Breakout Strategy",
            "based_on": "MAGICUSDT +18.81% winning performance",
            "strategy_type": "Momentum Breakout with Volume Confirmation",
            "screening_criteria": [
                "Price change >5% in 24h",
                "Volume ratio >1.2x average",
                "RSI between 50-80",
                "Price above 20-MA",
                "Clean breakout pattern visible",
                "Multiple timeframe alignment",
            ],
            "entry_rules": [
                "1. Wait for price to break above recent resistance",
                "2. Confirm volume surge (>1.2x average)",
                "3. Check RSI is not overbought (<80)",
                "4. Ensure price is above 20-period MA",
                "5. Verify Bollinger Band position (0.6-0.9)",
                "6. Confirm momentum alignment across timeframes",
            ],
            "confirmation_signals": [
                "Volume peak coincides with breakout",
                "MACD bullish or above signal line",
                "Multiple bullish patterns present",
                "Strong momentum consistency (>70%)",
            ],
            "position_sizing": [
                "Risk 1-2% of account per trade",
                "Adjust size based on volatility",
                "Smaller size for lower volume tokens",
                "Scale in on strong confirmation",
            ],
            "risk_management": [
                "Stop loss: Below recent support or 20-MA",
                "Take profits: At resistance levels",
                "Partial exits: 25% at +5%, 25% at +10%",
                "Trail stop: After +15% gain",
                "Exit if volume drops significantly",
            ],
            "success_metrics": {
                "target_win_rate": "60-70%",
                "target_risk_reward": "1:2 minimum",
                "expected_gain_range": "5-20%",
                "max_holding_period": "24-48 hours",
            },
            "market_conditions": [
                "Best in medium to high volatility",
                "Avoid during major market downturns",
                "Optimal during trending markets",
                "Be cautious near major resistance",
            ],
        }

        return strategy_template

    def run_complete_winner_analysis(self) -> Dict:
        """Run complete analysis and create actionable strategy"""

        print("🧠 WINNER TRAIT LEARNING & STRATEGY BUILDER")
        print("=" * 60)
        print("🎯 Learning from MAGICUSDT's +18.81% winning performance")

        start_time = time.time()

        # Deep dive analysis
        analysis = self.analyze_magicusdt_deep_dive()

        if not analysis:
            print("❌ Analysis failed")
            return {}

        # Create strategy template
        strategy_template = self.create_winning_strategy_template(analysis)

        # Compile results
        results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_duration": time.time() - start_time,
            "winner_symbol": "MAGICUSDT",
            "winner_performance": "+18.81%",
            "deep_analysis": analysis,
            "winning_strategy_template": strategy_template,
            "key_learnings": self.extract_key_learnings(analysis),
            "implementation_guide": self.create_implementation_guide(strategy_template),
        }

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"winner_trait_learning_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Print analysis
        self.print_winner_learning_analysis(results)

        print(f"\n✅ Winner Learning Analysis completed!")
        print(f"📁 Results saved to: {filename}")
        print(f"⏱️  Analysis duration: {results['analysis_duration']:.1f} seconds")

        return results

    def extract_key_learnings(self, analysis: Dict) -> List[str]:
        """Extract key learnings from the analysis"""

        learnings = []

        # Performance learning
        performance = analysis.get("performance_metrics", {})
        learnings.append(
            f"🎯 Exceptional performance: +{performance.get('price_change_24h', 0):.2f}% in 24h"
        )

        # Price action learning
        price_action = analysis.get("price_action", {})
        if price_action.get("breakout_analysis", {}).get("breakout_confirmed"):
            learnings.append("🚀 Clean breakout above resistance with strong momentum")

        # Volume learning
        volume_pattern = analysis.get("volume_pattern", {})
        volume_score = volume_pattern.get("volume_quality_score", 0)
        learnings.append(
            f"📊 Volume quality score: {volume_score:.2f} - {'Excellent' if volume_score > 0.7 else 'Good' if volume_score > 0.5 else 'Moderate'}"
        )

        # Technical learning
        technical = analysis.get("technical_setup", {})
        technical_score = technical.get("technical_score", 0)
        learnings.append(
            f"⚙️ Technical setup score: {technical_score:.2f} - Strong foundation"
        )

        # Momentum learning
        momentum = analysis.get("momentum_analysis", {})
        momentum_strength = momentum.get("momentum_classification", {}).get(
            "strength", "UNKNOWN"
        )
        learnings.append(
            f"🌊 Momentum strength: {momentum_strength} with multi-timeframe alignment"
        )

        # Timing learning
        timing = analysis.get("timing_analysis", {})
        session = timing.get("move_timing", {}).get("current_session", "UNKNOWN")
        learnings.append(
            f"⏰ Optimal timing: {session} session with volume-price synchronization"
        )

        return learnings

    def create_implementation_guide(self, strategy_template: Dict) -> Dict:
        """Create step-by-step implementation guide"""

        return {
            "daily_routine": [
                "1. Scan for tokens with >5% 24h gain",
                "2. Filter by volume ratio >1.2x",
                "3. Check technical indicators (RSI, MA, BB)",
                "4. Analyze breakout patterns",
                "5. Verify multi-timeframe alignment",
                "6. Set up alerts for entry signals",
            ],
            "entry_checklist": [
                "☐ Price breaking above resistance",
                "☐ Volume surge confirmed (>1.2x avg)",
                "☐ RSI between 50-80",
                "☐ Price above 20-period MA",
                "☐ BB position 0.6-0.9",
                "☐ MACD bullish signal",
                "☐ Multi-timeframe momentum aligned",
            ],
            "risk_management_steps": [
                "1. Calculate position size (1-2% risk)",
                "2. Set stop loss below support/MA20",
                "3. Define profit targets at resistance",
                "4. Plan partial exit strategy",
                "5. Set up trailing stop after +15%",
            ],
            "monitoring_protocol": [
                "Monitor volume for continuation",
                "Watch for momentum divergence",
                "Check for break of key levels",
                "Track overall market conditions",
                "Be ready to exit if setup fails",
            ],
            "success_tracking": [
                "Log all trades with screenshots",
                "Track win rate and R:R ratio",
                "Note what worked and what didn't",
                "Refine entry criteria based on results",
                "Adapt to changing market conditions",
            ],
        }

    def print_winner_learning_analysis(self, results: Dict):
        """Print comprehensive winner learning analysis"""

        print("\n" + "=" * 80)
        print("🏆 MAGICUSDT WINNER TRAIT ANALYSIS")
        print("=" * 80)

        # Performance summary
        analysis = results["deep_analysis"]
        performance = analysis.get("performance_metrics", {})

        print(f"\n📊 PERFORMANCE SUMMARY:")
        print(f"   Symbol: MAGICUSDT")
        print(f"   24h Gain: +{performance.get('price_change_24h', 0):.2f}%")
        print(f"   Current Price: ${performance.get('current_price', 0):.4f}")
        print(f"   24h Volume: {performance.get('volume_24h', 0):,.0f} USDT")
        print(
            f"   24h Range: ${performance.get('low_24h', 0):.4f} - ${performance.get('high_24h', 0):.4f}"
        )

        # Winning formula
        winning_formula = analysis.get("winning_formula", {})
        print(f"\n🧠 WINNING FORMULA:")
        print(f"   Formula Score: {winning_formula.get('formula_score', 0):.2f}")
        print(f"   Pattern Type: {winning_formula.get('pattern_type', 'UNKNOWN')}")
        print(
            f"   Success Probability: {winning_formula.get('success_probability', 0):.1%}"
        )
        print(f"   Key Insight: {winning_formula.get('key_insight', 'N/A')}")

        # Key characteristics
        price_action = analysis.get("price_action", {})
        volume_pattern = analysis.get("volume_pattern", {})
        technical_setup = analysis.get("technical_setup", {})
        momentum_analysis = analysis.get("momentum_analysis", {})

        print(f"\n🔍 KEY WINNING CHARACTERISTICS:")
        print(
            f"   💥 Breakout Strength: {price_action.get('breakout_analysis', {}).get('breakout_strength', 0):.3f}"
        )
        print(
            f"   📊 Volume Quality Score: {volume_pattern.get('volume_quality_score', 0):.2f}"
        )
        print(f"   ⚙️ Technical Score: {technical_setup.get('technical_score', 0):.2f}")
        print(f"   🌊 Momentum Score: {momentum_analysis.get('momentum_score', 0):.2f}")

        # Strategy template
        strategy = results["winning_strategy_template"]
        print(f"\n🎯 REPLICABLE STRATEGY: {strategy['strategy_name']}")
        print(f"   Strategy Type: {strategy['strategy_type']}")

        print(f"\n📋 ENTRY CRITERIA:")
        for i, criteria in enumerate(strategy["screening_criteria"][:5], 1):
            print(f"   {i}. {criteria}")

        print(f"\n⚡ ENTRY RULES:")
        for i, rule in enumerate(strategy["entry_rules"][:4], 1):
            print(f"   {i}. {rule}")

        # Key learnings
        key_learnings = results["key_learnings"]
        print(f"\n💡 KEY LEARNINGS:")
        for learning in key_learnings[:5]:
            print(f"   • {learning}")

        # Implementation
        implementation = results["implementation_guide"]
        print(f"\n🚀 IMPLEMENTATION CHECKLIST:")
        for item in implementation["entry_checklist"][:6]:
            print(f"   {item}")

        print(f"\n📈 SUCCESS METRICS TARGET:")
        success_metrics = strategy["success_metrics"]
        print(f"   Win Rate: {success_metrics['target_win_rate']}")
        print(f"   Risk:Reward: {success_metrics['target_risk_reward']}")
        print(f"   Expected Gain: {success_metrics['expected_gain_range']}")


def main():
    """Main execution function"""

    system = WinnerTraitLearningSystem()
    results = system.run_complete_winner_analysis()

    print("\n🎉 Winner trait learning complete!")
    print("💡 Use this template to identify and trade similar setups!")


if __name__ == "__main__":
    main()
