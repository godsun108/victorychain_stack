#!/usr/bin/env python3
"""
Quantum-Level Data-Driven Market Analysis System
Advanced statistical models, machine learning, and quantitative finance
"""

import os
import json
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr, jarque_bera, shapiro, kurtosis, skew
from scipy.optimize import minimize
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA, FastICA
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.neighbors import LocalOutlierFactor
from binance.client import Client
from dotenv import load_dotenv

warnings.filterwarnings("ignore")


class QuantumDataAnalyst:
    def __init__(self):
        load_dotenv()

        # Initialize Binance client
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        print("🚀 Quantum Data-Driven Analyst initialized")
        print("⚛️  Loading advanced statistical models and ML algorithms...")
        print("📡 Initializing quantitative finance indicators...")

    def get_comprehensive_market_data(
        self, symbols: List[str], lookback_hours: int = 168
    ) -> Dict:
        """Get comprehensive market data with multiple timeframes"""

        print(f"📊 Gathering comprehensive market data for {len(symbols)} symbols...")
        print(f"🕐 Lookback period: {lookback_hours} hours")

        market_data = {}
        failed_symbols = []

        for i, symbol in enumerate(symbols):
            try:
                # Get ticker data
                ticker = self.client.get_ticker(symbol=symbol)

                # Get klines for multiple timeframes
                klines_1h = self.client.get_klines(
                    symbol=symbol, interval="1h", limit=lookback_hours
                )
                klines_4h = self.client.get_klines(
                    symbol=symbol, interval="4h", limit=lookback_hours // 4
                )
                klines_1d = self.client.get_klines(
                    symbol=symbol, interval="1d", limit=lookback_hours // 24
                )

                # Get order book depth
                depth = self.client.get_order_book(symbol=symbol, limit=100)

                # Get recent trades
                trades = self.client.get_recent_trades(symbol=symbol, limit=100)

                if klines_1h and klines_4h and klines_1d:
                    market_data[symbol] = {
                        "ticker": ticker,
                        "klines": {
                            "1h": self.parse_klines(klines_1h),
                            "4h": self.parse_klines(klines_4h),
                            "1d": self.parse_klines(klines_1d),
                        },
                        "depth": depth,
                        "trades": trades,
                    }

                # Progress indicator
                if (i + 1) % 5 == 0:
                    print(f"📈 Processed {i + 1}/{len(symbols)} symbols...")

                time.sleep(0.2)  # Rate limiting

            except Exception as e:
                print(f"❌ Failed to get data for {symbol}: {str(e)}")
                failed_symbols.append(symbol)
                continue

        print(f"✅ Successfully gathered data for {len(market_data)} symbols")
        if failed_symbols:
            print(
                f"⚠️  Failed to get data for {len(failed_symbols)} symbols: {failed_symbols}"
            )

        return market_data

    def parse_klines(self, klines: List) -> pd.DataFrame:
        """Parse klines data into DataFrame with comprehensive columns"""

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

        # Convert to proper types
        numeric_cols = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "quote_volume",
            "taker_buy_volume",
            "taker_buy_quote_volume",
            "count",
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        return df

    def calculate_advanced_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate advanced technical and statistical indicators"""

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # Basic price indicators
        df["returns"] = close.pct_change()
        df["log_returns"] = np.log(close / close.shift(1))
        df["price_change"] = close.diff()

        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f"sma_{period}"] = close.rolling(window=period).mean()
            df[f"ema_{period}"] = close.ewm(span=period).mean()

        # MACD family
        df["ema_12"] = close.ewm(span=12).mean()
        df["ema_26"] = close.ewm(span=26).mean()
        df["macd"] = df["ema_12"] - df["ema_26"]
        df["macd_signal"] = df["macd"].ewm(span=9).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))

        # Bollinger Bands
        df["bb_middle"] = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        df["bb_upper"] = df["bb_middle"] + (bb_std * 2)
        df["bb_lower"] = df["bb_middle"] - (bb_std * 2)
        df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
        df["bb_position"] = (close - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])

        # Stochastic Oscillator
        lowest_low = low.rolling(window=14).min()
        highest_high = high.rolling(window=14).max()
        df["stoch_k"] = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        df["stoch_d"] = df["stoch_k"].rolling(window=3).mean()

        # ATR and volatility
        df["tr1"] = high - low
        df["tr2"] = abs(high - close.shift())
        df["tr3"] = abs(low - close.shift())
        df["true_range"] = df[["tr1", "tr2", "tr3"]].max(axis=1)
        df["atr"] = df["true_range"].rolling(window=14).mean()
        df["volatility"] = close.rolling(window=20).std()

        # Volume indicators
        df["volume_sma"] = volume.rolling(window=20).mean()
        df["volume_ratio"] = volume / df["volume_sma"]
        df["vwap"] = (close * volume).cumsum() / volume.cumsum()

        # Advanced momentum indicators
        df["momentum"] = close / close.shift(10) - 1
        df["rate_of_change"] = (close - close.shift(10)) / close.shift(10) * 100
        df["williams_r"] = -100 * (highest_high - close) / (highest_high - lowest_low)

        # Statistical measures (rolling)
        df["skewness"] = df["returns"].rolling(window=20).skew()
        df["kurtosis"] = df["returns"].rolling(window=20).kurt()
        df["sharpe_ratio"] = (
            df["returns"].rolling(window=20).mean()
            / df["returns"].rolling(window=20).std()
        )

        return df

    def perform_statistical_analysis(self, data: Dict) -> Dict:
        """Perform comprehensive statistical analysis"""

        print("🔬 Performing comprehensive statistical analysis...")

        statistical_results = {}

        for symbol, symbol_data in data.items():
            try:
                df_1h = symbol_data["klines"]["1h"]
                df_4h = symbol_data["klines"]["4h"]
                df_1d = symbol_data["klines"]["1d"]

                # Calculate indicators for each timeframe
                df_1h = self.calculate_advanced_indicators(df_1h)
                df_4h = self.calculate_advanced_indicators(df_4h)
                df_1d = self.calculate_advanced_indicators(df_1d)

                # Statistical tests on returns
                returns_1h = df_1h["returns"].dropna()
                returns_4h = df_4h["returns"].dropna()
                returns_1d = df_1d["returns"].dropna()

                # Normality tests
                jb_stat_1h, jb_p_1h = jarque_bera(returns_1h)
                sw_stat_1h, sw_p_1h = shapiro(
                    returns_1h[:5000] if len(returns_1h) > 5000 else returns_1h
                )

                # Distribution statistics
                mean_return_1h = returns_1h.mean()
                std_return_1h = returns_1h.std()
                skewness_1h = skew(returns_1h)
                kurtosis_1h = kurtosis(returns_1h)

                # Price momentum and trends
                current_price = float(symbol_data["ticker"]["lastPrice"])
                price_change_24h = float(symbol_data["ticker"]["priceChangePercent"])

                # Calculate multi-timeframe momentum
                momentum_1h = self.calculate_momentum_score(df_1h)
                momentum_4h = self.calculate_momentum_score(df_4h)
                momentum_1d = self.calculate_momentum_score(df_1d)

                # Volatility analysis
                volatility_1h = (
                    df_1h["volatility"].iloc[-1]
                    if not df_1h["volatility"].isna().iloc[-1]
                    else 0
                )
                volatility_4h = (
                    df_4h["volatility"].iloc[-1]
                    if not df_4h["volatility"].isna().iloc[-1]
                    else 0
                )

                # Volume analysis
                volume_trend = self.analyze_volume_trend(df_1h)

                # Risk metrics
                var_95 = np.percentile(returns_1h, 5)  # Value at Risk 95%
                max_drawdown = self.calculate_max_drawdown(df_1h["close"])

                statistical_results[symbol] = {
                    "price_data": {
                        "current_price": current_price,
                        "price_change_24h": price_change_24h,
                        "volatility_1h": volatility_1h,
                        "volatility_4h": volatility_4h,
                    },
                    "returns_analysis": {
                        "mean_return_1h": mean_return_1h,
                        "std_return_1h": std_return_1h,
                        "skewness": skewness_1h,
                        "kurtosis": kurtosis_1h,
                        "var_95": var_95,
                        "max_drawdown": max_drawdown,
                    },
                    "normality_tests": {
                        "jarque_bera_stat": jb_stat_1h,
                        "jarque_bera_p": jb_p_1h,
                        "shapiro_stat": sw_stat_1h,
                        "shapiro_p": sw_p_1h,
                        "is_normal": sw_p_1h > 0.05,
                    },
                    "momentum_analysis": {
                        "momentum_1h": momentum_1h,
                        "momentum_4h": momentum_4h,
                        "momentum_1d": momentum_1d,
                        "combined_momentum": (momentum_1h + momentum_4h + momentum_1d)
                        / 3,
                    },
                    "volume_analysis": volume_trend,
                    "technical_indicators": {
                        "rsi_1h": (
                            df_1h["rsi"].iloc[-1]
                            if not df_1h["rsi"].isna().iloc[-1]
                            else 50
                        ),
                        "macd_1h": (
                            df_1h["macd"].iloc[-1]
                            if not df_1h["macd"].isna().iloc[-1]
                            else 0
                        ),
                        "bb_position_1h": (
                            df_1h["bb_position"].iloc[-1]
                            if not df_1h["bb_position"].isna().iloc[-1]
                            else 0.5
                        ),
                        "stoch_k_1h": (
                            df_1h["stoch_k"].iloc[-1]
                            if not df_1h["stoch_k"].isna().iloc[-1]
                            else 50
                        ),
                    },
                }

            except Exception as e:
                print(f"❌ Statistical analysis failed for {symbol}: {str(e)}")
                continue

        print(
            f"✅ Statistical analysis completed for {len(statistical_results)} symbols"
        )
        return statistical_results

    def calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """Calculate comprehensive momentum score"""

        try:
            # Price momentum
            price_momentum = (
                df["momentum"].iloc[-1] if not df["momentum"].isna().iloc[-1] else 0
            )

            # RSI momentum (converted to -1 to 1 scale)
            rsi = df["rsi"].iloc[-1] if not df["rsi"].isna().iloc[-1] else 50
            rsi_momentum = (rsi - 50) / 50

            # MACD momentum
            macd = df["macd"].iloc[-1] if not df["macd"].isna().iloc[-1] else 0
            macd_signal = (
                df["macd_signal"].iloc[-1]
                if not df["macd_signal"].isna().iloc[-1]
                else 0
            )
            macd_momentum = 1 if macd > macd_signal else -1

            # Moving average momentum
            sma_20 = (
                df["sma_20"].iloc[-1]
                if not df["sma_20"].isna().iloc[-1]
                else df["close"].iloc[-1]
            )
            ma_momentum = (df["close"].iloc[-1] - sma_20) / sma_20

            # Combine momentum factors
            momentum_score = (
                price_momentum * 0.4
                + rsi_momentum * 0.2
                + macd_momentum * 0.2
                + ma_momentum * 0.2
            )

            return float(momentum_score)

        except:
            return 0.0

    def analyze_volume_trend(self, df: pd.DataFrame) -> Dict:
        """Analyze volume trends and patterns"""

        try:
            volume = df["volume"]
            volume_sma = df["volume_sma"]

            # Current volume vs average
            current_volume_ratio = (
                volume.iloc[-1] / volume_sma.iloc[-1]
                if not volume_sma.isna().iloc[-1]
                else 1
            )

            # Volume trend (increasing/decreasing)
            volume_trend = np.polyfit(range(len(volume[-10:])), volume[-10:], 1)[0]

            # Volume spikes
            volume_spikes = (volume > volume_sma * 2).sum()

            return {
                "current_volume_ratio": float(current_volume_ratio),
                "volume_trend": float(volume_trend),
                "volume_spikes_count": int(volume_spikes),
                "volume_pattern": "increasing" if volume_trend > 0 else "decreasing",
            }

        except:
            return {
                "current_volume_ratio": 1.0,
                "volume_trend": 0.0,
                "volume_spikes_count": 0,
                "volume_pattern": "stable",
            }

    def calculate_max_drawdown(self, prices: pd.Series) -> float:
        """Calculate maximum drawdown"""

        try:
            cumulative = (1 + prices.pct_change()).cumprod()
            running_max = cumulative.cummax()
            drawdown = (cumulative - running_max) / running_max
            return float(drawdown.min())
        except:
            return 0.0

    def perform_machine_learning_analysis(self, statistical_results: Dict) -> Dict:
        """Perform machine learning analysis on the data"""

        print("🤖 Performing machine learning analysis...")

        # Prepare data for ML
        ml_data = []
        symbols = []

        for symbol, data in statistical_results.items():
            try:
                feature_vector = [
                    data["price_data"]["price_change_24h"],
                    data["price_data"]["volatility_1h"],
                    data["returns_analysis"]["mean_return_1h"],
                    data["returns_analysis"]["std_return_1h"],
                    data["returns_analysis"]["skewness"],
                    data["returns_analysis"]["kurtosis"],
                    data["momentum_analysis"]["combined_momentum"],
                    data["volume_analysis"]["current_volume_ratio"],
                    data["technical_indicators"]["rsi_1h"],
                    data["technical_indicators"]["macd_1h"],
                    data["technical_indicators"]["bb_position_1h"],
                ]

                # Only include if all features are valid
                if not any(pd.isna(feature_vector)) and not any(
                    np.isinf(feature_vector)
                ):
                    ml_data.append(feature_vector)
                    symbols.append(symbol)

            except Exception as e:
                continue

        if len(ml_data) < 5:
            print("❌ Insufficient data for ML analysis")
            return {}

        ml_data = np.array(ml_data)

        # Standardize features
        scaler = StandardScaler()
        ml_data_scaled = scaler.fit_transform(ml_data)

        # Clustering analysis
        kmeans = KMeans(n_clusters=min(5, len(ml_data)), random_state=42)
        clusters = kmeans.fit_predict(ml_data_scaled)

        # PCA analysis
        pca = PCA(n_components=min(3, ml_data_scaled.shape[1]))
        pca_components = pca.fit_transform(ml_data_scaled)

        # Outlier detection
        lof = LocalOutlierFactor(n_neighbors=min(10, len(ml_data)))
        outlier_scores = lof.fit_predict(ml_data_scaled)

        # Prepare results
        ml_results = {}

        for i, symbol in enumerate(symbols):
            ml_results[symbol] = {
                "cluster": int(clusters[i]),
                "pca_components": pca_components[i].tolist(),
                "is_outlier": int(outlier_scores[i]) == -1,
                "outlier_score": float(lof.negative_outlier_factor_[i]),
            }

        # Cluster analysis
        cluster_analysis = {}
        for cluster_id in range(kmeans.n_clusters):
            cluster_symbols = [
                symbols[i] for i in range(len(symbols)) if clusters[i] == cluster_id
            ]
            cluster_center = kmeans.cluster_centers_[cluster_id]

            cluster_analysis[f"cluster_{cluster_id}"] = {
                "symbols": cluster_symbols,
                "size": len(cluster_symbols),
                "characteristics": {
                    "avg_price_change": float(cluster_center[0]),
                    "avg_volatility": float(cluster_center[1]),
                    "avg_momentum": float(cluster_center[6]),
                    "avg_volume_ratio": float(cluster_center[7]),
                },
            }

        print(f"✅ ML analysis completed for {len(ml_results)} symbols")
        print(
            f"📊 Identified {kmeans.n_clusters} clusters and {sum(1 for x in outlier_scores if x == -1)} outliers"
        )

        return {
            "individual_results": ml_results,
            "cluster_analysis": cluster_analysis,
            "pca_explained_variance": pca.explained_variance_ratio_.tolist(),
            "total_outliers": sum(1 for x in outlier_scores if x == -1),
        }

    def generate_predictive_models(self, statistical_results: Dict) -> Dict:
        """Generate predictive models for price movements"""

        print("🔮 Generating predictive models...")

        # Prepare data for prediction models
        features = []
        targets = []
        symbols = []

        for symbol, data in statistical_results.items():
            try:
                feature_vector = [
                    data["returns_analysis"]["mean_return_1h"],
                    data["returns_analysis"]["std_return_1h"],
                    data["momentum_analysis"]["combined_momentum"],
                    data["volume_analysis"]["current_volume_ratio"],
                    data["technical_indicators"]["rsi_1h"],
                    data["technical_indicators"]["macd_1h"],
                    data["technical_indicators"]["bb_position_1h"],
                ]

                target = data["price_data"]["price_change_24h"]

                if not any(pd.isna(feature_vector)) and not pd.isna(target):
                    features.append(feature_vector)
                    targets.append(target)
                    symbols.append(symbol)

            except:
                continue

        if len(features) < 10:
            print("❌ Insufficient data for predictive modeling")
            return {}

        features = np.array(features)
        targets = np.array(targets)

        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)

        # Train multiple models
        models = {
            "linear_regression": LinearRegression(),
            "ridge_regression": Ridge(alpha=1.0),
            "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=100, random_state=42
            ),
        }

        model_results = {}

        for model_name, model in models.items():
            try:
                # Cross-validation
                cv_scores = cross_val_score(
                    model, features_scaled, targets, cv=5, scoring="r2"
                )

                # Fit the model
                model.fit(features_scaled, targets)

                # Predictions
                predictions = model.predict(features_scaled)

                # Model performance
                r2 = r2_score(targets, predictions)
                mse = mean_squared_error(targets, predictions)

                model_results[model_name] = {
                    "cv_scores": cv_scores.tolist(),
                    "cv_mean": float(cv_scores.mean()),
                    "cv_std": float(cv_scores.std()),
                    "r2_score": float(r2),
                    "mse": float(mse),
                    "predictions": predictions.tolist(),
                }

            except Exception as e:
                print(f"❌ Model {model_name} failed: {str(e)}")
                continue

        # Generate predictions for each symbol
        symbol_predictions = {}

        for i, symbol in enumerate(symbols):
            symbol_predictions[symbol] = {
                "actual_change": float(targets[i]),
                "predictions": {
                    model_name: float(results["predictions"][i])
                    for model_name, results in model_results.items()
                    if "predictions" in results
                },
            }

        print(f"✅ Predictive models generated for {len(symbol_predictions)} symbols")

        return {
            "model_performance": model_results,
            "symbol_predictions": symbol_predictions,
            "feature_importance": self.get_feature_importance(
                models.get("random_forest")
            ),
        }

    def get_feature_importance(self, rf_model) -> Dict:
        """Get feature importance from Random Forest model"""

        if rf_model is None:
            return {}

        feature_names = [
            "mean_return_1h",
            "std_return_1h",
            "combined_momentum",
            "volume_ratio",
            "rsi",
            "macd",
            "bb_position",
        ]

        importances = rf_model.feature_importances_

        return {
            feature_names[i]: float(importances[i]) for i in range(len(feature_names))
        }

    def generate_quantum_insights(
        self, statistical_results: Dict, ml_results: Dict, predictive_results: Dict
    ) -> Dict:
        """Generate quantum-level insights and recommendations"""

        print("⚛️  Generating quantum-level insights...")

        insights = {
            "market_regime_analysis": self.analyze_market_regime(statistical_results),
            "opportunity_ranking": self.rank_opportunities(
                statistical_results, ml_results, predictive_results
            ),
            "risk_assessment": self.assess_risks(statistical_results),
            "portfolio_recommendations": self.generate_portfolio_recommendations(
                statistical_results, ml_results
            ),
            "trading_signals": self.generate_trading_signals(
                statistical_results, predictive_results
            ),
            "market_microstructure": self.analyze_market_microstructure(
                statistical_results
            ),
            "regime_predictions": self.predict_market_regime_changes(
                statistical_results
            ),
        }

        return insights

    def analyze_market_regime(self, statistical_results: Dict) -> Dict:
        """Analyze current market regime"""

        # Calculate market-wide metrics
        price_changes = [
            data["price_data"]["price_change_24h"]
            for data in statistical_results.values()
        ]
        volatilities = [
            data["price_data"]["volatility_1h"] for data in statistical_results.values()
        ]
        momentums = [
            data["momentum_analysis"]["combined_momentum"]
            for data in statistical_results.values()
        ]

        avg_price_change = np.mean(price_changes)
        avg_volatility = np.mean(volatilities)
        avg_momentum = np.mean(momentums)

        # Determine regime
        if avg_price_change > 2 and avg_momentum > 0.1:
            regime = "BULL_MARKET"
            confidence = min(abs(avg_price_change) / 5, 1.0)
        elif avg_price_change < -2 and avg_momentum < -0.1:
            regime = "BEAR_MARKET"
            confidence = min(abs(avg_price_change) / 5, 1.0)
        elif avg_volatility > 0.05:
            regime = "HIGH_VOLATILITY"
            confidence = min(avg_volatility / 0.1, 1.0)
        else:
            regime = "SIDEWAYS"
            confidence = 0.5

        return {
            "regime": regime,
            "confidence": float(confidence),
            "metrics": {
                "avg_price_change": float(avg_price_change),
                "avg_volatility": float(avg_volatility),
                "avg_momentum": float(avg_momentum),
            },
        }

    def rank_opportunities(
        self, statistical_results: Dict, ml_results: Dict, predictive_results: Dict
    ) -> List:
        """Rank trading opportunities"""

        opportunities = []

        for symbol in statistical_results.keys():
            try:
                stat_data = statistical_results[symbol]
                ml_data = ml_results.get("individual_results", {}).get(symbol, {})
                pred_data = predictive_results.get("symbol_predictions", {}).get(
                    symbol, {}
                )

                # Calculate opportunity score
                momentum_score = stat_data["momentum_analysis"]["combined_momentum"]
                volatility_score = min(
                    stat_data["price_data"]["volatility_1h"] / 0.1, 1.0
                )
                volume_score = min(
                    stat_data["volume_analysis"]["current_volume_ratio"] / 2, 1.0
                )

                # ML factors
                is_outlier = ml_data.get("is_outlier", False)
                outlier_bonus = 0.2 if is_outlier else 0

                # Prediction factors
                pred_avg = (
                    np.mean(list(pred_data.get("predictions", {}).values()))
                    if pred_data.get("predictions")
                    else 0
                )
                prediction_score = pred_avg / 10  # Normalize

                # Combined score
                opportunity_score = (
                    momentum_score * 0.4
                    + volatility_score * 0.2
                    + volume_score * 0.2
                    + prediction_score * 0.2
                    + outlier_bonus
                )

                opportunities.append(
                    {
                        "symbol": symbol,
                        "opportunity_score": float(opportunity_score),
                        "momentum_score": float(momentum_score),
                        "volatility_score": float(volatility_score),
                        "volume_score": float(volume_score),
                        "prediction_score": float(prediction_score),
                        "is_outlier": is_outlier,
                        "current_price": stat_data["price_data"]["current_price"],
                        "price_change_24h": stat_data["price_data"]["price_change_24h"],
                    }
                )

            except Exception as e:
                continue

        # Sort by opportunity score
        opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)

        return opportunities[:20]  # Top 20 opportunities

    def assess_risks(self, statistical_results: Dict) -> Dict:
        """Assess market risks"""

        risks = []

        for symbol, data in statistical_results.items():
            try:
                var_95 = abs(data["returns_analysis"]["var_95"])
                max_drawdown = abs(data["returns_analysis"]["max_drawdown"])
                volatility = data["price_data"]["volatility_1h"]

                risk_score = var_95 * 0.4 + max_drawdown * 0.4 + volatility * 0.2

                risks.append(
                    {
                        "symbol": symbol,
                        "risk_score": float(risk_score),
                        "var_95": float(var_95),
                        "max_drawdown": float(max_drawdown),
                        "volatility": float(volatility),
                    }
                )

            except:
                continue

        risks.sort(key=lambda x: x["risk_score"], reverse=True)

        return {
            "highest_risk_assets": risks[:10],
            "lowest_risk_assets": risks[-10:],
            "market_risk_level": (
                "HIGH"
                if np.mean([r["risk_score"] for r in risks]) > 0.1
                else "MODERATE"
            ),
        }

    def generate_portfolio_recommendations(
        self, statistical_results: Dict, ml_results: Dict
    ) -> Dict:
        """Generate portfolio allocation recommendations"""

        # Get cluster analysis
        cluster_analysis = ml_results.get("cluster_analysis", {})

        recommendations = {
            "diversification_strategy": "Select assets from different clusters for diversification",
            "cluster_allocations": {},
            "top_picks": [],
            "avoid_list": [],
        }

        # Analyze clusters
        for cluster_name, cluster_data in cluster_analysis.items():
            cluster_symbols = cluster_data["symbols"]
            cluster_chars = cluster_data["characteristics"]

            # Determine cluster strategy
            if (
                cluster_chars["avg_momentum"] > 0.1
                and cluster_chars["avg_price_change"] > 0
            ):
                strategy = "GROWTH"
                allocation = 0.4
            elif cluster_chars["avg_volatility"] < 0.03:
                strategy = "STABLE"
                allocation = 0.3
            elif cluster_chars["avg_volume_ratio"] > 1.5:
                strategy = "HIGH_ACTIVITY"
                allocation = 0.2
            else:
                strategy = "SPECULATIVE"
                allocation = 0.1

            recommendations["cluster_allocations"][cluster_name] = {
                "strategy": strategy,
                "recommended_allocation": allocation,
                "symbols": cluster_symbols[:3],  # Top 3 from cluster
            }

        return recommendations

    def generate_trading_signals(
        self, statistical_results: Dict, predictive_results: Dict
    ) -> List:
        """Generate specific trading signals"""

        signals = []

        for symbol in statistical_results.keys():
            try:
                stat_data = statistical_results[symbol]
                pred_data = predictive_results.get("symbol_predictions", {}).get(
                    symbol, {}
                )

                # Technical signals
                rsi = stat_data["technical_indicators"]["rsi_1h"]
                macd = stat_data["technical_indicators"]["macd_1h"]
                bb_position = stat_data["technical_indicators"]["bb_position_1h"]
                momentum = stat_data["momentum_analysis"]["combined_momentum"]

                # Prediction signals
                predictions = pred_data.get("predictions", {})
                avg_prediction = (
                    np.mean(list(predictions.values())) if predictions else 0
                )

                # Generate signal
                signal_strength = 0
                signal_type = "HOLD"
                reasons = []

                # Bullish signals
                if rsi < 30:
                    signal_strength += 0.3
                    reasons.append("RSI oversold")
                if momentum > 0.2:
                    signal_strength += 0.4
                    reasons.append("Strong momentum")
                if avg_prediction > 5:
                    signal_strength += 0.3
                    reasons.append("Positive predictions")
                if bb_position < 0.2:
                    signal_strength += 0.2
                    reasons.append("Below Bollinger lower band")

                # Bearish signals
                if rsi > 70:
                    signal_strength -= 0.3
                    reasons.append("RSI overbought")
                if momentum < -0.2:
                    signal_strength -= 0.4
                    reasons.append("Negative momentum")
                if avg_prediction < -5:
                    signal_strength -= 0.3
                    reasons.append("Negative predictions")
                if bb_position > 0.8:
                    signal_strength -= 0.2
                    reasons.append("Above Bollinger upper band")

                # Determine signal type
                if signal_strength > 0.5:
                    signal_type = "STRONG_BUY"
                elif signal_strength > 0.2:
                    signal_type = "BUY"
                elif signal_strength < -0.5:
                    signal_type = "STRONG_SELL"
                elif signal_strength < -0.2:
                    signal_type = "SELL"

                if signal_type != "HOLD":
                    signals.append(
                        {
                            "symbol": symbol,
                            "signal": signal_type,
                            "strength": float(signal_strength),
                            "reasons": reasons,
                            "current_price": stat_data["price_data"]["current_price"],
                            "predicted_change": float(avg_prediction),
                        }
                    )

            except:
                continue

        # Sort by signal strength
        signals.sort(key=lambda x: abs(x["strength"]), reverse=True)

        return signals[:15]  # Top 15 signals

    def analyze_market_microstructure(self, statistical_results: Dict) -> Dict:
        """Analyze market microstructure patterns"""

        # Analyze volume patterns
        volume_patterns = {}
        price_patterns = {}

        for symbol, data in statistical_results.items():
            try:
                volume_data = data["volume_analysis"]
                price_change = data["price_data"]["price_change_24h"]
                volatility = data["price_data"]["volatility_1h"]

                # Volume pattern classification
                if volume_data["current_volume_ratio"] > 2:
                    volume_pattern = "VOLUME_SPIKE"
                elif volume_data["volume_pattern"] == "increasing":
                    volume_pattern = "VOLUME_BUILDING"
                elif volume_data["current_volume_ratio"] < 0.5:
                    volume_pattern = "LOW_VOLUME"
                else:
                    volume_pattern = "NORMAL_VOLUME"

                volume_patterns[symbol] = volume_pattern

                # Price pattern classification
                if abs(price_change) > 10 and volatility > 0.05:
                    price_pattern = "HIGH_VOLATILITY_BREAKOUT"
                elif price_change > 5:
                    price_pattern = "BULLISH_MOMENTUM"
                elif price_change < -5:
                    price_pattern = "BEARISH_MOMENTUM"
                else:
                    price_pattern = "CONSOLIDATION"

                price_patterns[symbol] = price_pattern

            except:
                continue

        return {
            "volume_patterns": volume_patterns,
            "price_patterns": price_patterns,
            "pattern_summary": {
                "volume_spikes": sum(
                    1 for p in volume_patterns.values() if p == "VOLUME_SPIKE"
                ),
                "breakouts": sum(
                    1
                    for p in price_patterns.values()
                    if p == "HIGH_VOLATILITY_BREAKOUT"
                ),
                "bullish_momentum": sum(
                    1 for p in price_patterns.values() if p == "BULLISH_MOMENTUM"
                ),
            },
        }

    def predict_market_regime_changes(self, statistical_results: Dict) -> Dict:
        """Predict potential market regime changes"""

        # Analyze leading indicators
        momentum_values = [
            data["momentum_analysis"]["combined_momentum"]
            for data in statistical_results.values()
        ]
        volatility_values = [
            data["price_data"]["volatility_1h"] for data in statistical_results.values()
        ]
        volume_ratios = [
            data["volume_analysis"]["current_volume_ratio"]
            for data in statistical_results.values()
        ]

        # Calculate regime change signals
        momentum_divergence = np.std(momentum_values)
        volatility_spike = max(volatility_values) / np.mean(volatility_values)
        volume_anomaly = max(volume_ratios) / np.mean(volume_ratios)

        regime_change_probability = 0
        signals = []

        if momentum_divergence > 0.5:
            regime_change_probability += 0.3
            signals.append("High momentum divergence detected")

        if volatility_spike > 2:
            regime_change_probability += 0.4
            signals.append("Volatility spike detected")

        if volume_anomaly > 3:
            regime_change_probability += 0.3
            signals.append("Volume anomaly detected")

        return {
            "regime_change_probability": float(min(regime_change_probability, 1.0)),
            "signals": signals,
            "leading_indicators": {
                "momentum_divergence": float(momentum_divergence),
                "volatility_spike": float(volatility_spike),
                "volume_anomaly": float(volume_anomaly),
            },
        }

    def run_complete_analysis(self, symbols: List[str] = None) -> Dict:
        """Run complete quantum data analysis"""

        print("🚀 Starting Quantum Data Analysis...")

        if symbols is None:
            # Get all tradable USDT symbols
            exchange_info = self.client.get_exchange_info()
            symbols = [
                s["symbol"]
                for s in exchange_info["symbols"]
                if s["symbol"].endswith("USDT") and s["status"] == "TRADING"
            ]
            symbols = symbols[:30]  # Limit for demo

        print(f"📊 Analyzing {len(symbols)} symbols...")

        # Step 1: Get comprehensive market data
        market_data = self.get_comprehensive_market_data(symbols)

        if not market_data:
            print("❌ No market data available")
            return {}

        # Step 2: Statistical analysis
        statistical_results = self.perform_statistical_analysis(market_data)

        # Step 3: Machine learning analysis
        ml_results = self.perform_machine_learning_analysis(statistical_results)

        # Step 4: Predictive modeling
        predictive_results = self.generate_predictive_models(statistical_results)

        # Step 5: Generate quantum insights
        quantum_insights = self.generate_quantum_insights(
            statistical_results, ml_results, predictive_results
        )

        # Compile final results
        final_results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "symbols_analyzed": len(statistical_results),
            "statistical_analysis": statistical_results,
            "machine_learning_analysis": ml_results,
            "predictive_analysis": predictive_results,
            "quantum_insights": quantum_insights,
            "executive_summary": self.generate_executive_summary(quantum_insights),
        }

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quantum_data_analysis_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(final_results, f, indent=2, default=str)

        print(f"✅ Quantum Data Analysis completed!")
        print(f"📁 Results saved to: {filename}")
        print(f"📊 Analyzed {len(statistical_results)} symbols")
        print(
            f"🤖 ML clusters: {ml_results.get('cluster_analysis', {}).keys() if ml_results else 'N/A'}"
        )
        print(
            f"🔮 Top opportunities: {len(quantum_insights.get('opportunity_ranking', []))}"
        )
        print(f"📈 Trading signals: {len(quantum_insights.get('trading_signals', []))}")

        return final_results

    def generate_executive_summary(self, quantum_insights: Dict) -> Dict:
        """Generate executive summary of the analysis"""

        market_regime = quantum_insights.get("market_regime_analysis", {})
        opportunities = quantum_insights.get("opportunity_ranking", [])
        risks = quantum_insights.get("risk_assessment", {})
        signals = quantum_insights.get("trading_signals", [])

        return {
            "market_outlook": {
                "current_regime": market_regime.get("regime", "UNKNOWN"),
                "regime_confidence": market_regime.get("confidence", 0),
                "key_metrics": market_regime.get("metrics", {}),
            },
            "top_opportunities": opportunities[:5] if opportunities else [],
            "immediate_signals": signals[:5] if signals else [],
            "risk_level": risks.get("market_risk_level", "UNKNOWN"),
            "recommendations": [
                f"Current market regime: {market_regime.get('regime', 'UNKNOWN')}",
                f"Top opportunity: {opportunities[0]['symbol'] if opportunities else 'None detected'}",
                f"Risk level: {risks.get('market_risk_level', 'UNKNOWN')}",
                f"Active signals: {len(signals)} detected",
            ],
        }


def main():
    """Main execution function"""

    print("⚛️  QUANTUM DATA-DRIVEN MARKET ANALYSIS SYSTEM ⚛️")
    print("=" * 60)

    analyst = QuantumDataAnalyst()

    # Run complete analysis
    results = analyst.run_complete_analysis()

    if results:
        print("\n" + "=" * 60)
        print("📋 EXECUTIVE SUMMARY")
        print("=" * 60)

        summary = results.get("executive_summary", {})

        print(
            f"📊 Market Regime: {summary.get('market_outlook', {}).get('current_regime', 'Unknown')}"
        )
        print(f"📈 Risk Level: {summary.get('risk_level', 'Unknown')}")
        print(f"🎯 Symbols Analyzed: {results.get('symbols_analyzed', 0)}")
        print(
            f"🚨 Active Signals: {len(results.get('quantum_insights', {}).get('trading_signals', []))}"
        )

        print("\n🏆 TOP OPPORTUNITIES:")
        for i, opp in enumerate(summary.get("top_opportunities", [])[:3], 1):
            print(
                f"  {i}. {opp['symbol']}: Score {opp['opportunity_score']:.3f} "
                f"({opp['price_change_24h']:+.2f}%)"
            )

        print("\n⚡ IMMEDIATE SIGNALS:")
        for signal in summary.get("immediate_signals", [])[:3]:
            print(
                f"  • {signal['symbol']}: {signal['signal']} "
                f"(Strength: {signal['strength']:.2f})"
            )

        print("\n📝 KEY RECOMMENDATIONS:")
        for rec in summary.get("recommendations", []):
            print(f"  • {rec}")

    print("\n🎉 Quantum analysis complete!")


if __name__ == "__main__":
    main()
