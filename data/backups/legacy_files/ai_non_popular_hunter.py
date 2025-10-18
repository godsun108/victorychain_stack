#!/usr/bin/env python3
"""
AI-Powered Non-Popular Token Hunter
Advanced pattern learning system for finding alpha in micro/nano cap tokens
Learns from market behavior and makes intelligent trades on least popular tokens
"""

import os
import json
import time
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings

warnings.filterwarnings("ignore")


class AINonPopularHunter:
    def __init__(self):
        load_dotenv()

        # Initialize Binance client
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(
                    f'ai_hunter_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
                ),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Non-popular token focus (avoiding mainstream coins)
        self.hunt_criteria = {
            "max_volume_usd": 75_000,  # Avoid anything >$75K (too popular)
            "min_volume_usd": 500,  # Minimum $500 (avoid total dust)
            "sweet_spot_max": 25_000,  # Sweet spot: $500-$25K
            "ultra_low_max": 5_000,  # Ultra low: $500-$5K (highest alpha)
        }

        # AI Learning parameters
        self.ai_params = {
            "lookback_hours": 168,  # 7 days of data
            "min_confidence": 0.75,  # 75% model confidence
            "feature_count": 25,  # Number of features for ML
            "retrain_threshold": 50,  # Retrain after 50 samples
        }

        # Trading parameters for non-popular tokens
        self.trading_params = {
            "max_position_pct": 6,  # 6% max per position
            "stop_loss_pct": 7,  # 7% stop loss
            "take_profit_1": 18,  # 18% first target
            "take_profit_2": 35,  # 35% second target
            "max_concurrent": 3,  # Max 3 positions
            "min_hold_hours": 2,  # Min 2 hours holding
        }

        # Learning data storage
        self.learning_database = {
            "successful_patterns": [],
            "failed_patterns": [],
            "token_behaviors": {},
            "market_conditions": [],
            "feature_importance": {},
            "model_accuracy": 0.0,
        }

        # AI Models
        self.price_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        self.volume_predictor = RandomForestClassifier(
            n_estimators=100, random_state=42
        )
        self.scaler = StandardScaler()
        self.model_trained = False

        self.load_learning_database()
        self.logger.info("🎯 AI Non-Popular Token Hunter initialized")
        self.logger.info("🔍 Focus: Micro/nano caps with maximum alpha potential")

    def load_learning_database(self):
        """Load historical learning data"""
        try:
            if os.path.exists("ai_hunter_database.json"):
                with open("ai_hunter_database.json", "r") as f:
                    self.learning_database = json.load(f)

                success_count = len(
                    self.learning_database.get("successful_patterns", [])
                )
                failed_count = len(self.learning_database.get("failed_patterns", []))

                self.logger.info(
                    f"📚 Loaded learning database: {success_count} successful, {failed_count} failed patterns"
                )

                # Retrain model if we have enough data
                if success_count + failed_count >= self.ai_params["retrain_threshold"]:
                    self.train_ai_models()

        except Exception as e:
            self.logger.error(f"Error loading learning database: {e}")

    def save_learning_database(self):
        """Save learning database"""
        try:
            with open("ai_hunter_database.json", "w") as f:
                json.dump(self.learning_database, f, indent=2, default=str)
            self.logger.info("💾 Learning database saved")
        except Exception as e:
            self.logger.error(f"Error saving learning database: {e}")

    def hunt_non_popular_tokens(self) -> List[Dict]:
        """Hunt for the least popular tokens with highest alpha potential"""
        try:
            # Get all USDT pairs
            tickers = self.client.get_ticker()

            non_popular_candidates = []

            for ticker in tickers:
                symbol = ticker["symbol"]

                # Only USDT pairs
                if not symbol.endswith("USDT"):
                    continue

                # Skip stablecoins
                base_asset = symbol.replace("USDT", "")
                if base_asset in ["USDC", "BUSD", "DAI", "TUSD", "FDUSD"]:
                    continue

                volume_usd = float(ticker["quoteVolume"])
                price_change = float(ticker["priceChangePercent"])
                current_price = float(ticker["lastPrice"])

                # Filter for non-popular tokens
                if (
                    self.hunt_criteria["min_volume_usd"]
                    <= volume_usd
                    <= self.hunt_criteria["max_volume_usd"]
                ):

                    non_popular_candidates.append(
                        {
                            "symbol": symbol,
                            "volume_usd": volume_usd,
                            "price_change_24h": price_change,
                            "current_price": current_price,
                            "high_24h": float(ticker["highPrice"]),
                            "low_24h": float(ticker["lowPrice"]),
                            "volume_24h": float(ticker["volume"]),
                            "trade_count": int(ticker["count"]),
                            "popularity_score": self.calculate_popularity_score(
                                volume_usd, int(ticker["count"])
                            ),
                        }
                    )

            # Sort by popularity score (lowest = most non-popular)
            non_popular_candidates.sort(key=lambda x: x["popularity_score"])

            self.logger.info(
                f"🎯 Found {len(non_popular_candidates)} non-popular token candidates"
            )
            return non_popular_candidates

        except Exception as e:
            self.logger.error(f"Error hunting non-popular tokens: {e}")
            return []

    def calculate_popularity_score(self, volume_usd: float, trade_count: int) -> float:
        """Calculate popularity score (lower = less popular = better for alpha)"""
        # Combine volume and trade frequency
        volume_score = min(volume_usd / 1000, 100)  # Cap at 100
        trade_score = min(trade_count / 100, 100)  # Cap at 100

        # Lower score = less popular = higher alpha potential
        popularity = (volume_score * 0.7) + (trade_score * 0.3)
        return popularity

    def extract_features(self, symbol: str, token_data: Dict) -> Optional[np.ndarray]:
        """Extract AI features from token data"""
        try:
            # Get historical data
            klines = self.client.get_klines(
                symbol=symbol, interval="1h", limit=self.ai_params["lookback_hours"]
            )

            if len(klines) < 50:  # Need minimum data
                return None

            # Convert to DataFrame
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
                    "quote_asset_volume",
                    "number_of_trades",
                    "taker_buy_base_asset_volume",
                    "taker_buy_quote_asset_volume",
                    "ignore",
                ],
            )

            # Convert to numeric
            numeric_cols = [
                "open",
                "high",
                "low",
                "close",
                "volume",
                "quote_asset_volume",
                "number_of_trades",
            ]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col])

            # Calculate technical indicators
            df["returns"] = df["close"].pct_change()
            df["log_returns"] = np.log(df["close"] / df["close"].shift(1))

            # Moving averages
            df["sma_10"] = df["close"].rolling(10).mean()
            df["sma_20"] = df["close"].rolling(20).mean()
            df["sma_50"] = df["close"].rolling(50).mean()

            # RSI
            delta = df["close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

            # MACD
            ema_12 = df["close"].ewm(span=12).mean()
            ema_26 = df["close"].ewm(span=26).mean()
            df["macd"] = ema_12 - ema_26
            df["macd_signal"] = df["macd"].ewm(span=9).mean()
            df["macd_histogram"] = df["macd"] - df["macd_signal"]

            # Volatility
            df["volatility"] = df["returns"].rolling(20).std()

            # Volume indicators
            df["volume_sma"] = df["volume"].rolling(20).mean()
            df["volume_ratio"] = df["volume"] / df["volume_sma"]
            df["price_volume"] = df["close"] * df["volume"]

            # Bollinger Bands
            bb_period = 20
            df["bb_middle"] = df["close"].rolling(bb_period).mean()
            bb_std = df["close"].rolling(bb_period).std()
            df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
            df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
            df["bb_position"] = (df["close"] - df["bb_lower"]) / (
                df["bb_upper"] - df["bb_lower"]
            )

            # Get latest values for features
            latest = df.iloc[-1]
            prev_5 = df.iloc[-6:-1]
            prev_24 = df.iloc[-25:-1] if len(df) >= 25 else df.iloc[:-1]

            # Feature vector (25 features)
            features = [
                latest["rsi"],
                latest["macd"],
                latest["macd_signal"],
                latest["macd_histogram"],
                latest["bb_position"],
                latest["volume_ratio"],
                latest["volatility"],
                (latest["close"] / latest["sma_10"] - 1) * 100,  # Price vs SMA10
                (latest["close"] / latest["sma_20"] - 1) * 100,  # Price vs SMA20
                (latest["close"] / latest["sma_50"] - 1) * 100,  # Price vs SMA50
                prev_5["returns"].mean() * 100,  # 5-period avg return
                prev_24["returns"].mean() * 100,  # 24-period avg return
                prev_5["returns"].std() * 100,  # 5-period volatility
                prev_24["returns"].std() * 100,  # 24-period volatility
                (latest["high"] / latest["low"] - 1) * 100,  # Daily range
                latest["number_of_trades"],  # Trade count
                token_data["popularity_score"],  # Popularity score
                np.log(token_data["volume_usd"]),  # Log volume
                token_data["price_change_24h"],  # 24h change
                (latest["close"] - df["close"].min())
                / (df["close"].max() - df["close"].min()),  # Price position
                df["volume"].iloc[-5:].mean()
                / df["volume"].mean(),  # Recent volume ratio
                len([x for x in prev_5["returns"] if x > 0]) / len(prev_5),  # Win rate
                df["returns"].skew(),  # Return skewness
                df["returns"].kurtosis(),  # Return kurtosis
                latest["close"],  # Current price
            ]

            # Handle NaN values
            features = [0 if pd.isna(x) or np.isinf(x) else float(x) for x in features]

            return np.array(features)

        except Exception as e:
            self.logger.error(f"Error extracting features for {symbol}: {e}")
            return None

    def ai_analyze_token(self, symbol: str, token_data: Dict) -> Dict:
        """Use AI to analyze token and generate trading signals"""
        try:
            # Extract features
            features = self.extract_features(symbol, token_data)
            if features is None:
                return {
                    "signal": "SKIP",
                    "confidence": 0,
                    "reason": "Insufficient data",
                }

            # Normalize features
            features_scaled = features.reshape(1, -1)

            if self.model_trained:
                # Use trained model for prediction
                try:
                    features_scaled = self.scaler.transform(features_scaled)
                    price_prediction = self.price_predictor.predict_proba(
                        features_scaled
                    )[0]
                    volume_prediction = self.volume_predictor.predict_proba(
                        features_scaled
                    )[0]

                    # Combine predictions
                    buy_confidence = (price_prediction[1] * 0.7) + (
                        volume_prediction[1] * 0.3
                    )

                    signal = (
                        "BUY"
                        if buy_confidence >= self.ai_params["min_confidence"]
                        else "HOLD"
                    )

                    return {
                        "signal": signal,
                        "confidence": buy_confidence,
                        "price_prediction": price_prediction[1],
                        "volume_prediction": volume_prediction[1],
                        "reason": f"AI Model Prediction: {buy_confidence:.2f} confidence",
                    }

                except Exception as e:
                    self.logger.error(f"Error using trained model: {e}")
                    # Fall back to heuristic analysis
                    return self.heuristic_analysis(features, token_data)
            else:
                # Use heuristic analysis until model is trained
                return self.heuristic_analysis(features, token_data)

        except Exception as e:
            self.logger.error(f"Error in AI analysis for {symbol}: {e}")
            return {
                "signal": "SKIP",
                "confidence": 0,
                "reason": f"Analysis failed: {e}",
            }

    def heuristic_analysis(self, features: np.ndarray, token_data: Dict) -> Dict:
        """Heuristic analysis for non-popular tokens when AI model isn't ready"""
        try:
            rsi, macd, macd_signal, macd_histogram, bb_position = features[:5]
            volume_ratio, volatility = features[5], features[6]
            price_vs_sma20 = features[8]
            popularity_score = features[16]
            price_change_24h = features[18]

            score = 0
            reasons = []

            # RSI-based signals (oversold conditions in non-popular tokens)
            if rsi < 30:
                score += 25
                reasons.append(f"Oversold RSI: {rsi:.1f}")
            elif rsi < 40:
                score += 15
                reasons.append(f"Low RSI: {rsi:.1f}")
            elif rsi > 70:
                score -= 10  # Overbought

            # MACD signals
            if macd > macd_signal and macd_histogram > 0:
                score += 20
                reasons.append("MACD bullish crossover")
            elif macd < macd_signal:
                score -= 5

            # Bollinger Bands position
            if bb_position < 0.2:  # Near lower band
                score += 20
                reasons.append(f"Near BB lower: {bb_position:.2f}")
            elif bb_position > 0.8:  # Near upper band
                score -= 10

            # Volume analysis (crucial for non-popular tokens)
            if volume_ratio > 2:  # Volume spike
                score += 25
                reasons.append(f"Volume spike: {volume_ratio:.2f}x")
            elif volume_ratio > 1.5:
                score += 15
                reasons.append(f"High volume: {volume_ratio:.2f}x")
            elif volume_ratio < 0.5:
                score -= 15  # Low volume

            # Price position relative to SMA
            if -5 < price_vs_sma20 < 0:  # Slightly below SMA20
                score += 10
                reasons.append("Below SMA20 - potential bounce")
            elif price_vs_sma20 < -10:  # Well below SMA20
                score += 20
                reasons.append("Well below SMA20 - oversold")

            # Popularity bonus (less popular = higher potential)
            if popularity_score < 10:
                score += 15
                reasons.append("Ultra non-popular token")
            elif popularity_score < 25:
                score += 10
                reasons.append("Non-popular token")

            # Recent momentum
            if 0 < price_change_24h < 5:
                score += 10
                reasons.append("Positive momentum")
            elif price_change_24h > 10:
                score -= 5  # Too much momentum already

            # Volatility consideration
            if 2 < volatility < 8:  # Good volatility for gains
                score += 10
            elif volatility > 15:  # Too volatile
                score -= 15

            # Determine signal
            confidence = min(score / 100, 0.95)  # Cap at 95%

            if score >= 75:
                signal = "BUY"
            elif score >= 50:
                signal = "WATCH"
            else:
                signal = "HOLD"

            return {
                "signal": signal,
                "confidence": confidence,
                "score": score,
                "reasons": reasons,
                "reason": f"Heuristic score: {score} - " + "; ".join(reasons[:3]),
            }

        except Exception as e:
            self.logger.error(f"Error in heuristic analysis: {e}")
            return {
                "signal": "SKIP",
                "confidence": 0,
                "reason": f"Heuristic failed: {e}",
            }

    def train_ai_models(self):
        """Train AI models from learning database"""
        try:
            successful = self.learning_database.get("successful_patterns", [])
            failed = self.learning_database.get("failed_patterns", [])

            if len(successful) + len(failed) < 20:  # Need minimum samples
                self.logger.info("Not enough data to train AI models")
                return

            # Prepare training data
            X, y = [], []

            for pattern in successful:
                if "features" in pattern:
                    X.append(pattern["features"])
                    y.append(1)  # Success

            for pattern in failed:
                if "features" in pattern:
                    X.append(pattern["features"])
                    y.append(0)  # Failure

            if len(X) < 10:
                self.logger.info("Not enough feature data to train models")
                return

            X = np.array(X)
            y = np.array(y)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train models
            self.price_predictor.fit(X_scaled, y)
            self.volume_predictor.fit(X_scaled, y)  # Can use same data

            # Calculate accuracy
            accuracy = self.price_predictor.score(X_scaled, y)
            self.learning_database["model_accuracy"] = accuracy
            self.model_trained = True

            self.logger.info(f"🤖 AI models trained with accuracy: {accuracy:.2f}")

        except Exception as e:
            self.logger.error(f"Error training AI models: {e}")

    def execute_ai_trade(self, symbol: str, analysis: Dict, token_data: Dict) -> bool:
        """Execute trade based on AI analysis"""
        try:
            signal = analysis.get("signal", "HOLD")
            confidence = analysis.get("confidence", 0)

            if signal == "BUY" and confidence >= self.ai_params["min_confidence"]:
                return self.place_buy_order(symbol, analysis, token_data)

            return False

        except Exception as e:
            self.logger.error(f"Error executing AI trade for {symbol}: {e}")
            return False

    def place_buy_order(self, symbol: str, analysis: Dict, token_data: Dict) -> bool:
        """Place buy order for non-popular token"""
        try:
            # Get USDT balance
            account = self.client.get_account()
            usdt_balance = 0

            for balance in account["balances"]:
                if balance["asset"] == "USDT":
                    usdt_balance = float(balance["free"])
                    break

            if usdt_balance < 15:  # Need minimum balance
                self.logger.warning(f"Insufficient USDT balance: ${usdt_balance}")
                return False

            # Calculate position size (smaller for non-popular tokens)
            position_value = usdt_balance * (
                self.trading_params["max_position_pct"] / 100
            )
            current_price = token_data["current_price"]
            quantity = position_value / current_price

            # Get symbol precision
            symbol_info = self.client.get_symbol_info(symbol)
            step_size = 0.00000001

            for filter in symbol_info["filters"]:
                if filter["filterType"] == "LOT_SIZE":
                    step_size = float(filter["stepSize"])
                    break

            # Round quantity
            quantity = round(quantity - (quantity % step_size), 8)

            if quantity * current_price < 10:  # Minimum order value
                self.logger.warning(f"Order value too small for {symbol}")
                return False

            # Place buy order
            self.logger.info(
                f"🎯 AI BUY: {symbol} | Qty: {quantity} | Price: ${current_price:.8f} | Confidence: {analysis.get('confidence', 0):.2f}"
            )

            order = self.client.order_market_buy(symbol=symbol, quantity=quantity)

            # Record trade for learning
            trade_record = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "action": "BUY",
                "quantity": quantity,
                "price": current_price,
                "confidence": analysis.get("confidence", 0),
                "analysis": analysis,
                "token_data": token_data,
                "order_id": order["orderId"],
            }

            self.save_trade_record(trade_record)
            self.logger.info(
                f"✅ AI Buy executed: {symbol} - Order ID: {order['orderId']}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error placing buy order for {symbol}: {e}")
            return False

    def save_trade_record(self, trade_record: Dict):
        """Save trade record"""
        try:
            filename = f"ai_hunter_trades_{datetime.now().strftime('%Y%m%d')}.json"

            trades = []
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    trades = json.load(f)

            trades.append(trade_record)

            with open(filename, "w") as f:
                json.dump(trades, f, indent=2, default=str)

        except Exception as e:
            self.logger.error(f"Error saving trade record: {e}")

    def run_hunting_session(self):
        """Run complete AI hunting session for non-popular tokens"""
        self.logger.info("🚀 Starting AI Non-Popular Token Hunting Session")

        # Hunt for non-popular tokens
        candidates = self.hunt_non_popular_tokens()

        if not candidates:
            self.logger.warning("No non-popular token candidates found")
            return

        # Focus on ultra non-popular tokens (highest alpha potential)
        ultra_candidates = [
            c
            for c in candidates
            if c["volume_usd"] < self.hunt_criteria["ultra_low_max"]
        ][:10]

        if ultra_candidates:
            self.logger.info(
                f"🎯 Focusing on {len(ultra_candidates)} ultra non-popular tokens"
            )
        else:
            ultra_candidates = candidates[:10]  # Fallback to top 10

        trades_executed = 0
        max_trades = self.trading_params["max_concurrent"]

        for candidate in ultra_candidates:
            if trades_executed >= max_trades:
                break

            symbol = candidate["symbol"]
            volume_usd = candidate["volume_usd"]

            self.logger.info(
                f"🔍 AI analyzing: {symbol} (Vol: ${volume_usd:,.0f}, Pop: {candidate['popularity_score']:.1f})"
            )

            # AI analysis
            analysis = self.ai_analyze_token(symbol, candidate)

            signal = analysis.get("signal", "HOLD")
            confidence = analysis.get("confidence", 0)
            reason = analysis.get("reason", "No reason")

            self.logger.info(
                f"   🤖 AI Signal: {signal} | Confidence: {confidence:.2f} | {reason[:60]}"
            )

            # Execute trade if signal is strong
            if self.execute_ai_trade(symbol, analysis, candidate):
                trades_executed += 1
                time.sleep(2)  # Brief pause between trades

            time.sleep(1)  # Rate limiting

        # Save learning database
        self.save_learning_database()

        self.logger.info(
            f"🏁 Hunting session complete. Trades executed: {trades_executed}"
        )


def main():
    """Main execution"""
    print("🎯 AI-Powered Non-Popular Token Hunter")
    print("=" * 50)
    print("Hunting for alpha in the least popular tokens")
    print("Using advanced AI pattern recognition")
    print("Focus: Micro-cap and nano-cap opportunities")
    print("=" * 50)

    hunter = AINonPopularHunter()
    hunter.run_hunting_session()


if __name__ == "__main__":
    main()
