#!/usr/bin/env python3
"""
VictoryChain Statistical Momentum Analyzer
Uses standard deviation and probability analysis to find optimal trading opportunities
"""

import requests
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from scipy import stats
import statistics


class StatisticalMomentumAnalyzer:
    def __init__(self):
        self.claude_api_key = os.getenv(
            "CLAUDE_API_KEY",
            "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",
        )
        self.binance_us_base = "https://api.binance.us"

    def get_kline_data(
        self, symbol: str, interval: str = "1h", limit: int = 168
    ) -> List[Dict]:
        """Get historical kline data for statistical analysis (168 hours = 7 days)"""
        try:
            url = f"{self.binance_us_base}/api/v3/klines"
            params = {"symbol": symbol, "interval": interval, "limit": limit}

            response = requests.get(url, params=params)
            if response.status_code == 200:
                klines = response.json()
                processed_data = []

                for kline in klines:
                    processed_data.append(
                        {
                            "timestamp": int(kline[0]),
                            "open": float(kline[1]),
                            "high": float(kline[2]),
                            "low": float(kline[3]),
                            "close": float(kline[4]),
                            "volume": float(kline[5]),
                            "returns": 0.0,  # Will calculate later
                        }
                    )

                # Calculate hourly returns
                for i in range(1, len(processed_data)):
                    processed_data[i]["returns"] = (
                        (processed_data[i]["close"] - processed_data[i - 1]["close"])
                        / processed_data[i - 1]["close"]
                    ) * 100

                return processed_data[1:]  # Remove first entry (no return calculated)
            else:
                print(f"Failed to get kline data for {symbol}: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting kline data for {symbol}: {e}")
            return []

    def calculate_statistical_metrics(self, data: List[Dict]) -> Dict:
        """Calculate comprehensive statistical metrics"""
        if len(data) < 20:
            return {}

        returns = [d["returns"] for d in data]
        prices = [d["close"] for d in data]
        volumes = [d["volume"] for d in data]

        # Basic statistics
        mean_return = np.mean(returns)
        std_dev = np.std(returns)
        variance = np.var(returns)

        # Risk-adjusted metrics
        sharpe_ratio = mean_return / std_dev if std_dev > 0 else 0

        # Probability metrics
        positive_returns = [r for r in returns if r > 0]
        win_rate = len(positive_returns) / len(returns)

        # Statistical significance tests
        t_stat, p_value = stats.ttest_1samp(returns, 0)

        # Momentum indicators
        recent_returns = returns[-24:]  # Last 24 hours
        recent_mean = np.mean(recent_returns)
        recent_std = np.std(recent_returns)

        # Z-score for current momentum
        current_z_score = (recent_mean - mean_return) / std_dev if std_dev > 0 else 0

        # Bollinger Band position
        sma_20 = np.mean(prices[-20:])
        bb_upper = sma_20 + (2 * np.std(prices[-20:]))
        bb_lower = sma_20 - (2 * np.std(prices[-20:]))
        current_price = prices[-1]
        bb_position = (
            (current_price - bb_lower) / (bb_upper - bb_lower)
            if bb_upper != bb_lower
            else 0.5
        )

        # Volume analysis
        avg_volume = np.mean(volumes)
        recent_volume = np.mean(volumes[-6:])  # Last 6 hours
        volume_surge = recent_volume / avg_volume if avg_volume > 0 else 1

        # Volatility clustering (GARCH-like)
        squared_returns = [r**2 for r in returns]
        volatility_persistence = (
            np.corrcoef(squared_returns[:-1], squared_returns[1:])[0, 1]
            if len(squared_returns) > 1
            else 0
        )

        # Price momentum
        price_momentum_1h = (
            (prices[-1] - prices[-2]) / prices[-2] * 100 if len(prices) > 1 else 0
        )
        price_momentum_6h = (
            (prices[-1] - prices[-7]) / prices[-7] * 100 if len(prices) > 6 else 0
        )
        price_momentum_24h = (
            (prices[-1] - prices[-25]) / prices[-25] * 100 if len(prices) > 24 else 0
        )

        # Trend strength
        correlation_with_time = np.corrcoef(range(len(prices)), prices)[0, 1]

        return {
            "symbol": data[0].get("symbol", "UNKNOWN"),
            "current_price": current_price,
            "mean_return": mean_return,
            "std_dev": std_dev,
            "variance": variance,
            "sharpe_ratio": sharpe_ratio,
            "win_rate": win_rate,
            "p_value": p_value,
            "statistical_significance": p_value < 0.05,
            "current_z_score": current_z_score,
            "bb_position": bb_position,
            "volume_surge": volume_surge,
            "volatility_persistence": volatility_persistence,
            "price_momentum_1h": price_momentum_1h,
            "price_momentum_6h": price_momentum_6h,
            "price_momentum_24h": price_momentum_24h,
            "trend_strength": correlation_with_time,
            "data_points": len(data),
            "recent_mean_return": recent_mean,
            "recent_std_dev": recent_std,
        }

    def calculate_probability_score(self, metrics: Dict) -> Dict:
        """Calculate probability-based trading score"""
        score = 0
        max_score = 100
        confidence_factors = []

        # Sharpe ratio scoring (0-15 points)
        if metrics["sharpe_ratio"] > 2.0:
            score += 15
            confidence_factors.append("Excellent Sharpe ratio")
        elif metrics["sharpe_ratio"] > 1.0:
            score += 10
            confidence_factors.append("Good Sharpe ratio")
        elif metrics["sharpe_ratio"] > 0.5:
            score += 5
            confidence_factors.append("Moderate Sharpe ratio")

        # Win rate scoring (0-20 points)
        if metrics["win_rate"] > 0.65:
            score += 20
            confidence_factors.append("High win rate")
        elif metrics["win_rate"] > 0.55:
            score += 15
            confidence_factors.append("Good win rate")
        elif metrics["win_rate"] > 0.45:
            score += 10
            confidence_factors.append("Average win rate")

        # Statistical significance (0-10 points)
        if metrics["statistical_significance"]:
            score += 10
            confidence_factors.append("Statistically significant returns")

        # Current momentum Z-score (0-15 points)
        z_score = abs(metrics["current_z_score"])
        if z_score > 2.0 and metrics["current_z_score"] > 0:
            score += 15
            confidence_factors.append("Strong positive momentum")
        elif z_score > 1.5 and metrics["current_z_score"] > 0:
            score += 10
            confidence_factors.append("Good positive momentum")
        elif z_score > 1.0 and metrics["current_z_score"] > 0:
            score += 5
            confidence_factors.append("Moderate positive momentum")

        # Bollinger Band position (0-10 points)
        if 0.2 <= metrics["bb_position"] <= 0.4:  # Near lower band (potential bounce)
            score += 10
            confidence_factors.append("Oversold position")
        elif 0.4 <= metrics["bb_position"] <= 0.6:  # Middle range
            score += 5
            confidence_factors.append("Neutral position")

        # Volume surge (0-10 points)
        if metrics["volume_surge"] > 2.0:
            score += 10
            confidence_factors.append("High volume surge")
        elif metrics["volume_surge"] > 1.5:
            score += 7
            confidence_factors.append("Volume increase")
        elif metrics["volume_surge"] > 1.2:
            score += 3
            confidence_factors.append("Slight volume increase")

        # Price momentum consistency (0-10 points)
        momentum_consistency = 0
        if metrics["price_momentum_1h"] > 0:
            momentum_consistency += 1
        if metrics["price_momentum_6h"] > 0:
            momentum_consistency += 1
        if metrics["price_momentum_24h"] > 0:
            momentum_consistency += 1

        if momentum_consistency == 3:
            score += 10
            confidence_factors.append("Consistent positive momentum")
        elif momentum_consistency == 2:
            score += 6
            confidence_factors.append("Good momentum consistency")
        elif momentum_consistency == 1:
            score += 3
            confidence_factors.append("Some positive momentum")

        # Trend strength (0-10 points)
        if metrics["trend_strength"] > 0.7:
            score += 10
            confidence_factors.append("Strong uptrend")
        elif metrics["trend_strength"] > 0.4:
            score += 6
            confidence_factors.append("Moderate uptrend")
        elif metrics["trend_strength"] > 0.1:
            score += 3
            confidence_factors.append("Weak uptrend")

        # Calculate probability of 20%+ gain
        prob_20_gain = self.estimate_gain_probability(metrics, target_gain=20)
        prob_30_gain = self.estimate_gain_probability(metrics, target_gain=30)

        return {
            "total_score": min(score, max_score),
            "probability_20_gain": prob_20_gain,
            "probability_30_gain": prob_30_gain,
            "confidence_factors": confidence_factors,
            "risk_score": self.calculate_risk_score(metrics),
            "expected_return": metrics["mean_return"] * 24,  # Expected 24h return
            "risk_adjusted_score": (score * prob_20_gain) / 100,
        }

    def estimate_gain_probability(self, metrics: Dict, target_gain: float) -> float:
        """Estimate probability of achieving target gain based on historical data"""
        mean_return = metrics["mean_return"]
        std_dev = metrics["std_dev"]

        if std_dev <= 0:
            return 0

        # Assuming normal distribution of returns
        # Calculate probability of achieving target_gain in next 24 hours
        target_hourly_return = target_gain / 24  # Distribute over 24 hours
        z_score = (target_hourly_return - mean_return) / std_dev

        # Use cumulative distribution function
        probability = (1 - stats.norm.cdf(z_score)) * 100

        # Adjust for momentum factors
        momentum_adjustment = 1.0
        if metrics["current_z_score"] > 1.0:
            momentum_adjustment = 1.2
        elif metrics["current_z_score"] > 0.5:
            momentum_adjustment = 1.1

        # Adjust for volume surge
        volume_adjustment = min(1.0 + (metrics["volume_surge"] - 1.0) * 0.1, 1.3)

        adjusted_probability = min(
            probability * momentum_adjustment * volume_adjustment, 95
        )
        return max(adjusted_probability, 0)

    def calculate_risk_score(self, metrics: Dict) -> float:
        """Calculate risk score (0-100, higher = more risky)"""
        risk_score = 0

        # Volatility risk
        if metrics["std_dev"] > 10:
            risk_score += 30
        elif metrics["std_dev"] > 5:
            risk_score += 20
        elif metrics["std_dev"] > 3:
            risk_score += 10

        # Low win rate risk
        if metrics["win_rate"] < 0.4:
            risk_score += 25
        elif metrics["win_rate"] < 0.5:
            risk_score += 15

        # Negative trend risk
        if metrics["trend_strength"] < -0.3:
            risk_score += 20
        elif metrics["trend_strength"] < 0:
            risk_score += 10

        # Volatility clustering risk
        if metrics["volatility_persistence"] > 0.5:
            risk_score += 15

        # Recent negative momentum
        if metrics["price_momentum_24h"] < -10:
            risk_score += 20
        elif metrics["price_momentum_24h"] < -5:
            risk_score += 10

        return min(risk_score, 100)

    def analyze_all_tokens(self) -> List[Dict]:
        """Analyze all available USDT tokens with statistical methods"""
        print(
            "📊 Statistical Momentum Analysis - Using Standard Deviation & Probability"
        )
        print("=" * 80)

        # Get all USDT symbols
        try:
            response = requests.get(f"{self.binance_us_base}/api/v3/exchangeInfo")
            if response.status_code != 200:
                print("Failed to get exchange info")
                return []

            exchange_info = response.json()
            usdt_symbols = [
                symbol["symbol"]
                for symbol in exchange_info["symbols"]
                if symbol["symbol"].endswith("USDT") and symbol["status"] == "TRADING"
            ]

            print(
                f"🔍 Analyzing {len(usdt_symbols)} USDT pairs with statistical methods..."
            )

        except Exception as e:
            print(f"Error getting symbols: {e}")
            return []

        analyzed_tokens = []

        for i, symbol in enumerate(usdt_symbols):
            try:
                print(f"   [{i+1}/{len(usdt_symbols)}] Analyzing {symbol}...", end=" ")

                # Get historical data
                kline_data = self.get_kline_data(symbol)

                if len(kline_data) < 50:  # Need enough data for analysis
                    print("❌ Insufficient data")
                    continue

                # Add symbol to data
                for d in kline_data:
                    d["symbol"] = symbol

                # Calculate statistical metrics
                metrics = self.calculate_statistical_metrics(kline_data)
                if not metrics:
                    print("❌ Analysis failed")
                    continue

                # Calculate probability scores
                probability_analysis = self.calculate_probability_score(metrics)

                # Combine all analysis
                full_analysis = {**metrics, **probability_analysis}

                # Filter for high-probability opportunities
                if (
                    full_analysis["total_score"] >= 60
                    and full_analysis["probability_20_gain"] >= 15
                    and full_analysis["risk_score"] <= 70
                ):

                    analyzed_tokens.append(full_analysis)
                    print(
                        f"✅ Score: {full_analysis['total_score']}, P(20%): {full_analysis['probability_20_gain']:.1f}%"
                    )
                else:
                    print(f"❌ Low probability")

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                print(f"❌ Error: {e}")
                continue

        # Sort by risk-adjusted score
        analyzed_tokens.sort(key=lambda x: x["risk_adjusted_score"], reverse=True)

        return analyzed_tokens

    def display_analysis_results(self, tokens: List[Dict]):
        """Display comprehensive analysis results"""
        print("\n" + "=" * 100)
        print("🎯 STATISTICAL MOMENTUM ANALYSIS RESULTS")
        print("=" * 100)

        if not tokens:
            print("❌ No tokens meet the statistical probability criteria")
            print("\nCriteria used:")
            print("   • Total Score: ≥60/100")
            print("   • Probability of 20% gain: ≥15%")
            print("   • Risk Score: ≤70/100")
            print("   • Sufficient historical data (50+ data points)")
            return

        print(f"Found {len(tokens)} tokens with optimal statistical profiles:\n")

        for i, token in enumerate(tokens, 1):
            print(f"{i}. {token['symbol']} 📈")
            print(f"   Current Price:        ${token['current_price']:.6f}")
            print(f"   Total Score:          {token['total_score']}/100")
            print(f"   Risk-Adjusted Score:  {token['risk_adjusted_score']:.1f}")
            print(f"   ")
            print(f"   PROBABILITY ANALYSIS:")
            print(f"   Prob. of 20% gain:    {token['probability_20_gain']:.1f}%")
            print(f"   Prob. of 30% gain:    {token['probability_30_gain']:.1f}%")
            print(f"   Expected 24h return:  {token['expected_return']:.2f}%")
            print(f"   ")
            print(f"   STATISTICAL METRICS:")
            print(f"   Standard Deviation:   {token['std_dev']:.3f}")
            print(f"   Sharpe Ratio:         {token['sharpe_ratio']:.3f}")
            print(f"   Win Rate:             {token['win_rate']:.1%}")
            print(f"   Current Z-Score:      {token['current_z_score']:.2f}")
            print(f"   ")
            print(f"   MOMENTUM INDICATORS:")
            print(f"   1h Momentum:          {token['price_momentum_1h']:+.2f}%")
            print(f"   6h Momentum:          {token['price_momentum_6h']:+.2f}%")
            print(f"   24h Momentum:         {token['price_momentum_24h']:+.2f}%")
            print(f"   Volume Surge:         {token['volume_surge']:.2f}x")
            print(f"   ")
            print(f"   RISK ASSESSMENT:")
            print(f"   Risk Score:           {token['risk_score']}/100")
            print(f"   Bollinger Position:   {token['bb_position']:.2f}")
            print(f"   Trend Strength:       {token['trend_strength']:+.3f}")
            print(f"   ")
            print(f"   CONFIDENCE FACTORS:")
            for factor in token["confidence_factors"]:
                print(f"   ✓ {factor}")

            # Risk level
            if token["risk_score"] <= 30:
                risk_level = "🟢 LOW"
            elif token["risk_score"] <= 60:
                risk_level = "🟡 MEDIUM"
            else:
                risk_level = "🔴 HIGH"

            print(f"   Risk Level:           {risk_level}")
            print("-" * 100)

        # Show trading recommendations
        if tokens:
            print("\n💡 STATISTICAL TRADING RECOMMENDATIONS:")

            top_token = tokens[0]
            print(f"\n🥇 TOP PICK: {top_token['symbol']}")
            print(
                f"   • Highest risk-adjusted score: {top_token['risk_adjusted_score']:.1f}"
            )
            print(f"   • {top_token['probability_20_gain']:.1f}% chance of 20% gain")
            print(f"   • Recommended position size: $75-100")

            if len(tokens) >= 2:
                print(f"\n🥈 SECOND CHOICE: {tokens[1]['symbol']}")
                print(
                    f"   • Risk-adjusted score: {tokens[1]['risk_adjusted_score']:.1f}"
                )
                print(
                    f"   • {tokens[1]['probability_20_gain']:.1f}% chance of 20% gain"
                )

            print(f"\n📊 PORTFOLIO ALLOCATION STRATEGY:")
            print(f"   • Diversify across top 2-3 tokens")
            print(f"   • Weight by risk-adjusted scores")
            print(f"   • Use Kelly Criterion for position sizing")
            print(f"   • Set stop losses at 2 standard deviations below entry")

            # Calculate Kelly Criterion for top token
            if top_token["win_rate"] > 0 and top_token["expected_return"] != 0:
                win_rate = top_token["win_rate"]
                avg_win = (
                    abs(top_token["expected_return"])
                    if top_token["expected_return"] > 0
                    else 5
                )
                avg_loss = top_token["std_dev"] * 2  # 2 std dev stop loss

                if avg_loss > 0:
                    kelly_fraction = (
                        win_rate * avg_win - (1 - win_rate) * avg_loss
                    ) / avg_win
                    kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%

                    print(f"\n🎯 KELLY CRITERION POSITION SIZING:")
                    print(
                        f"   • Optimal position size: {kelly_fraction:.1%} of portfolio"
                    )
                    print(f"   • With $237 available: ${237 * kelly_fraction:.2f}")


def main():
    analyzer = StatisticalMomentumAnalyzer()

    print("🔬 VictoryChain Statistical Momentum Analyzer")
    print("Advanced Probability-Based Token Analysis")
    print("Using Standard Deviation, Z-Scores, and Statistical Significance")
    print()

    # Run comprehensive analysis
    results = analyzer.analyze_all_tokens()

    # Display results
    analyzer.display_analysis_results(results)

    print(f"\n⚠️  STATISTICAL DISCLAIMERS:")
    print(f"   • Past performance doesn't guarantee future results")
    print(f"   • Probabilities are estimates based on historical data")
    print(f"   • Market conditions can change rapidly")
    print(f"   • Always use proper risk management")
    print(f"   • This analysis assumes normal distribution of returns")


if __name__ == "__main__":
    main()
