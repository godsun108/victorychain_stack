#!/usr/bin/env python3

"""
📊 PORTFOLIO VIEWER
Quick view of all current holdings
"""

import os
import sys
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    api_key = os.getenv("BINANCEUS_KEY")
    api_secret = os.getenv("BINANCEUS_SECRET")

    if not api_key or not api_secret:
        print("❌ Error: Binance API credentials not found!")
        print("Please set BINANCEUS_KEY and BINANCEUS_SECRET in your .env file")
        sys.exit(1)

    # Initialize Binance client for US
    client = Client(api_key, api_secret, tld="us")

    try:
        account = client.get_account()
        total_usdt_value = 0.0
        holdings_count = 0

        print("\n📊 CURRENT PORTFOLIO HOLDINGS:")
        print("=" * 70)

        for balance in account["balances"]:
            asset = balance["asset"]
            free_balance = float(balance["free"])
            locked_balance = float(balance["locked"])
            total_balance = free_balance + locked_balance

            if total_balance > 0:
                holdings_count += 1

                if asset == "USDT":
                    usdt_value = total_balance
                    total_usdt_value += usdt_value
                    print(f"💰 {asset:<12} {total_balance:>15.8f} (${usdt_value:.2f})")
                else:
                    # Get current price for non-USDT assets
                    try:
                        symbol = f"{asset}USDT"
                        ticker = client.get_symbol_ticker(symbol=symbol)
                        price = float(ticker["price"])
                        usdt_value = total_balance * price
                        total_usdt_value += usdt_value

                        print(
                            f"📈 {asset:<12} {total_balance:>15.8f} @ ${price:.6f} = ${usdt_value:.2f}"
                        )

                        if locked_balance > 0:
                            print(
                                f"   └─ Free: {free_balance:.8f}, Locked: {locked_balance:.8f}"
                            )

                    except BinanceAPIException as e:
                        if "Invalid symbol" not in str(e):
                            print(
                                f"⚠️  {asset:<12} {total_balance:>15.8f} (Price unavailable)"
                            )

        print("=" * 70)
        print(f"💼 TOTAL PORTFOLIO VALUE: ${total_usdt_value:.2f}")
        print(f"📊 TOTAL HOLDINGS: {holdings_count} different assets")

        if holdings_count > 1:
            print(f"\n💡 To consolidate all holdings into one token, run:")
            print(f"   python3 portfolio_consolidator.py [TARGET_SYMBOL]")
            print(f"   Example: python3 portfolio_consolidator.py MAGICUSDT")

    except Exception as e:
        print(f"❌ Error getting portfolio: {e}")


if __name__ == "__main__":
    main()
