#!/usr/bin/env python3

"""
🚀 QUICK CONSOLIDATOR - Consolidate to MAGICUSDT
Auto-consolidates all holdings to MAGICUSDT (your top performer)
"""

import os
import sys
import time
from decimal import Decimal, ROUND_DOWN
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    api_key = os.getenv("BINANCEUS_KEY")
    api_secret = os.getenv("BINANCEUS_SECRET")

    if not api_key or not api_secret:
        print("❌ Error: Binance API credentials not found!")
        sys.exit(1)

    client = Client(api_key, api_secret, tld="us")
    target_symbol = "MAGICUSDT"

    print(f"🚀 QUICK CONSOLIDATION TO {target_symbol}")
    print("=" * 50)

    try:
        # Get current holdings
        account = client.get_account()
        total_usdt_received = 0.0
        positions_to_sell = []

        print("📊 Current holdings to liquidate:")

        for balance in account["balances"]:
            asset = balance["asset"]
            free_balance = float(balance["free"])
            total_balance = free_balance + float(balance["locked"])

            if total_balance > 0 and asset not in ["USDT", "MAGIC"]:
                try:
                    symbol = f"{asset}USDT"
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    price = float(ticker["price"])
                    usdt_value = total_balance * price

                    if usdt_value >= 1.0:  # Only liquidate positions worth > $1
                        positions_to_sell.append(
                            {
                                "asset": asset,
                                "symbol": symbol,
                                "quantity": free_balance,
                                "usdt_value": usdt_value,
                            }
                        )
                        print(f"   {asset}: {free_balance:.8f} = ${usdt_value:.2f}")
                except:
                    continue

        # Get current USDT balance
        for balance in account["balances"]:
            if balance["asset"] == "USDT":
                usdt_balance = float(balance["free"])
                total_usdt_received += usdt_balance
                print(f"   USDT: ${usdt_balance:.2f}")
                break

        if not positions_to_sell:
            print("ℹ️  No significant positions to liquidate")
            return

        print(f"\nLiquidating {len(positions_to_sell)} positions...")

        # Liquidate positions
        for position in positions_to_sell:
            try:
                symbol = position["symbol"]
                quantity = position["quantity"]

                if quantity <= 0:
                    continue

                # Get step size for precision
                symbol_info = client.get_symbol_info(symbol)
                step_size = None

                for filter_info in symbol_info["filters"]:
                    if filter_info["filterType"] == "LOT_SIZE":
                        step_size = float(filter_info["stepSize"])
                        break

                if step_size:
                    precision = len(str(step_size).rstrip("0").split(".")[-1])
                    quantity = float(
                        Decimal(str(quantity)).quantize(
                            Decimal(str(step_size)), rounding=ROUND_DOWN
                        )
                    )

                if quantity <= 0:
                    print(f"⚠️  {position['asset']}: quantity too small")
                    continue

                print(f"🔄 Selling {quantity:.8f} {position['asset']}...")

                order = client.order_market_sell(symbol=symbol, quantity=quantity)

                usdt_received = float(order["cummulativeQuoteQty"])
                total_usdt_received += usdt_received

                print(f"✅ Sold {position['asset']}: ${usdt_received:.2f}")
                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"❌ Error selling {position['asset']}: {e}")
                continue

        print(f"\n💰 Total USDT available: ${total_usdt_received:.2f}")

        # Buy MAGICUSDT
        if total_usdt_received >= 10.0:
            try:
                # Use 99% to leave buffer for fees
                buy_amount = total_usdt_received * 0.99

                print(f"🎯 Buying {target_symbol} with ${buy_amount:.2f}...")

                order = client.order_market_buy(
                    symbol=target_symbol, quoteOrderQty=buy_amount
                )

                executed_qty = float(order["executedQty"])
                avg_price = float(order["fills"][0]["price"])

                print(
                    f"✅ Bought {target_symbol}: {executed_qty:.8f} @ ${avg_price:.6f}"
                )
                print(f"🎉 CONSOLIDATION COMPLETE!")

                # Show final portfolio
                print(f"\n📊 FINAL PORTFOLIO:")
                account = client.get_account()
                for balance in account["balances"]:
                    if float(balance["free"]) + float(balance["locked"]) > 0:
                        asset = balance["asset"]
                        total_bal = float(balance["free"]) + float(balance["locked"])
                        print(f"   {asset}: {total_bal:.8f}")

            except Exception as e:
                print(f"❌ Error buying {target_symbol}: {e}")
        else:
            print(f"⚠️  Not enough USDT (${total_usdt_received:.2f}) for minimum trade")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
