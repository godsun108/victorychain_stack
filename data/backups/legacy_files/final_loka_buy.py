#!/usr/bin/env python3
"""
Final LOKA Buy - Use all available USDT to buy more LOKA
Complete the consolidation by purchasing LOKA with remaining USDT
"""

import os
import json
import time
from datetime import datetime
from binance.client import Client
from dotenv import load_dotenv


def final_loka_buy():
    """Buy LOKA with all available USDT"""
    load_dotenv()

    client = Client(
        api_key=os.getenv("BINANCEUS_KEY"),
        api_secret=os.getenv("BINANCEUS_SECRET"),
        tld="us",
    )

    try:
        print("🚀 FINAL LOKA CONSOLIDATION BUY")
        print("=" * 40)

        # Get USDT balance
        account = client.get_account()
        usdt_balance = 0

        for balance in account["balances"]:
            if balance["asset"] == "USDT":
                usdt_balance = float(balance["free"])
                break

        print(f"💰 Available USDT: ${usdt_balance:.2f}")

        if usdt_balance < 10:
            print(f"❌ Insufficient USDT for trade (minimum $10)")
            return

        # Use 99% to avoid precision issues
        buy_amount = round(usdt_balance * 0.99, 2)

        print(f"🎯 Buying LOKA with ${buy_amount:.2f}")
        print()

        confirm = input("🔥 Type 'BUY LOKA NOW' to execute: ")
        if confirm != "BUY LOKA NOW":
            print("❌ LOKA buy cancelled")
            return

        # Execute buy
        print("🚀 EXECUTING LOKA BUY...")

        order = client.order_market_buy(symbol="LOKAUSDT", quoteOrderQty=buy_amount)

        print("✅ LOKA BUY SUCCESSFUL!")
        print(f"📄 Order ID: {order['orderId']}")
        print(f"💎 Bought LOKA with ${buy_amount:.2f}")
        print()
        print("🎉 CONSOLIDATION ENHANCED!")
        print("🚀 MORE ALLOCATION IN LOKA!")

        # Save record
        record = {
            "timestamp": datetime.now().isoformat(),
            "order": order,
            "amount_usdt": buy_amount,
            "type": "final_loka_consolidation_buy",
        }

        filename = f"final_loka_buy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, "w") as f:
            json.dump(record, f, indent=2, default=str)

        print(f"📄 Record saved: {filename}")

        # Show updated portfolio
        time.sleep(2)
        print("\n📊 CHECKING UPDATED PORTFOLIO...")

        account = client.get_account()
        loka_total = 0
        total_value = 0

        for balance in account["balances"]:
            free = float(balance["free"])
            locked = float(balance["locked"])
            total = free + locked

            if total > 0.01:
                if balance["asset"] == "LOKA":
                    loka_total = total
                    try:
                        ticker = client.get_symbol_ticker(symbol="LOKAUSDT")
                        loka_price = float(ticker["price"])
                        loka_value = total * loka_price
                        total_value += loka_value
                        print(f"🏆 LOKA: {total:.2f} tokens = ${loka_value:.2f}")
                    except:
                        print(f"🏆 LOKA: {total:.2f} tokens")
                elif balance["asset"] == "USDT":
                    print(f"💰 USDT remaining: ${total:.2f}")
                    total_value += total

        print(f"\n🎯 LOKA ALLOCATION INCREASED!")
        print(f"🚀 CONSOLIDATION PROGRESS MADE!")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    final_loka_buy()
