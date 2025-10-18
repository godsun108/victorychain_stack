#!/usr/bin/env python3
"""
Advanced Data-Driven Market Analysis System (Simplified)
Statistical models, quantitative analysis, and predictive modeling
"""

import os
import json
import time
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from binance.client import Client
from dotenv import load_dotenv

warnings.filterwarnings("ignore")


class AdvancedDataAnalyst:
    def __init__(self):
        load_dotenv()

        # Initialize Binance client
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        print("📊 Advanced Data-Driven Analyst initialized")
        print("🔬 Loading statistical models and quantitative indicators...")

    def get_comprehensive_ohlcv_data(
        self, symbols: List[str], limit: int = 100
    ) -> Dict:
        """Get comprehensive OHLCV data for statistical analysis"""

        print(f"📈 Gathering OHLCV data for {len(symbols)} symbols...")

        ohlcv_data = {}
        failed_symbols = []

        for i, symbol in enumerate(symbols):
            try:
                # Get multiple timeframes
                klines_1h = self.client.get_klines(
                    symbol=symbol, interval="1h", limit=limit
                )
                klines_4h = self.client.get_klines(
                    symbol=symbol, interval="4h", limit=limit // 4
                )
                klines_1d = self.client.get_klines(
                    symbol=symbol, interval="1d", limit=limit // 24
                )

                if klines_1h and klines_4h and klines_1d:
                    ohlcv_data[symbol] = {
                        "1h": self.parse_klines(klines_1h),
                        "4h": self.parse_klines(klines_4h),
                        "1d": self.parse_klines(klines_1d),
                    }

                # Progress indicator
                if (i + 1) % 10 == 0:
                    print(f"📊 Processed {i + 1}/{len(symbols)} symbols...")

                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                failed_symbols.append(symbol)
                continue

        print(f"✅ Successfully gathered data for {len(ohlcv_data)} symbols")
        if failed_symbols:
            print(f"⚠️  Failed to get data for {len(failed_symbols)} symbols")

        return ohlcv_data

    def parse_klines(self, klines: List) -> pd.DataFrame:
        """Parse klines data into DataFrame"""

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
        numeric_cols = ["open", "high", "low", "close", "volume", "quote_volume"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        return df

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators without TA-Lib"""

        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # Moving averages
        df["sma_10"] = close.rolling(window=10).mean()
        df["sma_20"] = close.rolling(window=20).mean()
        df["ema_12"] = close.ewm(span=12).mean()
        df["ema_26"] = close.ewm(span=26).mean()

        # MACD
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

        # Stochastic
        lowest_low = low.rolling(window=14).min()
        highest_high = high.rolling(window=14).max()
        df["stoch_k"] = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        df["stoch_d"] = df["stoch_k"].rolling(window=3).mean()

        # Volume indicators
        df["volume_sma"] = volume.rolling(window=20).mean()
        df["volume_ratio"] = volume / df["volume_sma"]

        # ATR (Average True Range)
        df["tr1"] = high - low
        df["tr2"] = abs(high - close.shift())
        df["tr3"] = abs(low - close.shift())
        df["true_range"] = df[["tr1", "tr2", "tr3"]].max(axis=1)
        df["atr"] = df["true_range"].rolling(window=14).mean()

        # Volatility
        df["volatility"] = close.rolling(window=20).std()

        # Returns
        df["returns_1h"] = close.pct_change()
        df["returns_24h"] = close.pct_change(24)
        df["log_returns"] = np.log(close / close.shift(1))

        return df

    def calculate_advanced_metrics(
        self, symbol: str, df_1h: pd.DataFrame, df_4h: pd.DataFrame, df_1d: pd.DataFrame
    ) -> Dict:
        """Calculate advanced statistical metrics"""

        metrics = {"symbol": symbol}

        # Price momentum analysis
        current_price = df_1h["close"].iloc[-1]
        metrics["price_momentum"] = {
            "1h_change": (
                (current_price / df_1h["close"].iloc[-2] - 1) * 100
                if len(df_1h) > 1
                else 0
            ),
            "4h_change": (
                (current_price / df_1h["close"].iloc[-5] - 1) * 100
                if len(df_1h) > 4
                else 0
            ),
            "24h_change": (
                (current_price / df_1h["close"].iloc[-25] - 1) * 100
                if len(df_1h) > 24
                else 0
            ),
            "7d_change": (
                (current_price / df_1d["close"].iloc[-8] - 1) * 100
                if len(df_1d) > 7
                else 0
            ),
        }

        # Volatility analysis
        returns_1h = df_1h["returns_1h"].dropna()
        returns_1d = df_1d["returns_1h"].dropna() if len(df_1d) > 1 else returns_1h

        if len(returns_1h) > 0:
            metrics["volatility"] = {
                "hourly_vol": returns_1h.std()
                * np.sqrt(24)
                * 100,  # Annualized hourly vol
                "daily_vol": returns_1d.std()
                * np.sqrt(365)
                * 100,  # Annualized daily vol
                "vol_of_vol": (
                    returns_1h.rolling(24).std().std() * 100
                    if len(returns_1h) > 24
                    else 0
                ),
                "skewness": returns_1h.skew(),
                "kurtosis": returns_1h.kurtosis(),
            }
        else:
            metrics["volatility"] = {
                "hourly_vol": 0,
                "daily_vol": 0,
                "vol_of_vol": 0,
                "skewness": 0,
                "kurtosis": 0,
            }

        # Technical strength
        latest_1h = df_1h.iloc[-1]
        metrics["technical_strength"] = {
            "rsi": latest_1h["rsi"] if not pd.isna(latest_1h["rsi"]) else 50,
            "macd_signal": 1 if latest_1h["macd"] > latest_1h["macd_signal"] else -1,
            "bb_position": (
                latest_1h["bb_position"]
                if not pd.isna(latest_1h["bb_position"])
                else 0.5
            ),
            "sma_position": 1 if current_price > latest_1h["sma_20"] else -1,
            "volume_strength": (
                latest_1h["volume_ratio"]
                if not pd.isna(latest_1h["volume_ratio"])
                else 1
            ),
        }

        # Trend analysis
        close_prices = df_1h["close"].values[-50:]  # Last 50 hours
        if len(close_prices) > 10:
            x = np.arange(len(close_prices))
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                x, close_prices
            )

            metrics["trend_analysis"] = {
                "trend_slope": slope,
                "trend_strength": r_value**2,  # R-squared
                "trend_significance": p_value,
                "trend_direction": 1 if slope > 0 else -1,
            }
        else:
            metrics["trend_analysis"] = {
                "trend_slope": 0,
                "trend_strength": 0,
                "trend_significance": 1,
                "trend_direction": 0,
            }

        # Volume analysis
        volume_24h = (
            df_1h["volume"].tail(24).sum()
            if len(df_1h) >= 24
            else df_1h["volume"].sum()
        )
        volume_7d_avg = (
            df_1h["volume"].tail(168).mean() * 24 if len(df_1h) >= 168 else volume_24h
        )

        volume_corr = 0
        if len(df_1h) >= 24:
            try:
                volume_corr = pearsonr(
                    df_1h["close"].tail(24).values, df_1h["volume"].tail(24).values
                )[0]
                if np.isnan(volume_corr):
                    volume_corr = 0
            except:
                volume_corr = 0

        metrics["volume_analysis"] = {
            "volume_24h": volume_24h,
            "volume_trend": volume_24h / volume_7d_avg if volume_7d_avg > 0 else 1,
            "volume_consistency": (
                1 - (df_1h["volume"].tail(24).std() / df_1h["volume"].tail(24).mean())
                if len(df_1h) >= 24
                else 0
            ),
            "price_volume_correlation": volume_corr,
        }

        # Support/Resistance levels
        highs = df_1h["high"].tail(100) if len(df_1h) >= 100 else df_1h["high"]
        lows = df_1h["low"].tail(100) if len(df_1h) >= 100 else df_1h["low"]

        resistance_level = np.percentile(highs, 95)
        support_level = np.percentile(lows, 5)

        metrics["support_resistance"] = {
            "resistance_level": resistance_level,
            "support_level": support_level,
            "distance_to_resistance": (resistance_level - current_price)
            / current_price
            * 100,
            "distance_to_support": (current_price - support_level)
            / current_price
            * 100,
        }

        return metrics

    def perform_statistical_analysis(self, all_metrics: List[Dict]) -> Dict:
        """Perform comprehensive statistical analysis across all tokens"""

        print("🔬 Performing advanced statistical analysis...")

        # Create feature matrix
        features = []
        symbols = []

        for metrics in all_metrics:
            try:
                feature_vector = [
                    metrics["price_momentum"]["1h_change"],
                    metrics["price_momentum"]["4h_change"],
                    metrics["price_momentum"]["24h_change"],
                    metrics["volatility"]["hourly_vol"],
                    metrics["volatility"]["daily_vol"],
                    metrics["technical_strength"]["rsi"],
                    metrics["technical_strength"]["bb_position"],
                    metrics["technical_strength"]["volume_strength"],
                    metrics["trend_analysis"]["trend_slope"],
                    metrics["trend_analysis"]["trend_strength"],
                    metrics["volume_analysis"]["volume_trend"],
                    metrics["volume_analysis"]["price_volume_correlation"],
                    metrics["support_resistance"]["distance_to_resistance"],
                    metrics["support_resistance"]["distance_to_support"],
                ]

                # Check for NaN/infinite values
                if not any(np.isnan(feature_vector)) and not any(
                    np.isinf(feature_vector)
                ):
                    features.append(feature_vector)
                    symbols.append(metrics["symbol"])

            except (KeyError, TypeError):
                continue

        if len(features) < 10:
            return {"error": "Insufficient data for statistical analysis"}

        features_array = np.array(features)

        # Standardize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features_array)

        # Cluster analysis
        n_clusters = min(5, len(features) // 10)
        if n_clusters >= 2:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(features_scaled)
        else:
            clusters = np.zeros(len(features))
            n_clusters = 1

        # PCA analysis
        n_components = min(3, features_array.shape[1])
        pca = PCA(n_components=n_components)
        pca_features = pca.fit_transform(features_scaled)

        # Correlation analysis
        feature_names = [
            "1h_change",
            "4h_change",
            "24h_change",
            "hourly_vol",
            "daily_vol",
            "rsi",
            "bb_position",
            "volume_strength",
            "trend_slope",
            "trend_strength",
            "volume_trend",
            "price_volume_corr",
            "dist_resistance",
            "dist_support",
        ]

        correlation_matrix = np.corrcoef(features_array.T)

        # Identify statistical outliers
        outliers = []
        for i, symbol in enumerate(symbols):
            z_scores = np.abs(stats.zscore(features_scaled[i]))
            if np.max(z_scores) > 3:  # 3 standard deviations
                outliers.append(
                    {
                        "symbol": symbol.replace("USDT", ""),
                        "max_z_score": np.max(z_scores),
                        "outlier_features": [
                            feature_names[j] for j, z in enumerate(z_scores) if z > 2
                        ],
                    }
                )

        # Market regime analysis
        market_momentum = np.mean([f[0] for f in features])  # Average 1h change
        market_volatility = np.mean([f[3] for f in features])  # Average hourly vol
        market_trend_strength = np.mean(
            [f[9] for f in features]
        )  # Average trend strength

        regime = "unknown"
        if market_momentum > 2 and market_volatility < 50:
            regime = "bull_trending"
        elif market_momentum < -2 and market_volatility < 50:
            regime = "bear_trending"
        elif market_volatility > 100:
            regime = "high_volatility"
        elif abs(market_momentum) < 1 and market_volatility < 30:
            regime = "low_volatility_range"
        else:
            regime = "mixed_conditions"

        return {
            "statistical_summary": {
                "total_tokens_analyzed": len(symbols),
                "feature_dimensions": features_array.shape[1],
                "market_regime": regime,
                "market_momentum": market_momentum,
                "market_volatility": market_volatility,
                "market_trend_strength": market_trend_strength,
            },
            "cluster_analysis": {
                "n_clusters": n_clusters,
                "tokens_by_cluster": {
                    i: [
                        symbols[j].replace("USDT", "")
                        for j, c in enumerate(clusters)
                        if c == i
                    ]
                    for i in range(n_clusters)
                },
            },
            "pca_analysis": {
                "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
                "cumulative_variance": np.cumsum(
                    pca.explained_variance_ratio_
                ).tolist(),
            },
            "correlation_insights": {
                "strong_correlations": [
                    f"{feature_names[i]} vs {feature_names[j]}: {correlation_matrix[i][j]:.3f}"
                    for i in range(len(feature_names))
                    for j in range(i + 1, len(feature_names))
                    if abs(correlation_matrix[i][j]) > 0.5
                    and not np.isnan(correlation_matrix[i][j])
                ]
            },
            "statistical_outliers": sorted(
                outliers, key=lambda x: x["max_z_score"], reverse=True
            )[:10],
            "feature_statistics": {
                feature_names[i]: {
                    "mean": np.mean(features_array[:, i]),
                    "std": np.std(features_array[:, i]),
                    "min": np.min(features_array[:, i]),
                    "max": np.max(features_array[:, i]),
                    "percentile_90": np.percentile(features_array[:, i], 90),
                    "percentile_10": np.percentile(features_array[:, i], 10),
                }
                for i in range(len(feature_names))
            },
        }

    def build_predictive_models(self, all_metrics: List[Dict]) -> Dict:
        """Build predictive models for price movement"""

        print("🤖 Building predictive models...")

        # Prepare data for modeling
        X = []
        y = []
        symbols = []

        for metrics in all_metrics:
            try:
                # Features (current state)
                features = [
                    metrics["technical_strength"]["rsi"],
                    metrics["technical_strength"]["bb_position"],
                    metrics["technical_strength"]["volume_strength"],
                    metrics["trend_analysis"]["trend_slope"],
                    metrics["trend_analysis"]["trend_strength"],
                    metrics["volatility"]["hourly_vol"],
                    metrics["volume_analysis"]["volume_trend"],
                    metrics["volume_analysis"]["price_volume_correlation"],
                ]

                # Target (future price movement)
                target = metrics["price_momentum"]["1h_change"]  # Predict 1h change

                if (
                    not any(np.isnan(features))
                    and not np.isnan(target)
                    and not any(np.isinf(features))
                    and not np.isinf(target)
                ):
                    X.append(features)
                    y.append(target)
                    symbols.append(metrics["symbol"])

            except (KeyError, TypeError):
                continue

        if len(X) < 20:
            return {"error": "Insufficient data for predictive modeling"}

        X = np.array(X)
        y = np.array(y)

        # Split data (simple random split for demonstration)
        n_train = int(0.8 * len(X))
        indices = np.random.permutation(len(X))
        train_idx, test_idx = indices[:n_train], indices[n_train:]

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Linear regression model
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        lr_score = lr_model.score(X_test, y_test)

        # Random Forest model
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        rf_model.fit(X_train, y_train)
        rf_score = rf_model.score(X_test, y_test)

        # Feature importance
        feature_names = [
            "rsi",
            "bb_position",
            "volume_strength",
            "trend_slope",
            "trend_strength",
            "volatility",
            "volume_trend",
            "price_volume_corr",
        ]

        feature_importance = dict(zip(feature_names, rf_model.feature_importances_))

        # Make predictions for all tokens
        predictions = {}
        for i, symbol in enumerate(symbols):
            lr_pred = lr_model.predict([X[i]])[0]
            rf_pred = rf_model.predict([X[i]])[0]

            predictions[symbol.replace("USDT", "")] = {
                "linear_regression_pred": lr_pred,
                "random_forest_pred": rf_pred,
                "ensemble_pred": (lr_pred + rf_pred) / 2,
                "confidence": max(0, min(1, (lr_score + rf_score) / 2)),
            }

        return {
            "model_performance": {
                "linear_regression_r2": lr_score,
                "random_forest_r2": rf_score,
                "ensemble_performance": (lr_score + rf_score) / 2,
            },
            "feature_importance": dict(
                sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            ),
            "predictions": predictions,
            "model_summary": {
                "training_samples": len(X_train),
                "test_samples": len(X_test),
                "features_used": len(feature_names),
                "prediction_horizon": "1_hour",
            },
        }

    def run_comprehensive_data_analysis(self) -> Dict:
        """Run comprehensive data-driven analysis"""

        print("🚀 STARTING COMPREHENSIVE DATA-DRIVEN ANALYSIS")
        print("=" * 60)

        # Get top tokens by volume for analysis
        tickers = self.client.get_ticker()
        usdt_pairs = [
            t
            for t in tickers
            if t["symbol"].endswith("USDT") and t["symbol"] != "USDCUSDT"
        ]

        # Sort by volume and take top 25 for detailed analysis (reduced for speed)
        volume_sorted = sorted(
            usdt_pairs, key=lambda x: float(x["quoteVolume"]), reverse=True
        )
        top_symbols = [t["symbol"] for t in volume_sorted[:25]]

        print(
            f"📊 Analyzing top 25 tokens by volume for comprehensive data analysis..."
        )

        # Get OHLCV data
        ohlcv_data = self.get_comprehensive_ohlcv_data(
            top_symbols, limit=72
        )  # 3 days of hourly data

        if len(ohlcv_data) < 5:
            print("❌ Insufficient data for comprehensive analysis")
            return {}

        # Calculate metrics for each token
        all_metrics = []

        print("🔬 Calculating advanced metrics...")
        for symbol, data in ohlcv_data.items():
            try:
                # Calculate technical indicators
                df_1h = self.calculate_technical_indicators(data["1h"].copy())
                df_4h = self.calculate_technical_indicators(data["4h"].copy())
                df_1d = self.calculate_technical_indicators(data["1d"].copy())

                # Calculate advanced metrics
                metrics = self.calculate_advanced_metrics(symbol, df_1h, df_4h, df_1d)
                all_metrics.append(metrics)

            except Exception as e:
                print(f"⚠️ Error calculating metrics for {symbol}: {e}")
                continue

        print(f"✅ Calculated metrics for {len(all_metrics)} tokens")

        if len(all_metrics) < 5:
            print("❌ Insufficient valid metrics for analysis")
            return {}

        # Perform statistical analysis
        statistical_analysis = self.perform_statistical_analysis(all_metrics)

        # Build predictive models
        predictive_models = self.build_predictive_models(all_metrics)

        # Generate insights
        quantitative_insights = self.generate_quantitative_insights(
            statistical_analysis, predictive_models
        )

        # Compile comprehensive report
        comprehensive_report = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "comprehensive_data_driven",
            "tokens_analyzed": len(all_metrics),
            "statistical_analysis": statistical_analysis,
            "predictive_models": predictive_models,
            "quantitative_insights": quantitative_insights,
        }

        # Display results
        self.display_data_driven_results(comprehensive_report)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_data_analysis_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(comprehensive_report, f, indent=2, default=str)

        print(f"\n💾 Comprehensive data analysis saved: {filename}")

        return comprehensive_report

    def generate_quantitative_insights(
        self, statistical_analysis: Dict, predictive_models: Dict
    ) -> Dict:
        """Generate quantitative trading insights"""

        insights = {
            "market_regime_analysis": {},
            "statistical_opportunities": [],
            "predictive_signals": [],
            "risk_metrics": {},
            "quantitative_recommendations": [],
        }

        if "error" in statistical_analysis or "error" in predictive_models:
            return insights

        # Market regime insights
        stats_summary = statistical_analysis.get("statistical_summary", {})
        regime = stats_summary.get("market_regime", "unknown")
        momentum = stats_summary.get("market_momentum", 0)
        volatility = stats_summary.get("market_volatility", 50)

        insights["market_regime_analysis"] = {
            "current_regime": regime,
            "regime_characteristics": self.get_regime_characteristics(regime),
            "momentum_score": momentum,
            "volatility_percentile": min(volatility / 100, 1.0),
            "regime_stability": stats_summary.get("market_trend_strength", 0.5),
        }

        # Statistical opportunities
        outliers = statistical_analysis.get("statistical_outliers", [])
        for outlier in outliers[:5]:
            insights["statistical_opportunities"].append(
                {
                    "token": outlier["symbol"],
                    "opportunity_type": "statistical_outlier",
                    "z_score": outlier["max_z_score"],
                    "reasoning": f"Statistical outlier in {', '.join(outlier['outlier_features'][:3])}",
                    "confidence": min(outlier["max_z_score"] / 5, 1.0),
                }
            )

        # Predictive signals
        if "predictions" in predictive_models:
            predictions = predictive_models["predictions"]
            sorted_predictions = sorted(
                predictions.items(),
                key=lambda x: abs(x[1]["ensemble_pred"]),
                reverse=True,
            )

            for token, pred in sorted_predictions[:10]:
                if abs(pred["ensemble_pred"]) > 1:  # Significant prediction
                    insights["predictive_signals"].append(
                        {
                            "token": token,
                            "predicted_change": pred["ensemble_pred"],
                            "signal_strength": abs(pred["ensemble_pred"]),
                            "model_confidence": pred["confidence"],
                            "direction": (
                                "bullish" if pred["ensemble_pred"] > 0 else "bearish"
                            ),
                        }
                    )

        # Risk metrics
        insights["risk_metrics"] = {
            "market_volatility_regime": (
                "high" if volatility > 80 else "medium" if volatility > 40 else "low"
            ),
            "regime_uncertainty": 1 - stats_summary.get("market_trend_strength", 0.5),
            "outlier_concentration": len(outliers)
            / stats_summary.get("total_tokens_analyzed", 1),
        }

        # Recommendations based on regime
        if regime == "bull_trending":
            insights["quantitative_recommendations"].extend(
                [
                    "High conviction long positions on momentum leaders",
                    "Focus on breakout patterns and trend continuation",
                    "Reduce hedging, increase position sizes gradually",
                ]
            )
        elif regime == "bear_trending":
            insights["quantitative_recommendations"].extend(
                [
                    "Implement strong risk management and stop losses",
                    "Increase cash positions and defensive positioning",
                    "Avoid new long positions until trend reversal",
                ]
            )
        elif regime == "high_volatility":
            insights["quantitative_recommendations"].extend(
                [
                    "Reduce position sizes due to high volatility",
                    "Increase monitoring frequency",
                    "Focus on mean reversion opportunities",
                ]
            )
        else:
            insights["quantitative_recommendations"].extend(
                [
                    "Maintain balanced approach in mixed conditions",
                    "Focus on high-conviction opportunities only",
                    "Monitor for regime change signals",
                ]
            )

        return insights

    def get_regime_characteristics(self, regime: str) -> str:
        """Get characteristics of market regime"""

        regime_map = {
            "bull_trending": "Strong upward momentum with controlled volatility",
            "bear_trending": "Consistent downward pressure with controlled volatility",
            "high_volatility": "Large price swings, increased uncertainty",
            "low_volatility_range": "Stable, range-bound market conditions",
            "mixed_conditions": "No clear directional bias, mixed signals",
        }

        return regime_map.get(regime, "Unknown market conditions")

    def display_data_driven_results(self, report: Dict):
        """Display comprehensive data-driven results"""

        print("\n📊 COMPREHENSIVE DATA-DRIVEN ANALYSIS RESULTS")
        print("=" * 60)

        # Statistical summary
        if (
            "statistical_analysis" in report
            and "error" not in report["statistical_analysis"]
        ):
            stats = report["statistical_analysis"]["statistical_summary"]
            print(f"🔬 STATISTICAL SUMMARY:")
            print(f"   Tokens Analyzed: {stats['total_tokens_analyzed']}")
            print(f"   Market Regime: {stats['market_regime'].upper()}")
            print(f"   Market Momentum: {stats['market_momentum']:+.2f}%")
            print(f"   Market Volatility: {stats['market_volatility']:.1f}%")
            print(f"   Trend Strength: {stats['market_trend_strength']:.3f}")

            # Cluster analysis
            clusters = report["statistical_analysis"]["cluster_analysis"]
            print(f"\n🏷️  CLUSTER ANALYSIS:")
            print(f"   Number of Clusters: {clusters['n_clusters']}")
            for i, tokens in clusters["tokens_by_cluster"].items():
                if tokens:
                    print(
                        f"   Cluster {i}: {tokens[:5]}{'...' if len(tokens) > 5 else ''}"
                    )

            # PCA
            pca = report["statistical_analysis"]["pca_analysis"]
            print(f"\n📊 PRINCIPAL COMPONENT ANALYSIS:")
            print(
                f"   Variance Explained: {[f'{v:.1%}' for v in pca['explained_variance_ratio']]}"
            )
            print(
                f"   Cumulative Variance: {[f'{v:.1%}' for v in pca['cumulative_variance']]}"
            )

            # Outliers
            outliers = report["statistical_analysis"]["statistical_outliers"]
            if outliers:
                print(f"\n🔍 STATISTICAL OUTLIERS:")
                for i, outlier in enumerate(outliers[:5], 1):
                    print(
                        f"   {i}. {outlier['symbol']}: Z-Score {outlier['max_z_score']:.2f}"
                    )

        # Predictive models
        if "predictive_models" in report and "error" not in report["predictive_models"]:
            perf = report["predictive_models"]["model_performance"]
            print(f"\n🤖 PREDICTIVE MODEL PERFORMANCE:")
            print(f"   Linear Regression R²: {perf['linear_regression_r2']:.3f}")
            print(f"   Random Forest R²: {perf['random_forest_r2']:.3f}")
            print(f"   Ensemble Performance: {perf['ensemble_performance']:.3f}")

            # Feature importance
            importance = report["predictive_models"]["feature_importance"]
            print(f"\n📈 TOP PREDICTIVE FEATURES:")
            for i, (feature, score) in enumerate(list(importance.items())[:5], 1):
                print(f"   {i}. {feature}: {score:.3f}")

            # Top predictions
            predictions = report["predictive_models"]["predictions"]
            sorted_preds = sorted(
                predictions.items(),
                key=lambda x: abs(x[1]["ensemble_pred"]),
                reverse=True,
            )

            print(f"\n🎯 TOP PREDICTIONS:")
            for i, (token, pred) in enumerate(sorted_preds[:5], 1):
                direction = "📈" if pred["ensemble_pred"] > 0 else "📉"
                print(
                    f"   {i}. {token} {direction}: {pred['ensemble_pred']:+.2f}% "
                    f"(Confidence: {pred['confidence']:.2f})"
                )

        # Quantitative insights
        insights = report["quantitative_insights"]
        regime = insights["market_regime_analysis"]

        print(f"\n🎯 MARKET REGIME ANALYSIS:")
        print(f"   Current Regime: {regime['current_regime'].upper()}")
        print(f"   Characteristics: {regime['regime_characteristics']}")
        print(f"   Momentum Score: {regime['momentum_score']:+.2f}")
        print(f"   Volatility Level: {regime['volatility_percentile']:.1%}")

        # Statistical opportunities
        stat_opps = insights["statistical_opportunities"]
        if stat_opps:
            print(f"\n🔍 STATISTICAL OPPORTUNITIES:")
            for i, opp in enumerate(stat_opps[:5], 1):
                print(
                    f"   {i}. {opp['token']}: {opp['reasoning']} (Z-Score: {opp['z_score']:.2f})"
                )

        # Predictive signals
        pred_signals = insights["predictive_signals"]
        if pred_signals:
            print(f"\n🎲 PREDICTIVE SIGNALS:")
            for i, signal in enumerate(pred_signals[:5], 1):
                direction = "🚀" if signal["direction"] == "bullish" else "🔻"
                print(
                    f"   {i}. {signal['token']} {direction}: {signal['predicted_change']:+.2f}% "
                    f"(Strength: {signal['signal_strength']:.1f})"
                )

        # Recommendations
        recommendations = insights["quantitative_recommendations"]
        if recommendations:
            print(f"\n💡 QUANTITATIVE RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")


def main():
    analyst = AdvancedDataAnalyst()
    report = analyst.run_comprehensive_data_analysis()


if __name__ == "__main__":
    main()
