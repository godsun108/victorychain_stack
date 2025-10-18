#!/usr/bin/env python3
"""
VictoryChain Integrated Statistical Momentum Trading System
Combines momentum scanning, statistical analysis, and live trading execution
"""

import requests
import json
import os
import time
import math
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


class IntegratedMomentumTrader:
    def __init__(self):
        self.api_key = os.getenv("BINANCE_US_API_KEY", "")
        self.api_secret = os.getenv("BINANCE_US_SECRET_KEY", "")
        self.claude_api_key = os.getenv("CLAUDE_API_KEY", "")
        self.binance_us_base = "https://api.binance.us"

        # Trading parameters
        self.min_volume_24h = 1000000  # $1M minimum 24h volume
        self.min_price = 0.001  # Minimum price filter
        self.max_spread_percent = 2.0  # Maximum bid-ask spread

    def get_all_trading_pairs(self) -> List[Dict]:
        """Get all active USDT trading pairs with volume filtering"""
        try:
            # Get 24hr ticker data for volume filtering
            ticker_response = requests.get(f"{self.binance_us_base}/api/v3/ticker/24hr")
            if ticker_response.status_code != 200:
                print(f"❌ Failed to get ticker data: {ticker_response.status_code}")
                return []

            tickers = ticker_response.json()

            # Filter for USDT pairs with sufficient volume
            filtered_pairs = []
            for ticker in tickers:
                symbol = ticker["symbol"]
                if (
                    symbol.endswith("USDT")
                    and symbol not in ["USDCUSDT", "TUSDUSDT", "BUSDUSDT"]
                    and float(ticker["quoteVolume"]) >= self.min_volume_24h
                    and float(ticker["lastPrice"]) >= self.min_price
                ):

                    filtered_pairs.append(
                        {
                            "symbol": symbol,
                            "price": float(ticker["lastPrice"]),
                            "volume_24h": float(ticker["quoteVolume"]),
                            "price_change_24h": float(ticker["priceChangePercent"]),
                            "high_24h": float(ticker["highPrice"]),
                            "low_24h": float(ticker["lowPrice"]),
                        }
                    )

            # Sort by volume (liquidity)
            filtered_pairs.sort(key=lambda x: x["volume_24h"], reverse=True)

            print(f"📊 Found {len(filtered_pairs)} liquid USDT pairs")
            return filtered_pairs

        except Exception as e:
            print(f"❌ Error getting trading pairs: {e}")
            return []

    def get_kline_data(
        self, symbol: str, interval: str = "1h", limit: int = 336
    ) -> List[Dict]:
        """Get historical price data for analysis"""
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
                            "returns": 0.0,
                        }
                    )

                # Calculate hourly returns
                for i in range(1, len(processed_data)):
                    price_change = (
                        processed_data[i]["close"] - processed_data[i - 1]["close"]
                    ) / processed_data[i - 1]["close"]
                    processed_data[i]["returns"] = price_change * 100

                return processed_data[1:]  # Remove first entry
            else:
                return []
        except Exception as e:
            print(f"❌ Error getting kline data for {symbol}: {e}")
            return []

    def calculate_statistical_metrics(self, data: List[Dict]) -> Dict:
        """Calculate comprehensive statistical analysis"""
        if len(data) < 50:
            return {}

        returns = [d["returns"] for d in data]
        prices = [d["close"] for d in data]
        volumes = [d["volume"] for d in data]

        # Basic statistics
        mean_return = statistics.mean(returns)
        std_dev = statistics.stdev(returns) if len(returns) > 1 else 0

        # Multi-timeframe analysis
        returns_1h = returns[-1] if returns else 0
        returns_6h = sum(returns[-6:]) if len(returns) >= 6 else 0
        returns_24h = sum(returns[-24:]) if len(returns) >= 24 else 0
        returns_7d = sum(returns[-168:]) if len(returns) >= 168 else 0

        # Volatility at different timeframes
        std_1h = std_dev
        std_6h = statistics.stdev(returns[-6:]) if len(returns) >= 6 else std_dev
        std_24h = statistics.stdev(returns[-24:]) if len(returns) >= 24 else std_dev
        std_7d = statistics.stdev(returns[-168:]) if len(returns) >= 168 else std_dev

        # Momentum indicators (return/volatility ratio)
        momentum_1h = returns_1h / std_1h if std_1h > 0 else 0
        momentum_6h = returns_6h / std_6h if std_6h > 0 else 0
        momentum_24h = returns_24h / std_24h if std_24h > 0 else 0
        momentum_7d = returns_7d / std_7d if std_7d > 0 else 0

        # Risk metrics
        positive_returns = [r for r in returns if r > 0]
        win_rate = len(positive_returns) / len(returns) if returns else 0
        avg_win = statistics.mean(positive_returns) if positive_returns else 0

        negative_returns = [r for r in returns if r < 0]
        avg_loss = statistics.mean(negative_returns) if negative_returns else 0

        # Sharpe ratio
        sharpe_ratio = mean_return / std_dev if std_dev > 0 else 0

        # Price trend
        price_range = list(range(len(prices)))
        trend_correlation = (
            self.calculate_correlation(price_range, prices) if len(prices) > 1 else 0
        )

        return {
            "mean_return": mean_return,
            "std_dev": std_dev,
            "std_1h": std_1h,
            "std_6h": std_6h,
            "std_24h": std_24h,
            "std_7d": std_7d,
            "returns_1h": returns_1h,
            "returns_6h": returns_6h,
            "returns_24h": returns_24h,
            "returns_7d": returns_7d,
            "momentum_1h": momentum_1h,
            "momentum_6h": momentum_6h,
            "momentum_24h": momentum_24h,
            "momentum_7d": momentum_7d,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "sharpe_ratio": sharpe_ratio,
            "trend_correlation": trend_correlation,
            "data_points": len(data),
        }

    def calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0

        n = len(x)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        sum_sq_x = sum((x[i] - mean_x) ** 2 for i in range(n))
        sum_sq_y = sum((y[i] - mean_y) ** 2 for i in range(n))

        denominator = math.sqrt(sum_sq_x * sum_sq_y)
        return numerator / denominator if denominator > 0 else 0

    def normal_cdf_approx(self, x: float) -> float:
        """Approximate normal CDF for probability calculations"""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    def calculate_gain_probability(
        self, metrics: Dict, target_gain: float, hours: int
    ) -> float:
        """Calculate probability of achieving target gain"""
        mean_hourly = metrics["mean_return"]
        std_hourly = metrics["std_dev"]

        if std_hourly <= 0:
            return 0

        required_hourly = target_gain / hours
        z_score = (required_hourly - mean_hourly) / std_hourly

        base_prob = (1 - self.normal_cdf_approx(z_score)) * 100

        # Momentum adjustment
        momentum_adj = 1 + ((metrics["momentum_1h"] + metrics["momentum_6h"]) / 2) * 0.1

        # Trend adjustment
        trend_adj = 1 + metrics["trend_correlation"] * 0.2

        adjusted_prob = base_prob * momentum_adj * trend_adj
        return min(max(adjusted_prob, 0), 95)

    def calculate_composite_score(self, pair_data: Dict, stats: Dict) -> Dict:
        """Calculate composite trading score"""

        # Probability scores
        prob_10_24h = self.calculate_gain_probability(stats, 10, 24)
        prob_20_48h = self.calculate_gain_probability(stats, 20, 48)
        prob_30_72h = self.calculate_gain_probability(stats, 30, 72)

        # Risk-adjusted probabilities
        volatility_penalty = min(stats["std_24h"] / 10, 0.5)
        risk_adj_10 = prob_10_24h * (1 - volatility_penalty)
        risk_adj_20 = prob_20_48h * (1 - volatility_penalty * 1.2)
        risk_adj_30 = prob_30_72h * (1 - volatility_penalty * 1.5)

        # Momentum composite
        momentum_composite = (
            stats["momentum_1h"] * 0.4
            + stats["momentum_6h"] * 0.3
            + stats["momentum_24h"] * 0.2
            + stats["momentum_7d"] * 0.1
        )

        # Volume score (higher volume = better liquidity)
        volume_score = min(pair_data["volume_24h"] / 10000000, 10)  # Scale to 10 max

        # Recent performance
        recent_performance = pair_data["price_change_24h"]

        # Final composite score
        composite = (
            risk_adj_10 * 0.4
            + risk_adj_20 * 0.3
            + risk_adj_30 * 0.2
            + momentum_composite * 5
            + volume_score
            + max(recent_performance, 0) * 0.5
        )

        return {
            "composite_score": min(composite, 100),
            "prob_10_24h": prob_10_24h,
            "prob_20_48h": prob_20_48h,
            "prob_30_72h": prob_30_72h,
            "risk_adj_10": risk_adj_10,
            "risk_adj_20": risk_adj_20,
            "risk_adj_30": risk_adj_30,
            "momentum_composite": momentum_composite,
            "volume_score": volume_score,
            "volatility_penalty": volatility_penalty,
        }

    def analyze_and_rank_tokens(self, max_tokens: int = 30) -> List[Dict]:
        """Main analysis function - get and rank all tokens"""
        print("🔍 Starting comprehensive token analysis...")

        # Get all trading pairs
        pairs = self.get_all_trading_pairs()
        if not pairs:
            return []

        # Limit analysis
        pairs = pairs[:max_tokens]

        results = []

        for i, pair in enumerate(pairs, 1):
            try:
                symbol = pair["symbol"]
                print(f"📊 Analyzing {symbol} ({i}/{len(pairs)})...")

                # Get historical data
                kline_data = self.get_kline_data(symbol)
                if not kline_data:
                    continue

                # Calculate statistical metrics
                stats = self.calculate_statistical_metrics(kline_data)
                if not stats:
                    continue

                # Calculate composite score
                scores = self.calculate_composite_score(pair, stats)

                # Combine all data
                result = {
                    "symbol": symbol,
                    "current_price": pair["price"],
                    "volume_24h": pair["volume_24h"],
                    "price_change_24h": pair["price_change_24h"],
                    **stats,
                    **scores,
                    "analysis_time": datetime.now().isoformat(),
                }

                results.append(result)

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                print(f"❌ Error analyzing {pair['symbol']}: {e}")
                continue

        # Sort by composite score
        results.sort(key=lambda x: x["composite_score"], reverse=True)

        print(
            f"✅ Analysis complete! {len(results)} tokens ranked by statistical probability."
        )
        return results

    def print_analysis_results(self, results: List[Dict], top_n: int = 15):
        """Print detailed analysis results"""
        if not results:
            print("❌ No results to display")
            return

        print(f"\n🏆 TOP {min(top_n, len(results))} STATISTICAL MOMENTUM OPPORTUNITIES")
        print("=" * 140)

        for i, token in enumerate(results[:top_n], 1):
            print(
                f"\n#{i} {token['symbol']} - Composite Score: {token['composite_score']:.1f}/100"
            )
            print(
                f"   💰 Price: ${token['current_price']:.6f} | 24h Change: {token['price_change_24h']:+.2f}% | Volume: ${token['volume_24h']:,.0f}"
            )
            print(
                f"   📊 Gain Probabilities: 10% in 24h: {token['prob_10_24h']:.1f}% | 20% in 48h: {token['prob_20_48h']:.1f}% | 30% in 72h: {token['prob_30_72h']:.1f}%"
            )
            print(
                f"   🎯 Risk-Adjusted: 10%: {token['risk_adj_10']:.1f}% | 20%: {token['risk_adj_20']:.1f}% | 30%: {token['risk_adj_30']:.1f}%"
            )
            print(
                f"   📈 Momentum: 1h: {token['momentum_1h']:.2f} | 6h: {token['momentum_6h']:.2f} | 24h: {token['momentum_24h']:.2f}"
            )
            print(
                f"   📉 Volatility: 1h: {token['std_1h']:.2f}% | 24h: {token['std_24h']:.2f}% | Penalty: {token['volatility_penalty']:.2f}"
            )
            print(
                f"   🔥 Stats: Sharpe: {token['sharpe_ratio']:.2f} | Win Rate: {token['win_rate']:.1%} | Trend: {token['trend_correlation']:.2f}"
            )

    def get_top_token_for_trading(self, results: List[Dict]) -> Optional[Dict]:
        """Get the top-ranked token for trading"""
        if not results:
            return None

        top_token = results[0]

        # Additional safety checks
        if (
            top_token["composite_score"] < 20
            or top_token["volume_24h"] < 500000
            or top_token["std_24h"] > 15
        ):  # Too volatile
            print("⚠️  Top token doesn't meet safety criteria")
            return None

        return top_token

    def save_analysis_results(self, results: List[Dict]) -> str:
        """Save analysis results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"statistical_momentum_analysis_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        return filename


def main():
    """Main execution function"""
    print("🚀 VictoryChain Integrated Statistical Momentum Trading System")
    print("📊 Advanced probability-based token selection with risk analysis")
    print("=" * 90)

    trader = IntegratedMomentumTrader()

    # Perform analysis
    results = trader.analyze_and_rank_tokens(max_tokens=40)

    if results:
        # Print results
        trader.print_analysis_results(results, top_n=15)

        # Get top trading candidate
        top_token = trader.get_top_token_for_trading(results)
        if top_token:
            print(f"\n🎯 RECOMMENDED FOR TRADING: {top_token['symbol']}")
            print(f"   📊 Composite Score: {top_token['composite_score']:.1f}/100")
            print(f"   💰 Current Price: ${top_token['current_price']:.6f}")
            print(f"   📈 20% Gain Probability (48h): {top_token['prob_20_48h']:.1f}%")
            print(f"   🛡️ Risk-Adjusted 20% Prob: {top_token['risk_adj_20']:.1f}%")

        # Save results
        filename = trader.save_analysis_results(results)
        print(f"\n💾 Analysis saved to: {filename}")

        # Summary statistics
        avg_score = statistics.mean([r["composite_score"] for r in results])
        top_5_avg = statistics.mean([r["composite_score"] for r in results[:5]])

        print(f"\n📊 ANALYSIS SUMMARY")
        print(f"   📈 Tokens Analyzed: {len(results)}")
        print(f"   📊 Average Score: {avg_score:.1f}")
        print(f"   🏆 Top 5 Average: {top_5_avg:.1f}")
        print(
            f"   🎯 Best Opportunity: {results[0]['symbol']} ({results[0]['composite_score']:.1f} score)"
        )

    else:
        print("❌ No analysis results generated")


if __name__ == "__main__":
    main()
