#!/usr/bin/env python3

"""
🎮 MAGIC REAL-TIME MONITORING & ALERT SYSTEM
Live tracking, pattern detection, and smart alerts for MAGIC trading
"""

import json
import os
import sys
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import threading
from collections import deque
import statistics

# Add project root to path
sys.path.append(os.path.dirname(__file__))

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException

    binance_available = True
except ImportError:
    binance_available = False

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "config", ".env"))


class MagicRealtimeMonitor:
    """Real-time MAGIC monitoring with intelligent alerts"""

    def __init__(self):
        # Initialize Binance client
        self.BINANCEUS_KEY = os.getenv("BINANCEUS_KEY")
        self.BINANCEUS_SECRET = os.getenv("BINANCEUS_SECRET")
        self.client = None

        if binance_available and self.BINANCEUS_KEY:
            try:
                self.client = Client(self.BINANCEUS_KEY, self.BINANCEUS_SECRET)
                print("✅ Real-time monitor connected to Binance")
            except Exception as e:
                print(f"⚠️ Binance client error: {e}")

        # Real-time data storage
        self.price_data = deque(maxlen=288)  # 24 hours of 5-minute data
        self.volume_data = deque(maxlen=288)
        self.trade_data = deque(maxlen=100)

        # Monitoring state
        self.monitoring_active = False
        self.last_alert_time = {}
        self.alert_cooldown = 300  # 5 minutes between similar alerts

        # Key levels and triggers
        self.key_levels = {
            "strong_support": 0.21,
            "support": 0.23,
            "current_range_low": 0.235,
            "current_range_high": 0.245,
            "resistance": 0.27,
            "strong_resistance": 0.31,
            "breakout_target": 0.35,
        }

        # Alert configuration
        self.alert_config = {
            "price_spike": {
                "threshold": 0.03,  # 3% in 5 minutes
                "enabled": True,
                "priority": "HIGH",
            },
            "volume_surge": {
                "multiplier": 2.0,  # 2x average volume
                "enabled": True,
                "priority": "HIGH",
            },
            "support_test": {
                "distance": 0.005,  # Within 0.5% of support
                "enabled": True,
                "priority": "MEDIUM",
            },
            "resistance_approach": {
                "distance": 0.005,  # Within 0.5% of resistance
                "enabled": True,
                "priority": "MEDIUM",
            },
            "breakout_signal": {
                "volume_confirm": True,
                "enabled": True,
                "priority": "CRITICAL",
            },
            "pattern_completion": {"enabled": True, "priority": "HIGH"},
        }

        # Pattern recognition state
        self.pattern_state = {
            "current_pattern": None,
            "pattern_progress": 0.0,
            "confirmation_signals": 0,
            "invalidation_level": 0.0,
        }

        # Learning database
        self.learning_data = {
            "successful_alerts": [],
            "false_alerts": [],
            "pattern_outcomes": [],
            "optimal_entry_points": [],
        }

    def start_monitoring(self, interval: int = 30):
        """Start real-time monitoring with specified interval"""
        if not self.client:
            print("❌ Cannot start monitoring without Binance connection")
            return False

        self.monitoring_active = True
        print(f"🔄 Starting MAGIC real-time monitoring (interval: {interval}s)")

        def monitor_loop():
            while self.monitoring_active:
                try:
                    # Fetch current data
                    data = self._fetch_current_data()
                    if data:
                        # Store data
                        self._store_data(data)

                        # Analysis and alerts
                        self._analyze_and_alert(data)

                        # Pattern detection
                        self._detect_patterns(data)

                        # Learning updates
                        self._update_learning(data)

                    time.sleep(interval)

                except Exception as e:
                    print(f"⚠️ Monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error

        # Start in background thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

        return True

    def _fetch_current_data(self) -> Optional[Dict]:
        """Fetch current MAGIC market data"""
        try:
            # Current price
            ticker = self.client.get_symbol_ticker(symbol="MAGICUSDT")
            current_price = float(ticker["price"])

            # 24h stats
            stats = self.client.get_24hr_ticker(symbol="MAGICUSDT")
            volume_24h = float(stats["volume"]) * current_price
            price_change_24h = float(stats["priceChangePercent"])

            # Order book depth
            depth = self.client.get_order_book(symbol="MAGICUSDT", limit=20)
            bid_price = float(depth["bids"][0][0])
            ask_price = float(depth["asks"][0][0])
            spread = (ask_price - bid_price) / bid_price

            # Recent trades
            trades = self.client.get_recent_trades(symbol="MAGICUSDT", limit=100)

            return {
                "timestamp": datetime.now(),
                "price": current_price,
                "volume_24h": volume_24h,
                "price_change_24h": price_change_24h,
                "bid": bid_price,
                "ask": ask_price,
                "spread": spread,
                "trades_count": len(trades),
                "large_trades": len(
                    [t for t in trades if float(t["qty"]) * current_price > 1000]
                ),
            }

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None

    def _store_data(self, data: Dict):
        """Store data in rolling buffers"""
        timestamp = data["timestamp"]
        price = data["price"]
        volume = data["volume_24h"]

        self.price_data.append((timestamp, price))
        self.volume_data.append((timestamp, volume))

        # Store significant trades
        if data["large_trades"] > 0:
            self.trade_data.append(
                {
                    "timestamp": timestamp,
                    "price": price,
                    "large_trades": data["large_trades"],
                    "spread": data["spread"],
                }
            )

    def _analyze_and_alert(self, data: Dict):
        """Analyze current data and trigger alerts"""
        current_price = data["price"]
        current_volume = data["volume_24h"]
        timestamp = data["timestamp"]

        # Price movement alerts
        if len(self.price_data) >= 2:
            prev_price = self.price_data[-2][1]
            price_change = (current_price - prev_price) / prev_price

            if abs(price_change) > self.alert_config["price_spike"]["threshold"]:
                self._trigger_alert(
                    "price_spike",
                    {
                        "direction": "UP" if price_change > 0 else "DOWN",
                        "magnitude": abs(price_change) * 100,
                        "price": current_price,
                        "timestamp": timestamp,
                    },
                )

        # Volume surge alerts
        if len(self.volume_data) >= 10:
            avg_volume = statistics.mean([v[1] for v in list(self.volume_data)[-10:]])
            volume_ratio = current_volume / avg_volume

            if volume_ratio > self.alert_config["volume_surge"]["multiplier"]:
                self._trigger_alert(
                    "volume_surge",
                    {
                        "ratio": volume_ratio,
                        "current_volume": current_volume,
                        "avg_volume": avg_volume,
                        "timestamp": timestamp,
                    },
                )

        # Key level alerts
        self._check_key_levels(current_price, timestamp)

        # Breakout detection
        self._check_breakout_signals(data)

    def _check_key_levels(self, price: float, timestamp: datetime):
        """Check proximity to key support/resistance levels"""

        for level_name, level_price in self.key_levels.items():
            distance = abs(price - level_price) / level_price

            if distance < 0.005:  # Within 0.5%
                if "support" in level_name and price < level_price * 1.01:
                    self._trigger_alert(
                        "support_test",
                        {
                            "level": level_name,
                            "level_price": level_price,
                            "current_price": price,
                            "distance": distance * 100,
                            "timestamp": timestamp,
                        },
                    )

                elif "resistance" in level_name and price > level_price * 0.99:
                    self._trigger_alert(
                        "resistance_approach",
                        {
                            "level": level_name,
                            "level_price": level_price,
                            "current_price": price,
                            "distance": distance * 100,
                            "timestamp": timestamp,
                        },
                    )

    def _check_breakout_signals(self, data: Dict):
        """Check for breakout signals with volume confirmation"""
        current_price = data["price"]
        current_volume = data["volume_24h"]

        # Check for resistance breakout
        if current_price > self.key_levels["resistance"]:
            if len(self.volume_data) >= 5:
                avg_volume = statistics.mean(
                    [v[1] for v in list(self.volume_data)[-5:]]
                )
                if current_volume > avg_volume * 1.5:  # Volume confirmation
                    self._trigger_alert(
                        "breakout_signal",
                        {
                            "type": "resistance_breakout",
                            "level": self.key_levels["resistance"],
                            "current_price": current_price,
                            "volume_confirmation": True,
                            "target": self.key_levels["strong_resistance"],
                            "timestamp": data["timestamp"],
                        },
                    )

        # Check for support breakdown
        elif current_price < self.key_levels["support"]:
            if len(self.volume_data) >= 5:
                avg_volume = statistics.mean(
                    [v[1] for v in list(self.volume_data)[-5:]]
                )
                if current_volume > avg_volume * 1.3:  # Volume confirmation
                    self._trigger_alert(
                        "breakout_signal",
                        {
                            "type": "support_breakdown",
                            "level": self.key_levels["support"],
                            "current_price": current_price,
                            "volume_confirmation": True,
                            "target": self.key_levels["strong_support"],
                            "timestamp": data["timestamp"],
                        },
                    )

    def _detect_patterns(self, data: Dict):
        """Detect chart patterns in real-time"""
        if len(self.price_data) < 20:
            return

        recent_prices = [p[1] for p in list(self.price_data)[-20:]]
        current_price = data["price"]

        # Double bottom pattern
        if self._detect_double_bottom(recent_prices):
            self._trigger_alert(
                "pattern_completion",
                {
                    "pattern": "double_bottom",
                    "confidence": 0.75,
                    "target": current_price * 1.15,
                    "invalidation": min(recent_prices[-10:]) * 0.98,
                    "timestamp": data["timestamp"],
                },
            )

        # Bull flag pattern
        elif self._detect_bull_flag(recent_prices):
            self._trigger_alert(
                "pattern_completion",
                {
                    "pattern": "bull_flag",
                    "confidence": 0.70,
                    "target": current_price * 1.12,
                    "invalidation": current_price * 0.95,
                    "timestamp": data["timestamp"],
                },
            )

        # Ascending triangle
        elif self._detect_ascending_triangle(recent_prices):
            self._trigger_alert(
                "pattern_completion",
                {
                    "pattern": "ascending_triangle",
                    "confidence": 0.80,
                    "target": current_price * 1.18,
                    "invalidation": current_price * 0.92,
                    "timestamp": data["timestamp"],
                },
            )

    def _detect_double_bottom(self, prices: List[float]) -> bool:
        """Detect double bottom pattern"""
        if len(prices) < 15:
            return False

        # Find two lows with similar levels
        min_price = min(prices)
        low_indices = [i for i, p in enumerate(prices) if p <= min_price * 1.02]

        if len(low_indices) >= 2:
            # Check if there's a peak between the lows
            first_low_idx = low_indices[0]
            last_low_idx = low_indices[-1]

            if last_low_idx - first_low_idx > 5:
                middle_section = prices[first_low_idx:last_low_idx]
                if max(middle_section) > min_price * 1.05:
                    return True

        return False

    def _detect_bull_flag(self, prices: List[float]) -> bool:
        """Detect bull flag pattern"""
        if len(prices) < 12:
            return False

        # Strong move up followed by sideways consolidation
        early_prices = prices[:6]
        late_prices = prices[-6:]

        early_avg = statistics.mean(early_prices)
        late_avg = statistics.mean(late_prices)

        # Check for initial rally
        if late_avg > early_avg * 1.05:
            # Check for consolidation (low volatility)
            late_volatility = statistics.stdev(late_prices) / late_avg
            if late_volatility < 0.03:  # Low volatility
                return True

        return False

    def _detect_ascending_triangle(self, prices: List[float]) -> bool:
        """Detect ascending triangle pattern"""
        if len(prices) < 15:
            return False

        # Check for horizontal resistance and rising support
        highs = [
            prices[i]
            for i in range(len(prices))
            if i == 0
            or i == len(prices) - 1
            or (prices[i] > prices[i - 1] and prices[i] > prices[i + 1])
        ]

        lows = [
            prices[i]
            for i in range(len(prices))
            if i == 0
            or i == len(prices) - 1
            or (prices[i] < prices[i - 1] and prices[i] < prices[i + 1])
        ]

        if len(highs) >= 3 and len(lows) >= 3:
            # Check if highs are relatively flat
            high_volatility = statistics.stdev(highs) / statistics.mean(highs)
            if high_volatility < 0.02:
                # Check if lows are ascending
                if lows[-1] > lows[0] * 1.02:
                    return True

        return False

    def _trigger_alert(self, alert_type: str, data: Dict):
        """Trigger an alert with cooldown management"""
        current_time = datetime.now()

        # Check cooldown
        if alert_type in self.last_alert_time:
            time_since_last = (current_time - self.last_alert_time[alert_type]).seconds
            if time_since_last < self.alert_cooldown:
                return  # Skip due to cooldown

        # Update last alert time
        self.last_alert_time[alert_type] = current_time

        # Get alert configuration
        config = self.alert_config.get(alert_type, {})
        if not config.get("enabled", True):
            return

        priority = config.get("priority", "LOW")

        # Format alert message
        message = self._format_alert_message(alert_type, data, priority)

        # Display alert
        print(f"\n{message}")

        # Log alert for learning
        self.learning_data["successful_alerts"].append(
            {
                "type": alert_type,
                "data": data,
                "priority": priority,
                "timestamp": current_time,
            }
        )

        # Save alert to file for persistence
        self._save_alert_to_file(alert_type, data, priority, current_time)

    def _format_alert_message(self, alert_type: str, data: Dict, priority: str) -> str:
        """Format alert message for display"""
        timestamp = data.get("timestamp", datetime.now()).strftime("%H:%M:%S")

        if alert_type == "price_spike":
            direction = data["direction"]
            magnitude = data["magnitude"]
            price = data["price"]
            return f"🚨 [{priority}] {timestamp} - MAGIC {direction} {magnitude:.1f}% spike! Price: ${price:.4f}"

        elif alert_type == "volume_surge":
            ratio = data["ratio"]
            volume = data["current_volume"]
            return f"📈 [{priority}] {timestamp} - Volume surge {ratio:.1f}x! Current: ${volume:,.0f}"

        elif alert_type == "support_test":
            level = data["level"]
            level_price = data["level_price"]
            distance = data["distance"]
            return f"🛡️ [{priority}] {timestamp} - Testing {level} at ${level_price:.3f} ({distance:.1f}% away)"

        elif alert_type == "resistance_approach":
            level = data["level"]
            level_price = data["level_price"]
            distance = data["distance"]
            return f"⚔️ [{priority}] {timestamp} - Approaching {level} at ${level_price:.3f} ({distance:.1f}% away)"

        elif alert_type == "breakout_signal":
            breakout_type = data["type"]
            level = data["level"]
            target = data["target"]
            return f"🚀 [{priority}] {timestamp} - {breakout_type.replace('_', ' ').title()}! Level: ${level:.3f}, Target: ${target:.3f}"

        elif alert_type == "pattern_completion":
            pattern = data["pattern"]
            confidence = data["confidence"]
            target = data["target"]
            return f"🎯 [{priority}] {timestamp} - {pattern.replace('_', ' ').title()} pattern! Confidence: {confidence:.0%}, Target: ${target:.3f}"

        else:
            return f"📢 [{priority}] {timestamp} - {alert_type}: {data}"

    def _save_alert_to_file(
        self, alert_type: str, data: Dict, priority: str, timestamp: datetime
    ):
        """Save alert to file for persistence"""
        alert_record = {
            "type": alert_type,
            "priority": priority,
            "timestamp": timestamp.isoformat(),
            "data": data,
        }

        filename = f"magic_alerts_{datetime.now().strftime('%Y%m%d')}.json"

        # Load existing alerts
        alerts = []
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    alerts = json.load(f)
            except:
                alerts = []

        # Add new alert
        alerts.append(alert_record)

        # Save back to file
        with open(filename, "w") as f:
            json.dump(alerts, f, indent=2, default=str)

    def _update_learning(self, data: Dict):
        """Update learning database with current market behavior"""
        # This would implement machine learning updates in production
        pass

    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status and statistics"""
        return {
            "active": self.monitoring_active,
            "data_points": len(self.price_data),
            "alerts_today": len(
                [
                    a
                    for a in self.learning_data["successful_alerts"]
                    if a["timestamp"].date() == datetime.now().date()
                ]
            ),
            "last_price": self.price_data[-1][1] if self.price_data else 0,
            "current_pattern": self.pattern_state["current_pattern"],
            "key_levels": self.key_levels,
        }

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        print("🛑 MAGIC monitoring stopped")

    def get_alert_summary(self) -> str:
        """Get summary of recent alerts"""
        recent_alerts = [
            a
            for a in self.learning_data["successful_alerts"]
            if (datetime.now() - a["timestamp"]).seconds < 3600
        ]  # Last hour

        if not recent_alerts:
            return "📊 No alerts in the last hour"

        summary = f"📢 {len(recent_alerts)} alerts in the last hour:\n"
        for alert in recent_alerts[-5:]:  # Last 5 alerts
            timestamp = alert["timestamp"].strftime("%H:%M")
            alert_type = alert["type"].replace("_", " ").title()
            priority = alert["priority"]
            summary += f"   {timestamp} - {alert_type} [{priority}]\n"

        return summary


def main():
    """Main execution function"""
    print("🎮 MAGIC REAL-TIME MONITORING & ALERT SYSTEM")
    print("=" * 80)

    monitor = MagicRealtimeMonitor()

    if not monitor.client:
        print("❌ Cannot run without Binance connection")
        print("Running in demo mode with simulated data...")

        # Demo mode with simulated alerts
        print("\n🎯 DEMO ALERTS (simulated):")

        demo_alerts = [
            (
                "price_spike",
                {
                    "direction": "UP",
                    "magnitude": 3.2,
                    "price": 0.2465,
                    "timestamp": datetime.now(),
                },
            ),
            (
                "volume_surge",
                {
                    "ratio": 2.3,
                    "current_volume": 15420,
                    "avg_volume": 6700,
                    "timestamp": datetime.now(),
                },
            ),
            (
                "support_test",
                {
                    "level": "support",
                    "level_price": 0.230,
                    "current_price": 0.2315,
                    "distance": 0.6,
                    "timestamp": datetime.now(),
                },
            ),
            (
                "pattern_completion",
                {
                    "pattern": "double_bottom",
                    "confidence": 0.75,
                    "target": 0.275,
                    "timestamp": datetime.now(),
                },
            ),
        ]

        for alert_type, data in demo_alerts:
            monitor._trigger_alert(alert_type, data)
            time.sleep(1)

        print(f"\n📊 Demo monitoring status: {monitor.get_monitoring_status()}")
        print(f"\n{monitor.get_alert_summary()}")

        return

    # Real monitoring
    print("\n🔄 Starting real-time monitoring...")

    # Configuration
    interval = int(input("Enter monitoring interval in seconds (default 30): ") or "30")

    # Start monitoring
    if monitor.start_monitoring(interval):
        print(f"✅ Monitoring started with {interval}s interval")
        print("📢 Alerts will appear below...")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                time.sleep(10)

                # Show periodic status
                status = monitor.get_monitoring_status()
                if status["data_points"] > 0:
                    print(
                        f"📊 Status: {status['data_points']} data points, Last price: ${status['last_price']:.4f}"
                    )

                # Show alert summary every 5 minutes
                if datetime.now().minute % 5 == 0:
                    print(monitor.get_alert_summary())

        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\n✅ Monitoring session complete!")

            # Final summary
            final_status = monitor.get_monitoring_status()
            print(f"📊 Final statistics:")
            print(f"   Data points collected: {final_status['data_points']}")
            print(f"   Alerts triggered: {final_status['alerts_today']}")
            print(f"   Last price: ${final_status['last_price']:.4f}")

    else:
        print("❌ Failed to start monitoring")


if __name__ == "__main__":
    main()
