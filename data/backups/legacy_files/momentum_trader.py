#!/usr/bin/env python3
"""
VictoryChain Momentum Trader
Executes trades on 20-30% momentum opportunities
"""

import requests
import json
import time
import hmac
import hashlib
from urllib.parse import urlencode
import os
from datetime import datetime


class MomentumTrader:
    def __init__(self):
        self.api_key = os.getenv("BINANCEUS_KEY", "")
        self.secret_key = os.getenv("BINANCEUS_SECRET", "")
        self.base_url = "https://api.binance.us"

        if not self.api_key or not self.secret_key:
            print("⚠️ Warning: Binance API keys not found in environment")
            print("   Set BINANCEUS_KEY and BINANCEUS_SECRET to enable live trading")
            self.demo_mode = True
        else:
            self.demo_mode = False

    def create_signature(self, params):
        """Create HMAC SHA256 signature for Binance API"""
        query_string = urlencode(params)
        return hmac.new(
            self.secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def get_account_balance(self):
        """Get account balance"""
        if self.demo_mode:
            return {"USDT": {"free": "237.15", "locked": "0.00"}}

        try:
            timestamp = int(time.time() * 1000)
            params = {"timestamp": timestamp}
            signature = self.create_signature(params)
            params["signature"] = signature

            headers = {"X-MBX-APIKEY": self.api_key}

            response = requests.get(
                f"{self.base_url}/api/v3/account", headers=headers, params=params
            )

            if response.status_code == 200:
                account_data = response.json()
                balances = {}
                for balance in account_data["balances"]:
                    if float(balance["free"]) > 0 or float(balance["locked"]) > 0:
                        balances[balance["asset"]] = {
                            "free": balance["free"],
                            "locked": balance["locked"],
                        }
                return balances
            else:
                print(f"❌ Failed to get account balance: {response.status_code}")
                return {}
        except Exception as e:
            print(f"❌ Error getting balance: {e}")
            return {}

    def place_buy_order(self, symbol: str, usdt_amount: float):
        """Place a buy order for specified USDT amount"""
        if self.demo_mode:
            print(f"📝 DEMO: Would buy ${usdt_amount:.2f} worth of {symbol}")
            return {"status": "DEMO", "orderId": "DEMO123"}

        try:
            # Get current price to calculate quantity
            ticker_response = requests.get(
                f"{self.base_url}/api/v3/ticker/price?symbol={symbol}"
            )
            if ticker_response.status_code != 200:
                return {"error": "Failed to get current price"}

            current_price = float(ticker_response.json()["price"])
            quantity = usdt_amount / current_price

            # Round quantity to appropriate precision (simplified)
            quantity = round(quantity, 6)

            timestamp = int(time.time() * 1000)
            params = {
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quoteOrderQty": str(usdt_amount),
                "timestamp": timestamp,
            }

            signature = self.create_signature(params)
            params["signature"] = signature

            headers = {"X-MBX-APIKEY": self.api_key}

            response = requests.post(
                f"{self.base_url}/api/v3/order", headers=headers, data=params
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Order failed: {response.status_code} - {response.text}")
                return {"error": response.text}

        except Exception as e:
            print(f"❌ Error placing buy order: {e}")
            return {"error": str(e)}

    def place_sell_order(self, symbol: str, quantity: float):
        """Place a sell order for specified quantity"""
        if self.demo_mode:
            print(f"📝 DEMO: Would sell {quantity:.6f} {symbol}")
            return {"status": "DEMO", "orderId": "DEMO456"}

        try:
            timestamp = int(time.time() * 1000)
            params = {
                "symbol": symbol,
                "side": "SELL",
                "type": "MARKET",
                "quantity": str(quantity),
                "timestamp": timestamp,
            }

            signature = self.create_signature(params)
            params["signature"] = signature

            headers = {"X-MBX-APIKEY": self.api_key}

            response = requests.post(
                f"{self.base_url}/api/v3/order", headers=headers, data=params
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Sell order failed: {response.status_code} - {response.text}")
                return {"error": response.text}

        except Exception as e:
            print(f"❌ Error placing sell order: {e}")
            return {"error": str(e)}

    def execute_momentum_trades(self, opportunities: list, position_size: float = 75.0):
        """Execute trades on momentum opportunities"""
        print(f"🎯 Executing momentum trades with ${position_size:.2f} position size")

        # Check available balance
        balances = self.get_account_balance()
        usdt_balance = float(balances.get("USDT", {}).get("free", "0"))

        print(f"💰 Available USDT balance: ${usdt_balance:.2f}")

        if usdt_balance < position_size:
            print(f"⚠️ Insufficient balance for ${position_size:.2f} positions")
            position_size = min(
                position_size, usdt_balance * 0.9
            )  # Use 90% of available
            print(f"   Adjusted position size to: ${position_size:.2f}")

        executed_trades = []

        for i, opp in enumerate(opportunities[:3]):  # Top 3 opportunities only
            symbol = opp["symbol"]
            print(f"\n🚀 Executing trade {i+1}: {symbol}")
            print(f"   Target gain: {opp['gain_percent']:.1f}%")
            print(f"   AI confidence: {opp['confidence']}%")
            print(f"   Risk level: {opp['risk_level']}")

            # Place buy order
            result = self.place_buy_order(symbol, position_size)

            if "error" not in result:
                trade_record = {
                    "symbol": symbol,
                    "entry_time": datetime.now().isoformat(),
                    "entry_price": opp["current_price"],
                    "target_price": opp["target_price"],
                    "position_size": position_size,
                    "expected_gain": opp["gain_percent"],
                    "confidence": opp["confidence"],
                    "hold_hours": opp["hold_hours"],
                    "order_id": result.get("orderId", "DEMO"),
                    "status": "ACTIVE",
                }
                executed_trades.append(trade_record)

                print(f"✅ Trade executed successfully!")
                print(f"   Order ID: {result.get('orderId', 'DEMO')}")
                print(f"   Entry price: ${opp['current_price']:.6f}")
                print(f"   Target price: ${opp['target_price']:.6f}")

                # Calculate stop loss
                stop_loss_price = opp["current_price"] * 0.92  # 8% stop loss
                print(f"   Stop loss: ${stop_loss_price:.6f} (-8%)")

            else:
                print(f"❌ Trade failed: {result['error']}")

        return executed_trades

    def monitor_positions(self, trades: list):
        """Monitor active positions for exit signals"""
        print(f"\n📊 Monitoring {len(trades)} active positions...")

        for trade in trades:
            if trade["status"] != "ACTIVE":
                continue

            symbol = trade["symbol"]
            print(f"\n📈 Monitoring {symbol}:")

            # Get current price
            try:
                response = requests.get(
                    f"{self.base_url}/api/v3/ticker/price?symbol={symbol}"
                )
                if response.status_code == 200:
                    current_price = float(response.json()["price"])
                    entry_price = trade["entry_price"]

                    # Calculate current P&L
                    pnl_percent = (current_price - entry_price) / entry_price * 100

                    print(
                        f"   Entry: ${entry_price:.6f} | Current: ${current_price:.6f}"
                    )
                    print(
                        f"   P&L: {pnl_percent:+.2f}% | Target: +{trade['expected_gain']:.1f}%"
                    )

                    # Check exit conditions
                    target_hit = current_price >= trade["target_price"]
                    stop_loss_hit = current_price <= entry_price * 0.92

                    # Time-based exit (simplified)
                    time_exit = False  # Would implement time tracking here

                    if target_hit:
                        print(f"🎉 TARGET HIT! Profit: +{pnl_percent:.2f}%")
                        # Would execute sell order here
                        trade["status"] = "CLOSED_PROFIT"

                    elif stop_loss_hit:
                        print(f"🛡️ STOP LOSS triggered. Loss: {pnl_percent:.2f}%")
                        # Would execute sell order here
                        trade["status"] = "CLOSED_LOSS"

                    else:
                        print(f"   ⏳ Holding position...")

                else:
                    print(f"   ⚠️ Failed to get price for {symbol}")

            except Exception as e:
                print(f"   ❌ Error monitoring {symbol}: {e}")

    def get_position_summary(self, trades: list):
        """Get summary of all positions"""
        active_trades = [t for t in trades if t["status"] == "ACTIVE"]
        closed_profit = [t for t in trades if t["status"] == "CLOSED_PROFIT"]
        closed_loss = [t for t in trades if t["status"] == "CLOSED_LOSS"]

        print(f"\n💼 POSITION SUMMARY:")
        print(f"   Active positions: {len(active_trades)}")
        print(f"   Profitable closes: {len(closed_profit)}")
        print(f"   Loss closes: {len(closed_loss)}")

        if active_trades:
            total_invested = sum(t["position_size"] for t in active_trades)
            print(f"   Total invested: ${total_invested:.2f}")


def main():
    print("🎯 VictoryChain Momentum Trader")
    print("==============================")
    print("⚡ Automated 20-30% Momentum Trading")
    print("")

    trader = MomentumTrader()

    if trader.demo_mode:
        print("📝 DEMO MODE - No real trades will be executed")
        print("   Set BINANCEUS_KEY and BINANCEUS_SECRET for live trading")
    else:
        print("🔴 LIVE TRADING MODE - Real money will be used!")
        confirmation = input("Type 'CONFIRM' to proceed with live trading: ")
        if confirmation != "CONFIRM":
            print("❌ Trading cancelled")
            return

    # Sample opportunities (in real use, would come from momentum_scanner.py)
    sample_opportunities = [
        {
            "symbol": "XRPUSDT",
            "current_price": 2.7776,
            "target_price": 3.45,
            "gain_percent": 24.2,
            "confidence": 75,
            "risk_level": "MEDIUM",
            "hold_hours": 36,
        },
        {
            "symbol": "FLOKIUSDT",
            "current_price": 0.000101,
            "target_price": 0.000126,
            "gain_percent": 24.8,
            "confidence": 65,
            "risk_level": "HIGH",
            "hold_hours": 36,
        },
    ]

    print("🚀 Executing momentum trades...")
    executed_trades = trader.execute_momentum_trades(
        sample_opportunities, position_size=75.0
    )

    if executed_trades:
        print(f"\n✅ Successfully executed {len(executed_trades)} trades")

        # Monitor positions (simplified example)
        print("\n⏳ Starting position monitoring...")
        trader.monitor_positions(executed_trades)
        trader.get_position_summary(executed_trades)
    else:
        print("❌ No trades were executed")

    print("\n💡 Next steps:")
    print("   • Monitor positions regularly")
    print("   • Set price alerts for targets and stop losses")
    print("   • Take profits at target levels")
    print("   • Cut losses quickly at stop loss levels")
    print("   • Re-scan for new opportunities every hour")


if __name__ == "__main__":
    main()
