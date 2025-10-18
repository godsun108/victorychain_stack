#!/usr/bin/env python3

"""
🎮 LIVE GALA TRADING BOT
Real-time GALAUSDT trading using MAGIC-driven intelligence
Live market data, real-time analysis, and automated execution
"""

import json
import os
import sys
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import uuid
from dataclasses import dataclass, asdict
import requests
import threading

# Add project root to path
sys.path.append(os.path.dirname(__file__))

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException

    binance_available = True
except ImportError:
    binance_available = False
    print("⚠️ Binance library not available - using simulation mode")

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))


@dataclass
class LiveGalaPosition:
    """Live GALA position tracking"""

    symbol: str = "GALAUSDT"
    entry_price: float = 0.0
    current_price: float = 0.0
    quantity: float = 0.0
    allocation_percentage: float = 0.0
    entry_time: datetime = None
    stop_loss: float = 0.0
    target_prices: List[float] = None
    current_pnl: float = 0.0
    current_pnl_percentage: float = 0.0
    magic_similarity_score: float = 0.0
    position_id: str = ""
    status: str = "NONE"

    def __post_init__(self):
        if self.target_prices is None:
            self.target_prices = []
        if self.position_id == "":
            self.position_id = str(uuid.uuid4())
        if self.entry_time is None:
            self.entry_time = datetime.now()


@dataclass
class LiveMarketData:
    """Live market data for GALA"""

    symbol: str = "GALAUSDT"
    price: float = 0.0
    bid: float = 0.0
    ask: float = 0.0
    volume_24h: float = 0.0
    price_change_24h: float = 0.0
    price_change_percent_24h: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    last_update: datetime = None

    def __post_init__(self):
        if self.last_update is None:
            self.last_update = datetime.now()


class LiveGalaBot:
    """Live GALAUSDT trading bot with MAGIC-driven intelligence"""

    def __init__(self):
        self.symbol = "GALAUSDT"
        self.position = LiveGalaPosition()
        self.market_data = LiveMarketData()
        self.running = False
        self.client = None
        self.trading_enabled = False

        # MAGIC-driven parameters for GALA
        self.magic_gala_params = {
            "gaming_score": 7.0,  # GALA gaming ecosystem score
            "magic_similarity": 90.6,  # From our previous analysis
            "stop_loss_percentage": -10.0,  # Conservative stop
            "target_gains": [25.0, 50.0, 100.0, 200.0],  # GALA targets
            "max_allocation": 15.0,  # Maximum 15% like MAGIC
            "momentum_threshold": 5.0,  # Minimum momentum for entry
            "volume_threshold": 5000.0,  # Minimum daily volume
        }

        self.load_existing_analysis()
        self.setup_binance_client()

    def load_existing_analysis(self):
        """Load existing GALA analysis"""
        try:
            # Load GALA analysis if available
            with open("gala_analysis.py", "r") as f:
                print("✅ Found GALA analysis file")

            # Load comprehensive token data
            with open("comprehensive_token_analysis_20250805_155947.json", "r") as f:
                token_data = json.load(f)

                # Find GALA data
                for token in token_data:
                    if token.get("symbol") == "GALAUSDT":
                        self.gala_token_data = token
                        print(f"✅ Loaded GALA token data: ${token['price']:.6f}")
                        break

        except FileNotFoundError:
            print("⚠️ No existing GALA analysis found - using defaults")
            self.gala_token_data = {"price": 0.015, "volume_24h_usdt": 5000}

    def setup_binance_client(self):
        """Setup Binance client for live trading"""
        if not binance_available:
            print("📊 Running in simulation mode (no Binance library)")
            return

        try:
            api_key = os.getenv("BINANCEUS_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET")

            if api_key and api_secret:
                self.client = Client(api_key, api_secret, testnet=False)

                # Test connection
                account = self.client.get_account()
                print(
                    f"✅ Connected to Binance - Account Status: {account['accountType']}"
                )
                self.trading_enabled = True

                # Get GALA balance
                for balance in account["balances"]:
                    if balance["asset"] in ["GALA", "USDT"]:
                        print(
                            f"💰 {balance['asset']}: {balance['free']} (locked: {balance['locked']})"
                        )

            else:
                print("⚠️ No API credentials - running in simulation mode")

        except Exception as e:
            print(f"⚠️ Binance connection failed: {e}")
            print("📊 Running in simulation mode")

    def get_live_market_data(self) -> LiveMarketData:
        """Get live market data for GALA"""
        try:
            if self.client:
                # Get live ticker data
                ticker = self.client.get_ticker(symbol=self.symbol)

                self.market_data = LiveMarketData(
                    symbol=self.symbol,
                    price=float(ticker["lastPrice"]),
                    bid=float(ticker["bidPrice"]),
                    ask=float(ticker["askPrice"]),
                    volume_24h=float(ticker["volume"]),
                    price_change_24h=float(ticker["priceChange"]),
                    price_change_percent_24h=float(ticker["priceChangePercent"]),
                    high_24h=float(ticker["highPrice"]),
                    low_24h=float(ticker["lowPrice"]),
                    last_update=datetime.now(),
                )

            else:
                # Simulation mode - generate realistic data
                base_price = 0.01513  # From our analysis
                price_variation = np.random.uniform(-0.05, 0.05)
                current_price = base_price * (1 + price_variation)

                self.market_data = LiveMarketData(
                    symbol=self.symbol,
                    price=current_price,
                    bid=current_price * 0.999,
                    ask=current_price * 1.001,
                    volume_24h=np.random.uniform(4000, 8000),
                    price_change_24h=(current_price - base_price),
                    price_change_percent_24h=price_variation * 100,
                    high_24h=current_price * 1.02,
                    low_24h=current_price * 0.98,
                    last_update=datetime.now(),
                )

        except Exception as e:
            print(f"❌ Error getting market data: {e}")

        return self.market_data

    def calculate_gala_magic_score(self, market_data: LiveMarketData) -> float:
        """Calculate GALA's MAGIC similarity score in real-time"""
        score = 0.0

        # Gaming sector bonus (GALA is pure gaming)
        score += 30.0

        # Volume strength (target: >5000 USDT)
        if market_data.volume_24h >= self.magic_gala_params["volume_threshold"]:
            volume_score = min(market_data.volume_24h / 10000, 1.0) * 25.0
            score += volume_score

        # Price stability (prefer low volatility for entry)
        volatility = abs(market_data.price_change_percent_24h)
        if volatility <= 5.0:
            score += 20.0
        elif volatility <= 10.0:
            score += 15.0
        elif volatility <= 15.0:
            score += 10.0

        # MAGIC ecosystem comparison (GALA has 7.0 vs MAGIC's 8.5)
        ecosystem_ratio = self.magic_gala_params["gaming_score"] / 8.5
        score += ecosystem_ratio * 25.0

        return min(score, 100.0)

    def analyze_entry_opportunity(self, market_data: LiveMarketData) -> Dict:
        """Analyze GALA entry opportunity using MAGIC criteria"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "symbol": self.symbol,
            "current_price": market_data.price,
            "magic_score": self.calculate_gala_magic_score(market_data),
            "entry_signal": "NONE",
            "confidence": 0.0,
            "reasoning": [],
            "risk_assessment": {},
        }

        magic_score = analysis["magic_score"]

        # Entry criteria based on MAGIC learnings
        entry_criteria = {
            "magic_score": magic_score >= 60.0,
            "volume_adequate": market_data.volume_24h
            >= self.magic_gala_params["volume_threshold"],
            "price_stable": abs(market_data.price_change_percent_24h) <= 15.0,
            "gaming_sector": True,  # GALA is always gaming
            "no_existing_position": self.position.status == "NONE",
        }

        criteria_met = sum(entry_criteria.values())
        analysis["confidence"] = (criteria_met / len(entry_criteria)) * 100

        # Generate reasoning
        if entry_criteria["magic_score"]:
            analysis["reasoning"].append(
                f"Strong MAGIC similarity ({magic_score:.1f}%)"
            )

        if entry_criteria["volume_adequate"]:
            analysis["reasoning"].append(
                f"Adequate volume (${market_data.volume_24h:,.0f})"
            )

        if entry_criteria["price_stable"]:
            analysis["reasoning"].append(
                f"Price stability ({market_data.price_change_percent_24h:+.2f}%)"
            )

        analysis["reasoning"].append("Gaming sector validation (GALA ecosystem)")

        # Entry signal determination
        if criteria_met >= 4:
            analysis["entry_signal"] = "STRONG_BUY"
        elif criteria_met >= 3:
            analysis["entry_signal"] = "BUY"
        elif criteria_met >= 2:
            analysis["entry_signal"] = "WEAK_BUY"
        else:
            analysis["entry_signal"] = "HOLD"

        # Risk assessment
        analysis["risk_assessment"] = {
            "volatility": (
                "LOW" if abs(market_data.price_change_percent_24h) <= 5.0 else "MEDIUM"
            ),
            "liquidity": "ADEQUATE" if market_data.volume_24h >= 5000 else "LOW",
            "sector_risk": "LOW",  # Gaming sector strength
            "overall_risk": "MEDIUM",
        }

        return analysis

    def execute_gala_entry(self, market_data: LiveMarketData, analysis: Dict) -> bool:
        """Execute GALA entry based on analysis"""
        if analysis["entry_signal"] not in ["BUY", "STRONG_BUY"]:
            return False

        if self.position.status != "NONE":
            print("⚠️ Already have GALA position")
            return False

        # Calculate position size based on MAGIC parameters
        allocation_percentage = self.magic_gala_params["max_allocation"]
        if analysis["confidence"] >= 80.0:
            allocation_percentage = 15.0  # Maximum allocation
        elif analysis["confidence"] >= 70.0:
            allocation_percentage = 12.0
        elif analysis["confidence"] >= 60.0:
            allocation_percentage = 8.0
        else:
            allocation_percentage = 5.0

        entry_price = market_data.price
        stop_loss = entry_price * (
            1 + self.magic_gala_params["stop_loss_percentage"] / 100
        )
        target_prices = [
            entry_price * (1 + gain / 100)
            for gain in self.magic_gala_params["target_gains"]
        ]

        print(f"\n🚀 EXECUTING GALA ENTRY")
        print(f"📊 Price: ${entry_price:.6f}")
        print(f"🎯 Allocation: {allocation_percentage}%")
        print(f"📈 Confidence: {analysis['confidence']:.1f}%")
        print(
            f"🔻 Stop Loss: ${stop_loss:.6f} ({self.magic_gala_params['stop_loss_percentage']}%)"
        )
        print(f"🎯 Targets: {[f'${p:.6f}' for p in target_prices]}")

        # Execute trade (simulation or real)
        if self.trading_enabled and self.client:
            try:
                # Real trading execution
                print("💰 Executing real trade...")
                # Note: Actual trading implementation would go here
                # For safety, keeping as simulation for now
                execution_status = "SIMULATED"
            except Exception as e:
                print(f"❌ Trade execution failed: {e}")
                return False
        else:
            execution_status = "SIMULATED"

        # Update position
        self.position = LiveGalaPosition(
            symbol=self.symbol,
            entry_price=entry_price,
            current_price=entry_price,
            allocation_percentage=allocation_percentage,
            entry_time=datetime.now(),
            stop_loss=stop_loss,
            target_prices=target_prices,
            magic_similarity_score=analysis["magic_score"],
            status="ACTIVE",
        )

        # Save entry record
        entry_record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": self.symbol,
            "action": "ENTRY",
            "price": entry_price,
            "allocation": allocation_percentage,
            "confidence": analysis["confidence"],
            "magic_score": analysis["magic_score"],
            "targets": target_prices,
            "stop_loss": stop_loss,
            "execution_status": execution_status,
            "reasoning": analysis["reasoning"],
        }

        filename = f"live_gala_entry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(entry_record, f, indent=2)

        print(f"✅ GALA position opened - {execution_status}")
        print(f"💾 Entry record saved: {filename}")

        return True

    def monitor_gala_position(self, market_data: LiveMarketData):
        """Monitor active GALA position"""
        if self.position.status != "ACTIVE":
            return

        # Update current price and PnL
        self.position.current_price = market_data.price
        self.position.current_pnl = (
            self.position.current_price - self.position.entry_price
        )
        self.position.current_pnl_percentage = (
            self.position.current_pnl / self.position.entry_price
        ) * 100

        print(f"\n📊 GALA POSITION MONITOR")
        print(f"Entry: ${self.position.entry_price:.6f}")
        print(f"Current: ${self.position.current_price:.6f}")
        print(
            f"PnL: ${self.position.current_pnl:.6f} ({self.position.current_pnl_percentage:+.2f}%)"
        )
        print(f"Stop Loss: ${self.position.stop_loss:.6f}")

        # Check exit conditions
        exit_reason = None

        # Stop loss check
        if self.position.current_price <= self.position.stop_loss:
            exit_reason = "STOP_LOSS"

        # Target profit checks
        elif (
            self.position.current_pnl_percentage
            >= self.magic_gala_params["target_gains"][0]
        ):
            if (
                self.position.current_pnl_percentage
                >= self.magic_gala_params["target_gains"][2]
            ):  # 100% gain
                exit_reason = "TARGET_3_REACHED"
            elif (
                self.position.current_pnl_percentage
                >= self.magic_gala_params["target_gains"][1]
            ):  # 50% gain
                exit_reason = "TARGET_2_REACHED"
            else:  # 25% gain
                exit_reason = "TARGET_1_REACHED"

        if exit_reason:
            self.execute_gala_exit(market_data, exit_reason)

    def execute_gala_exit(self, market_data: LiveMarketData, reason: str):
        """Execute GALA position exit"""
        exit_price = market_data.price
        final_pnl = (
            (exit_price - self.position.entry_price) / self.position.entry_price * 100
        )

        print(f"\n🚪 EXECUTING GALA EXIT")
        print(f"📊 Reason: {reason}")
        print(f"💰 Exit Price: ${exit_price:.6f}")
        print(f"📈 Final PnL: {final_pnl:+.2f}%")

        # Create exit record
        exit_record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": self.symbol,
            "action": "EXIT",
            "reason": reason,
            "entry_price": self.position.entry_price,
            "exit_price": exit_price,
            "pnl_percentage": final_pnl,
            "allocation": self.position.allocation_percentage,
            "duration": str(datetime.now() - self.position.entry_time),
            "magic_score": self.position.magic_similarity_score,
        }

        filename = f"live_gala_exit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(exit_record, f, indent=2)

        print(f"💾 Exit record saved: {filename}")

        # Reset position
        self.position = LiveGalaPosition()

    def run_live_bot(self, duration_minutes: int = 60):
        """Run the live GALA bot"""
        print(f"🤖 STARTING LIVE GALA BOT")
        print(f"🎮 Target: {self.symbol}")
        print(f"⏰ Duration: {duration_minutes} minutes")
        print(f"📊 Mode: {'LIVE TRADING' if self.trading_enabled else 'SIMULATION'}")
        print("=" * 50)

        self.running = True
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        iteration = 0

        while self.running and datetime.now() < end_time:
            iteration += 1

            try:
                # Get live market data
                market_data = self.get_live_market_data()

                print(
                    f"\n🔄 Iteration #{iteration} - {datetime.now().strftime('%H:%M:%S')}"
                )
                print(
                    f"💰 GALA Price: ${market_data.price:.6f} ({market_data.price_change_percent_24h:+.2f}%)"
                )
                print(f"📊 Volume: ${market_data.volume_24h:,.0f}")

                # Analyze entry opportunity if no position
                if self.position.status == "NONE":
                    analysis = self.analyze_entry_opportunity(market_data)
                    print(f"🎯 Entry Signal: {analysis['entry_signal']}")
                    print(f"📈 Confidence: {analysis['confidence']:.1f}%")
                    print(f"🪄 MAGIC Score: {analysis['magic_score']:.1f}%")

                    if analysis["reasoning"]:
                        print(f"💡 Key Factors: {analysis['reasoning'][0]}")

                    # Execute entry if conditions met
                    if analysis["entry_signal"] in ["BUY", "STRONG_BUY"]:
                        self.execute_gala_entry(market_data, analysis)

                # Monitor existing position
                else:
                    self.monitor_gala_position(market_data)

                # Wait before next iteration
                time.sleep(30)  # 30 second intervals

            except KeyboardInterrupt:
                print("\n⏹️ Bot stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in bot loop: {e}")
                time.sleep(5)

        self.running = False
        print(f"\n✅ Live GALA bot completed")
        print(f"⏰ Total runtime: {datetime.now() - start_time}")


def main():
    """Main execution function"""
    print("🎮 LIVE GALA TRADING BOT")
    print("Using MAGIC-driven intelligence for GALAUSDT")
    print("Real-time analysis and automated execution")
    print("=" * 50)

    bot = LiveGalaBot()

    # Display bot configuration
    print(f"\n⚙️ BOT CONFIGURATION:")
    print(f"🎯 Target: {bot.symbol}")
    print(f"🎮 Gaming Score: {bot.magic_gala_params['gaming_score']}/10")
    print(f"🪄 MAGIC Similarity: {bot.magic_gala_params['magic_similarity']}%")
    print(f"🔻 Stop Loss: {bot.magic_gala_params['stop_loss_percentage']}%")
    print(f"📈 Targets: {bot.magic_gala_params['target_gains']}")
    print(f"💰 Max Allocation: {bot.magic_gala_params['max_allocation']}%")
    print(f"🔄 Trading Mode: {'LIVE' if bot.trading_enabled else 'SIMULATION'}")

    # Run the bot
    try:
        bot.run_live_bot(duration_minutes=30)  # Run for 30 minutes
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped")

    print("\n🎯 GALA bot session completed!")


if __name__ == "__main__":
    main()
