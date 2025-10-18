#!/usr/bin/env python3
"""
Statistical Arbitrage & Pairs Trading System
Advanced quantitative trading strategies based on statistical relationships
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
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, coint as sm_coint
from statsmodels.stats.stattools import jarque_bera
from binance.client import Client
from dotenv import load_dotenv

warnings.filterwarnings("ignore")


class StatisticalArbitrageSystem:
    def __init__(self):
        load_dotenv()

        # Initialize Binance client
        self.client = Client(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCEUS_SECRET"),
            tld="us",
        )

        print("📊 Statistical Arbitrage System initialized")
        print("🔍 Loading pairs trading and statistical models...")

    def get_price_data(
        self, symbols: List[str], interval: str = "1h", limit: int = 200
    ) -> Dict:
        """Get price data for multiple symbols"""

        print(f"📈 Gathering price data for {len(symbols)} symbols...")

        price_data = {}

        for symbol in symbols:
            try:
                klines = self.client.get_klines(
                    symbol=symbol, interval=interval, limit=limit
                )

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

                df["close"] = pd.to_numeric(df["close"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df.set_index("timestamp", inplace=True)

                price_data[symbol] = df["close"]

                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                print(f"❌ Failed to get data for {symbol}: {str(e)}")
                continue

        print(f"✅ Successfully gathered data for {len(price_data)} symbols")
        return price_data

    def find_cointegrated_pairs(
        self, price_data: Dict, significance_level: float = 0.05
    ) -> List[Dict]:
        """Find cointegrated pairs using statistical tests"""

        print("🔍 Searching for cointegrated pairs...")

        symbols = list(price_data.keys())
        cointegrated_pairs = []

        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                symbol1, symbol2 = symbols[i], symbols[j]

                try:
                    # Get aligned price series
                    prices1 = price_data[symbol1].dropna()
                    prices2 = price_data[symbol2].dropna()

                    # Align series
                    common_index = prices1.index.intersection(prices2.index)
                    if len(common_index) < 50:
                        continue

                    p1 = prices1.loc[common_index]
                    p2 = prices2.loc[common_index]

                    # Test for cointegration
                    score, p_value, _ = sm_coint(p1, p2)

                    if p_value < significance_level:
                        # Calculate additional statistics
                        correlation = p1.corr(p2)

                        # Linear regression to get hedge ratio
                        X = sm.add_constant(p2)
                        model = sm.OLS(p1, X).fit()
                        hedge_ratio = model.params[1]

                        # Calculate spread
                        spread = p1 - hedge_ratio * p2
                        spread_mean = spread.mean()
                        spread_std = spread.std()

                        # Test spread for stationarity
                        adf_stat, adf_p_value, _, _, _, _ = adfuller(spread.dropna())
                        is_stationary = adf_p_value < 0.05

                        if is_stationary:
                            cointegrated_pairs.append(
                                {
                                    "symbol1": symbol1,
                                    "symbol2": symbol2,
                                    "cointegration_score": float(score),
                                    "p_value": float(p_value),
                                    "correlation": float(correlation),
                                    "hedge_ratio": float(hedge_ratio),
                                    "spread_mean": float(spread_mean),
                                    "spread_std": float(spread_std),
                                    "adf_statistic": float(adf_stat),
                                    "adf_p_value": float(adf_p_value),
                                    "is_stationary": is_stationary,
                                    "r_squared": float(model.rsquared),
                                }
                            )

                except Exception as e:
                    continue

        # Sort by cointegration strength (lower p-value is better)
        cointegrated_pairs.sort(key=lambda x: x["p_value"])

        print(f"✅ Found {len(cointegrated_pairs)} cointegrated pairs")
        return cointegrated_pairs

    def calculate_z_scores(self, price_data: Dict, pairs: List[Dict]) -> Dict:
        """Calculate z-scores for pair spreads"""

        print("📊 Calculating z-scores for pairs...")

        z_scores = {}

        for pair in pairs:
            try:
                symbol1 = pair["symbol1"]
                symbol2 = pair["symbol2"]
                hedge_ratio = pair["hedge_ratio"]

                # Get current prices
                p1 = price_data[symbol1].dropna()
                p2 = price_data[symbol2].dropna()

                # Align series
                common_index = p1.index.intersection(p2.index)
                p1_aligned = p1.loc[common_index]
                p2_aligned = p2.loc[common_index]

                # Calculate spread
                spread = p1_aligned - hedge_ratio * p2_aligned

                # Calculate rolling statistics
                window = min(50, len(spread) // 4)
                rolling_mean = spread.rolling(window=window).mean()
                rolling_std = spread.rolling(window=window).std()

                # Calculate z-score
                z_score = (spread - rolling_mean) / rolling_std

                current_z_score = (
                    z_score.iloc[-1]
                    if not z_score.empty and not pd.isna(z_score.iloc[-1])
                    else 0
                )

                z_scores[f"{symbol1}_{symbol2}"] = {
                    "current_z_score": float(current_z_score),
                    "current_spread": float(spread.iloc[-1]) if not spread.empty else 0,
                    "spread_mean": (
                        float(rolling_mean.iloc[-1])
                        if not rolling_mean.empty and not pd.isna(rolling_mean.iloc[-1])
                        else 0
                    ),
                    "spread_std": (
                        float(rolling_std.iloc[-1])
                        if not rolling_std.empty and not pd.isna(rolling_std.iloc[-1])
                        else 1
                    ),
                    "z_score_history": z_score.tail(10).fillna(0).tolist(),
                    "spread_history": spread.tail(10).tolist(),
                }

            except Exception as e:
                print(
                    f"❌ Failed to calculate z-score for {pair['symbol1']}_{pair['symbol2']}: {str(e)}"
                )
                continue

        print(f"✅ Calculated z-scores for {len(z_scores)} pairs")
        return z_scores

    def generate_pairs_trading_signals(
        self,
        pairs: List[Dict],
        z_scores: Dict,
        entry_threshold: float = 2.0,
        exit_threshold: float = 0.5,
    ) -> List[Dict]:
        """Generate pairs trading signals based on z-scores"""

        print("🚨 Generating pairs trading signals...")

        signals = []

        for pair in pairs:
            try:
                pair_key = f"{pair['symbol1']}_{pair['symbol2']}"

                if pair_key not in z_scores:
                    continue

                z_data = z_scores[pair_key]
                current_z = z_data["current_z_score"]

                # Determine signal
                signal_type = "HOLD"
                confidence = 0.0
                action_plan = []

                if abs(current_z) > entry_threshold:
                    if current_z > entry_threshold:
                        # Spread is high - short spread (sell symbol1, buy symbol2)
                        signal_type = "SHORT_SPREAD"
                        confidence = min(abs(current_z) / entry_threshold, 3.0) / 3.0
                        action_plan = [
                            f"SELL {pair['symbol1']}",
                            f"BUY {pair['symbol2']} (ratio: {pair['hedge_ratio']:.4f})",
                        ]
                    elif current_z < -entry_threshold:
                        # Spread is low - long spread (buy symbol1, sell symbol2)
                        signal_type = "LONG_SPREAD"
                        confidence = min(abs(current_z) / entry_threshold, 3.0) / 3.0
                        action_plan = [
                            f"BUY {pair['symbol1']}",
                            f"SELL {pair['symbol2']} (ratio: {pair['hedge_ratio']:.4f})",
                        ]

                elif abs(current_z) < exit_threshold:
                    # Close to mean - exit signal
                    signal_type = "EXIT"
                    confidence = 1.0 - abs(current_z) / exit_threshold
                    action_plan = ["Close existing positions"]

                if signal_type != "HOLD":
                    signals.append(
                        {
                            "pair": pair_key,
                            "symbol1": pair["symbol1"],
                            "symbol2": pair["symbol2"],
                            "signal": signal_type,
                            "confidence": float(confidence),
                            "current_z_score": float(current_z),
                            "entry_threshold": entry_threshold,
                            "exit_threshold": exit_threshold,
                            "hedge_ratio": pair["hedge_ratio"],
                            "correlation": pair["correlation"],
                            "p_value": pair["p_value"],
                            "action_plan": action_plan,
                            "spread_info": {
                                "current_spread": z_data["current_spread"],
                                "spread_mean": z_data["spread_mean"],
                                "spread_std": z_data["spread_std"],
                            },
                        }
                    )

            except Exception as e:
                continue

        # Sort by confidence
        signals.sort(key=lambda x: x["confidence"], reverse=True)

        print(f"✅ Generated {len(signals)} pairs trading signals")
        return signals

    def find_statistical_anomalies(self, price_data: Dict) -> List[Dict]:
        """Find statistical anomalies in price movements"""

        print("🔍 Searching for statistical anomalies...")

        anomalies = []

        for symbol, prices in price_data.items():
            try:
                # Calculate returns
                returns = prices.pct_change().dropna()

                if len(returns) < 30:
                    continue

                # Statistical tests
                mean_return = returns.mean()
                std_return = returns.std()
                skewness = returns.skew()
                kurt = returns.kurtosis()

                # Jarque-Bera test for normality
                jb_stat, jb_p_value = jarque_bera(returns)

                # Recent unusual movements
                recent_returns = returns.tail(5)
                recent_z_scores = (recent_returns - mean_return) / std_return
                max_recent_z = abs(recent_z_scores).max()

                # Check for anomalies
                anomaly_score = 0
                anomaly_reasons = []

                # Extreme recent movement
                if max_recent_z > 3:
                    anomaly_score += 0.4
                    anomaly_reasons.append(
                        f"Extreme recent movement (z-score: {max_recent_z:.2f})"
                    )

                # Non-normal distribution
                if jb_p_value < 0.01:
                    anomaly_score += 0.2
                    anomaly_reasons.append("Non-normal return distribution")

                # High volatility
                current_vol = returns.tail(10).std()
                historical_vol = returns.std()
                if current_vol > historical_vol * 2:
                    anomaly_score += 0.3
                    anomaly_reasons.append("Elevated volatility")

                # Extreme skewness
                if abs(skewness) > 2:
                    anomaly_score += 0.1
                    anomaly_reasons.append(f"Extreme skewness: {skewness:.2f}")

                if anomaly_score > 0.3:
                    anomalies.append(
                        {
                            "symbol": symbol,
                            "anomaly_score": float(anomaly_score),
                            "reasons": anomaly_reasons,
                            "current_price": float(prices.iloc[-1]),
                            "recent_change": (
                                float(returns.tail(1).iloc[0])
                                if not returns.empty
                                else 0
                            ),
                            "max_recent_z_score": float(max_recent_z),
                            "statistics": {
                                "mean_return": float(mean_return),
                                "volatility": float(std_return),
                                "skewness": float(skewness),
                                "kurtosis": float(kurt),
                                "jb_p_value": float(jb_p_value),
                            },
                        }
                    )

            except Exception as e:
                continue

        # Sort by anomaly score
        anomalies.sort(key=lambda x: x["anomaly_score"], reverse=True)

        print(f"✅ Found {len(anomalies)} statistical anomalies")
        return anomalies

    def perform_mean_reversion_analysis(self, price_data: Dict) -> Dict:
        """Perform mean reversion analysis"""

        print("🔄 Performing mean reversion analysis...")

        mean_reversion_candidates = []

        for symbol, prices in price_data.items():
            try:
                # Calculate various moving averages
                ma_20 = prices.rolling(window=20).mean()
                ma_50 = prices.rolling(window=50).mean()

                # Calculate distance from moving averages
                distance_ma20 = (prices - ma_20) / ma_20
                distance_ma50 = (prices - ma_50) / ma_50

                current_distance_20 = (
                    distance_ma20.iloc[-1] if not pd.isna(distance_ma20.iloc[-1]) else 0
                )
                current_distance_50 = (
                    distance_ma50.iloc[-1] if not pd.isna(distance_ma50.iloc[-1]) else 0
                )

                # Calculate Bollinger Bands
                bb_middle = prices.rolling(window=20).mean()
                bb_std = prices.rolling(window=20).std()
                bb_upper = bb_middle + (bb_std * 2)
                bb_lower = bb_middle - (bb_std * 2)

                current_price = prices.iloc[-1]
                bb_position = (current_price - bb_lower.iloc[-1]) / (
                    bb_upper.iloc[-1] - bb_lower.iloc[-1]
                )

                # Mean reversion signals
                reversion_score = 0
                signals = []

                # Distance from MA20
                if abs(current_distance_20) > 0.1:
                    reversion_score += min(abs(current_distance_20) * 5, 1.0)
                    signals.append(f"Distance from MA20: {current_distance_20:.1%}")

                # Bollinger Bands position
                if bb_position < 0.1 or bb_position > 0.9:
                    reversion_score += 0.5
                    signals.append(f"BB extreme position: {bb_position:.2f}")

                # RSI calculation
                returns = prices.pct_change()
                delta = returns.dropna()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))

                current_rsi = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

                if current_rsi < 30 or current_rsi > 70:
                    reversion_score += 0.4
                    signals.append(f"RSI extreme: {current_rsi:.1f}")

                if reversion_score > 0.5:
                    direction = (
                        "BULLISH"
                        if current_distance_20 < -0.05 or bb_position < 0.2
                        else "BEARISH"
                    )

                    mean_reversion_candidates.append(
                        {
                            "symbol": symbol,
                            "reversion_score": float(reversion_score),
                            "direction": direction,
                            "signals": signals,
                            "current_price": float(current_price),
                            "distance_ma20": float(current_distance_20),
                            "distance_ma50": float(current_distance_50),
                            "bb_position": float(bb_position),
                            "rsi": float(current_rsi),
                            "ma20": (
                                float(ma_20.iloc[-1])
                                if not pd.isna(ma_20.iloc[-1])
                                else float(current_price)
                            ),
                            "ma50": (
                                float(ma_50.iloc[-1])
                                if not pd.isna(ma_50.iloc[-1])
                                else float(current_price)
                            ),
                        }
                    )

            except Exception as e:
                continue

        # Sort by reversion score
        mean_reversion_candidates.sort(key=lambda x: x["reversion_score"], reverse=True)

        print(f"✅ Found {len(mean_reversion_candidates)} mean reversion candidates")

        return {
            "candidates": mean_reversion_candidates,
            "summary": {
                "total_candidates": len(mean_reversion_candidates),
                "bullish_candidates": len(
                    [
                        c
                        for c in mean_reversion_candidates
                        if c["direction"] == "BULLISH"
                    ]
                ),
                "bearish_candidates": len(
                    [
                        c
                        for c in mean_reversion_candidates
                        if c["direction"] == "BEARISH"
                    ]
                ),
            },
        }

    def run_complete_statistical_arbitrage(self, symbols: List[str] = None) -> Dict:
        """Run complete statistical arbitrage analysis"""

        print("🚀 Starting Statistical Arbitrage Analysis...")

        if symbols is None:
            # Get all tradable USDT symbols
            exchange_info = self.client.get_exchange_info()
            symbols = [
                s["symbol"]
                for s in exchange_info["symbols"]
                if s["symbol"].endswith("USDT") and s["status"] == "TRADING"
            ]
            symbols = symbols[:50]  # Limit for computational efficiency

        print(f"📊 Analyzing {len(symbols)} symbols for statistical arbitrage...")

        # Get price data
        price_data = self.get_price_data(symbols)

        if len(price_data) < 5:
            print("❌ Insufficient price data")
            return {}

        # Find cointegrated pairs
        cointegrated_pairs = self.find_cointegrated_pairs(price_data)

        # Calculate z-scores
        z_scores = {}
        if cointegrated_pairs:
            z_scores = self.calculate_z_scores(price_data, cointegrated_pairs)

        # Generate pairs trading signals
        pairs_signals = []
        if cointegrated_pairs and z_scores:
            pairs_signals = self.generate_pairs_trading_signals(
                cointegrated_pairs, z_scores
            )

        # Find statistical anomalies
        anomalies = self.find_statistical_anomalies(price_data)

        # Mean reversion analysis
        mean_reversion = self.perform_mean_reversion_analysis(price_data)

        # Compile results
        results = {
            "analysis_timestamp": datetime.now().isoformat(),
            "symbols_analyzed": list(price_data.keys()),
            "cointegrated_pairs": cointegrated_pairs,
            "z_scores": z_scores,
            "pairs_trading_signals": pairs_signals,
            "statistical_anomalies": anomalies,
            "mean_reversion_analysis": mean_reversion,
            "summary": {
                "total_symbols": len(price_data),
                "cointegrated_pairs_found": len(cointegrated_pairs),
                "active_pairs_signals": len(pairs_signals),
                "statistical_anomalies": len(anomalies),
                "mean_reversion_candidates": len(mean_reversion.get("candidates", [])),
            },
        }

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"statistical_arbitrage_analysis_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"✅ Statistical Arbitrage Analysis completed!")
        print(f"📁 Results saved to: {filename}")
        print(f"📊 Analyzed {len(price_data)} symbols")
        print(f"🔗 Found {len(cointegrated_pairs)} cointegrated pairs")
        print(f"🚨 Generated {len(pairs_signals)} pairs trading signals")
        print(f"⚠️  Detected {len(anomalies)} statistical anomalies")
        print(
            f"🔄 Found {len(mean_reversion.get('candidates', []))} mean reversion opportunities"
        )

        return results

    def print_top_opportunities(self, results: Dict):
        """Print top statistical arbitrage opportunities"""

        print("\n" + "=" * 80)
        print("📊 STATISTICAL ARBITRAGE OPPORTUNITIES")
        print("=" * 80)

        # Top pairs trading signals
        pairs_signals = results.get("pairs_trading_signals", [])
        if pairs_signals:
            print("\n🔗 TOP PAIRS TRADING SIGNALS:")
            for i, signal in enumerate(pairs_signals[:5], 1):
                print(f"  {i}. {signal['pair']} - {signal['signal']}")
                print(
                    f"     Z-Score: {signal['current_z_score']:.2f}, Confidence: {signal['confidence']:.1%}"
                )
                print(f"     Action: {', '.join(signal['action_plan'])}")
                print()

        # Top anomalies
        anomalies = results.get("statistical_anomalies", [])
        if anomalies:
            print("\n⚠️  TOP STATISTICAL ANOMALIES:")
            for i, anomaly in enumerate(anomalies[:5], 1):
                print(
                    f"  {i}. {anomaly['symbol']} - Score: {anomaly['anomaly_score']:.2f}"
                )
                print(
                    f"     Price: ${anomaly['current_price']:.4f}, Change: {anomaly['recent_change']:.2%}"
                )
                print(f"     Reasons: {', '.join(anomaly['reasons'])}")
                print()

        # Top mean reversion candidates
        mean_reversion = results.get("mean_reversion_analysis", {}).get(
            "candidates", []
        )
        if mean_reversion:
            print("\n🔄 TOP MEAN REVERSION CANDIDATES:")
            for i, candidate in enumerate(mean_reversion[:5], 1):
                print(f"  {i}. {candidate['symbol']} - {candidate['direction']}")
                print(
                    f"     Score: {candidate['reversion_score']:.2f}, RSI: {candidate['rsi']:.1f}"
                )
                print(f"     Distance from MA20: {candidate['distance_ma20']:.1%}")
                print(f"     Signals: {', '.join(candidate['signals'])}")
                print()


def main():
    """Main execution function"""

    print("📊 STATISTICAL ARBITRAGE & PAIRS TRADING SYSTEM 📊")
    print("=" * 70)

    system = StatisticalArbitrageSystem()

    # Run complete analysis
    results = system.run_complete_statistical_arbitrage()

    if results:
        system.print_top_opportunities(results)

    print("\n🎉 Statistical arbitrage analysis complete!")


if __name__ == "__main__":
    main()
