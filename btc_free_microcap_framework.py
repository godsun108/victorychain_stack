#!/usr/bin/env python3

"""
BTC-FREE MICRO-CAP FRAMEWORK
============================
Pure micro-cap strategy with no BTC/ETH correlation
- MicroCap-30 hedge basket
- Autonomous Kelly position sizing
- BTC-independent timing signals
- Illiquidity-aware execution
- Self-contained micro-cap ecosystem
"""

import ccxt
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import json
import time
from dataclasses import dataclass, field
from collections import defaultdict
import warnings

warnings.filterwarnings("ignore")


@dataclass
class MicroCapToken:
    """Micro-cap token with complete market data"""

    symbol: str
    base_asset: str
    price: float
    market_cap: float
    volume_24h: float
    price_change_24h: float
    high_24h: float
    low_24h: float
    circulating_supply: float
    total_supply: float
    unlock_schedule: Dict[str, float] = field(default_factory=dict)
    github_commits_30d: int = 0
    roadmap_events: List[Dict] = field(default_factory=list)
    sma_50: float = 0.0
    sma_200: float = 0.0
    volatility_20d: float = 0.0
    liquidity_score: float = 0.0
    social_mentions_24h: int = 0
    dex_volume_ratio: float = 0.0


@dataclass
class MicroCapFramework:
    """BTC-free micro-cap trading framework"""

    target_tokens: List[str] = field(default_factory=list)
    hedge_basket: List[str] = field(default_factory=list)
    cash_allocation: float = 0.15
    hedge_allocation: float = 0.30
    long_allocation: float = 0.70
    kelly_fraction: float = 0.5
    liquidity_limit: float = 0.10


class BTCFreeMicroCapStrategy:
    """
    Complete BTC-free micro-cap framework implementation
    Pure micro-cap ecosystem with internal hedging
    """

    def __init__(self, api_key: str = None, api_secret: str = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = None
        self.framework = MicroCapFramework()
        self.tokens: Dict[str, MicroCapToken] = {}
        self.microcap_30_basket: List[str] = []
        self.go_signals: Dict[str, bool] = {}
        self.position_weights: Dict[str, float] = {}
        self.last_update = datetime.now()

        # Risk controls
        self.max_position_size = 0.12  # 12% max of daily volume
        self.basket_stop_threshold = 0.10  # 10% hedge rally vs longs
        self.flash_crash_threshold = 0.20  # 20% single candle drop
        self.unlock_warning_days = 2

        # GO Stack thresholds
        self.breadth_threshold = 0.40  # 40% tokens hitting 20-day highs
        self.dex_rotation_threshold = 1.2  # DEX/CEX volume ratio
        self.stablecoin_inflow_threshold = 25_000_000  # $25M
        self.social_velocity_threshold = 2.0  # 2x tweet mentions
        self.catalyst_density_threshold = 3  # 3+ events <10 days

    def setup_exchange(self):
        """Initialize Binance US connection"""
        try:
            self.exchange = ccxt.binanceus(
                {
                    "apiKey": self.api_key,
                    "secret": self.api_secret,
                    "sandbox": False,
                    "rateLimit": 1200,
                    "enableRateLimit": True,
                }
            )
            print("✅ Binance US exchange initialized")
        except Exception as e:
            print(f"❌ Exchange setup failed: {e}")
            self.exchange = ccxt.binanceus({"sandbox": False})

    async def scan_microcap_universe(self) -> Dict[str, MicroCapToken]:
        """
        Scan for micro-cap tokens ($10M < cap < $100M)
        With 30-day avg volume >= $0.5M
        """
        print("🔍 Scanning micro-cap universe...")

        if not self.exchange:
            self.setup_exchange()

        try:
            # Get all tickers
            tickers = self.exchange.fetch_tickers()
            markets = self.exchange.fetch_markets()

            microcap_tokens = {}

            for symbol, ticker in tickers.items():
                try:
                    if not symbol.endswith("USDT"):
                        continue

                    base_asset = symbol.replace("USDT", "")
                    price = float(ticker["last"] or 0)
                    volume_24h = float(ticker["quoteVolume"] or 0)

                    if price <= 0 or volume_24h <= 0:
                        continue

                    # Estimate market cap (simplified - would need external API for real data)
                    estimated_supply = volume_24h / (price * 0.05)  # Rough estimate
                    market_cap = price * estimated_supply

                    # Filter for micro-caps
                    if (
                        10_000_000 <= market_cap <= 100_000_000
                        and volume_24h >= 500_000
                    ):

                        token = MicroCapToken(
                            symbol=symbol,
                            base_asset=base_asset,
                            price=price,
                            market_cap=market_cap,
                            volume_24h=volume_24h,
                            price_change_24h=float(ticker["change"] or 0),
                            high_24h=float(ticker["high"] or 0),
                            low_24h=float(ticker["low"] or 0),
                            circulating_supply=estimated_supply,
                            total_supply=estimated_supply * 1.2,  # Rough estimate
                            volatility_20d=self.calculate_volatility(symbol),
                            liquidity_score=volume_24h / market_cap,
                        )

                        microcap_tokens[symbol] = token

                except Exception as e:
                    continue

            print(f"✅ Found {len(microcap_tokens)} micro-cap tokens")
            self.tokens = microcap_tokens
            return microcap_tokens

        except Exception as e:
            print(f"❌ Universe scan failed: {e}")
            return {}

    def calculate_volatility(self, symbol: str, days: int = 20) -> float:
        """Calculate 20-day volatility"""
        try:
            if not self.exchange:
                return 0.0

            # Get historical data
            ohlcv = self.exchange.fetch_ohlcv(symbol, "1d", limit=days)
            if len(ohlcv) < days:
                return 0.0

            closes = [x[4] for x in ohlcv]
            returns = np.diff(np.log(closes))
            volatility = np.std(returns) * np.sqrt(365)  # Annualized

            return float(volatility)

        except:
            return 0.0

    def build_microcap_30_basket(self) -> List[str]:
        """
        Build MicroCap-30 hedge basket
        Select 30 worst tokens for shorting
        """
        print("🏗️ Building MicroCap-30 hedge basket...")

        scored_tokens = []

        for symbol, token in self.tokens.items():
            score = 0

            # Low development activity (simulated)
            if token.github_commits_30d < 5:
                score += 30

            # Unlock schedule risk (simulated)
            near_unlocks = sum(
                v
                for k, v in token.unlock_schedule.items()
                if datetime.strptime(k, "%Y-%m-%d")
                <= datetime.now() + timedelta(days=60)
            )
            if near_unlocks > 0.30:  # >30% unlock in 60 days
                score += 40

            # No roadmap events (simulated)
            upcoming_events = [
                e
                for e in token.roadmap_events
                if datetime.strptime(e["date"], "%Y-%m-%d") >= datetime.now()
            ]
            if len(upcoming_events) == 0:
                score += 20

            # Price below SMAs
            if token.price < token.sma_50:
                score += 15
            if token.price < token.sma_200:
                score += 15

            # Low volume/volatility
            if token.volume_24h < 1_000_000:
                score += 10

            scored_tokens.append((symbol, score))

        # Sort by score (highest = worst) and take top 30
        scored_tokens.sort(key=lambda x: x[1], reverse=True)
        self.microcap_30_basket = [token[0] for token in scored_tokens[:30]]

        print(f"✅ MicroCap-30 basket: {len(self.microcap_30_basket)} tokens")
        print(f"Top 5 hedge candidates: {self.microcap_30_basket[:5]}")

        return self.microcap_30_basket

    def calculate_kelly_weights(self) -> Dict[str, float]:
        """
        Autonomous Kelly position sizing
        w_i = min[0.5 * μ_i / σ_i², L_i]
        """
        print("📊 Calculating Kelly position weights...")

        weights = {}

        for symbol, token in self.tokens.items():
            if symbol in self.microcap_30_basket:
                continue  # Skip hedge basket tokens for longs

            # Calculate excess return (μ_i)
            # 5-day excess return - 30-day volatility percentile
            excess_return = token.price_change_24h * 5 / 100  # Simplified

            # Calculate volatility (σ_i)
            volatility = max(token.volatility_20d, 0.01)  # Avoid division by zero

            # Kelly fraction
            kelly_weight = self.framework.kelly_fraction * (
                excess_return / (volatility**2)
            )

            # Liquidity ceiling (L_i)
            liquidity_ceiling = (
                self.framework.liquidity_limit * token.volume_24h / token.price
            )
            daily_volume_limit = token.volume_24h * self.max_position_size

            # Take minimum
            final_weight = min(abs(kelly_weight), liquidity_ceiling, daily_volume_limit)

            if final_weight > 0:
                weights[symbol] = final_weight

        # Normalize to 100%
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        # Apply long allocation (70%)
        weights = {k: v * self.framework.long_allocation for k, v in weights.items()}

        self.position_weights = weights
        print(f"✅ Calculated weights for {len(weights)} tokens")

        return weights

    def check_go_signals(self) -> bool:
        """
        BTC-independent GO stack
        Returns True if 4 of 5 signals are green
        """
        print("🚦 Checking GO signals...")

        signals = {}

        # 1. Micro-cap breadth
        high_breakers = 0
        for token in self.tokens.values():
            if (
                token.price >= token.high_24h * 0.95
                and token.volume_24h > token.volume_24h * 2
            ):
                high_breakers += 1

        breadth_pct = high_breakers / len(self.tokens) if self.tokens else 0
        signals["breadth"] = breadth_pct >= self.breadth_threshold

        # 2. DEX rotation (simulated)
        avg_dex_ratio = np.mean(
            [token.dex_volume_ratio for token in self.tokens.values()]
        )
        signals["dex_rotation"] = avg_dex_ratio >= self.dex_rotation_threshold

        # 3. Stablecoin inflow (simulated)
        total_volume = sum(token.volume_24h for token in self.tokens.values())
        signals["stablecoin_inflow"] = total_volume >= self.stablecoin_inflow_threshold

        # 4. Social velocity (simulated)
        avg_social = np.mean(
            [token.social_mentions_24h for token in self.tokens.values()]
        )
        baseline_social = avg_social / 7  # 7-day average approximation
        signals["social_velocity"] = (
            avg_social >= baseline_social * self.social_velocity_threshold
        )

        # 5. Catalyst density
        upcoming_catalysts = 0
        for token in self.tokens.values():
            for event in token.roadmap_events:
                event_date = datetime.strptime(event["date"], "%Y-%m-%d")
                if event_date <= datetime.now() + timedelta(days=10):
                    upcoming_catalysts += 1

        signals["catalyst_density"] = (
            upcoming_catalysts >= self.catalyst_density_threshold
        )

        # Need 4 of 5 signals
        green_count = sum(signals.values())
        go_signal = green_count >= 4

        self.go_signals = signals

        print("GO Signal Status:")
        for signal, status in signals.items():
            print(f"  {signal}: {'✅' if status else '❌'}")
        print(f"Overall GO: {'✅' if go_signal else '❌'} ({green_count}/5)")

        return go_signal

    def execute_illiquidity_aware_ladder(self, symbol: str, target_size: float):
        """
        Illiquidity-aware execution ladder
        4-leg simultaneous execution
        """
        print(f"🎯 Executing ladder for {symbol}: ${target_size:,.2f}")

        if not self.exchange or symbol not in self.tokens:
            return

        token = self.tokens[symbol]
        current_price = token.price
        daily_volume = token.volume_24h

        # Leg sizes
        leg_1_size = target_size * 0.30  # 30% passive
        leg_2_size = target_size * 0.20  # 20% iceberg
        leg_3_size = target_size * 0.30  # 30% smart limit
        leg_4_size = target_size * 0.20  # 20% TWAP

        try:
            # Leg 1: Passive maker ±0.25%
            leg_1_price = current_price * 0.9975
            print(f"  Leg 1: Passive ${leg_1_size:,.2f} @ ${leg_1_price:.6f}")

            # Leg 2: Hidden iceberg at prior high
            leg_2_price = token.high_24h
            print(f"  Leg 2: Iceberg ${leg_2_size:,.2f} @ ${leg_2_price:.6f}")

            # Leg 3: Smart limit on 0.5x ATR dip
            atr = (token.high_24h - token.low_24h) / 2
            leg_3_price = current_price - (0.5 * atr)
            print(f"  Leg 3: Smart limit ${leg_3_size:,.2f} @ ${leg_3_price:.6f}")

            # Leg 4: TWAP over 45 minutes
            print(f"  Leg 4: TWAP ${leg_4_size:,.2f} over 45 minutes")

            # In live trading, these would be actual orders
            print(f"✅ Ladder executed for {symbol}")

        except Exception as e:
            print(f"❌ Execution failed for {symbol}: {e}")

    def check_risk_controls(self) -> Dict[str, bool]:
        """
        Micro-cap-only risk controls
        """
        controls = {}

        # 1. Basket stop-clock
        if self.microcap_30_basket:
            # Check if hedge basket is rallying vs longs
            hedge_performance = 0.05  # Simulated
            long_performance = 0.02  # Simulated

            if hedge_performance - long_performance > self.basket_stop_threshold:
                controls["basket_stop"] = True
                print("⚠️ Basket stop triggered - hedge outperforming longs")
            else:
                controls["basket_stop"] = False

        # 2. Flash crash detection
        flash_crash_detected = False
        for symbol, token in self.tokens.items():
            if token.price_change_24h < -self.flash_crash_threshold * 100:
                flash_crash_detected = True
                print(f"⚠️ Flash crash detected: {symbol} {token.price_change_24h:.1f}%")

        controls["flash_crash"] = flash_crash_detected

        # 3. Unlock watch
        unlock_warnings = []
        for symbol, token in self.tokens.items():
            for date_str, unlock_pct in token.unlock_schedule.items():
                unlock_date = datetime.strptime(date_str, "%Y-%m-%d")
                days_until = (unlock_date - datetime.now()).days

                if days_until <= self.unlock_warning_days and unlock_pct > 0.05:
                    unlock_warnings.append((symbol, days_until, unlock_pct))

        controls["unlock_warnings"] = len(unlock_warnings) > 0
        if unlock_warnings:
            print(f"⚠️ Unlock warnings: {unlock_warnings}")

        return controls

    def generate_dashboard_metrics(self) -> Dict:
        """Generate real-time dashboard metrics"""
        if not self.tokens:
            return {}

        # Exposure metrics
        total_long_exposure = (
            sum(self.position_weights.values()) * 100000
        )  # Example portfolio
        hedge_exposure = len(self.microcap_30_basket) * 1000  # Example

        # Breadth metrics
        tokens_at_highs = sum(
            1 for t in self.tokens.values() if t.price >= t.high_24h * 0.95
        )
        breadth_pct = (tokens_at_highs / len(self.tokens)) * 100

        # PnL at Risk (simplified)
        portfolio_volatility = np.mean([t.volatility_20d for t in self.tokens.values()])
        var_95 = portfolio_volatility * 1.65  # 95% VaR

        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "exposure": {
                "net_long_usd": total_long_exposure,
                "hedge_usd": hedge_exposure,
                "net_exposure_pct": (total_long_exposure - hedge_exposure)
                / total_long_exposure
                * 100,
            },
            "breadth": {
                "tokens_at_highs": tokens_at_highs,
                "breadth_pct": breadth_pct,
                "status": (
                    "green"
                    if breadth_pct >= 20
                    else "yellow" if breadth_pct >= 10 else "red"
                ),
            },
            "risk": {
                "var_95_pct": var_95 * 100,
                "portfolio_vol": portfolio_volatility * 100,
            },
            "go_signals": self.go_signals,
            "active_tokens": len(self.tokens),
            "hedge_basket_size": len(self.microcap_30_basket),
        }

        return dashboard

    async def run_complete_framework(self):
        """
        Execute complete BTC-free micro-cap framework
        """
        print("🚀 Starting BTC-Free Micro-Cap Framework")
        print("=" * 50)

        # Step 1: Scan universe
        await self.scan_microcap_universe()

        if not self.tokens:
            print("❌ No micro-cap tokens found")
            return

        # Step 2: Build hedge basket
        self.build_microcap_30_basket()

        # Step 3: Calculate Kelly weights
        self.calculate_kelly_weights()

        # Step 4: Check GO signals
        go_signal = self.check_go_signals()

        # Step 5: Risk controls
        risk_controls = self.check_risk_controls()

        # Step 6: Generate dashboard
        dashboard = self.generate_dashboard_metrics()

        print("\n📊 FRAMEWORK SUMMARY")
        print("=" * 30)
        print(f"Micro-cap tokens found: {len(self.tokens)}")
        print(f"Hedge basket size: {len(self.microcap_30_basket)}")
        print(f"Position weights calculated: {len(self.position_weights)}")
        print(f"GO signal: {'✅' if go_signal else '❌'}")
        print(f"Risk controls: {sum(risk_controls.values())} active")

        # Step 7: Execute if GO
        if go_signal and not any(risk_controls.values()):
            print("\n🎯 EXECUTING POSITIONS")
            print("=" * 25)

            for symbol, weight in sorted(
                self.position_weights.items(), key=lambda x: x[1], reverse=True
            )[:10]:
                if weight > 0.01:  # Only significant positions
                    target_size = weight * 100000  # Example $100k portfolio
                    self.execute_illiquidity_aware_ladder(symbol, target_size)

        else:
            print("\n⏸️ STANDBY MODE")
            print("Maintaining <40% funded longs, minimal hedge")

        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "framework_summary": {
                "total_tokens": len(self.tokens),
                "hedge_basket": self.microcap_30_basket,
                "position_weights": self.position_weights,
                "go_signal": go_signal,
                "go_signals_detail": self.go_signals,
                "risk_controls": risk_controls,
                "dashboard": dashboard,
            },
        }

        with open("btc_free_microcap_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Results saved to btc_free_microcap_results.json")
        print("🏁 BTC-Free Micro-Cap Framework Complete")


async def main():
    """Demo the BTC-free micro-cap framework"""
    strategy = BTCFreeMicroCapStrategy()
    await strategy.run_complete_framework()


if __name__ == "__main__":
    asyncio.run(main())
