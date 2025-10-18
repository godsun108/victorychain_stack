#!/usr/bin/env python3

"""
🔧 ROBUST CONSOLIDATOR - Handles Binance precision requirements
"""

import os
import sys
import time
import math
from decimal import Decimal, ROUND_DOWN
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_precision_info(client, symbol):
    """Get precision info for a symbol"""
    try:
        symbol_info = client.get_symbol_info(symbol)

        lot_size_filter = None
        price_filter = None
        min_notional_filter = None

        for filter_info in symbol_info["filters"]:
            if filter_info["filterType"] == "LOT_SIZE":
                lot_size_filter = filter_info
            elif filter_info["filterType"] == "PRICE_FILTER":
                price_filter = filter_info
            elif filter_info["filterType"] == "MIN_NOTIONAL":
                min_notional_filter = filter_info

        return {
            "stepSize": (
                float(lot_size_filter["stepSize"]) if lot_size_filter else 0.00000001
            ),
            "minQty": (
                float(lot_size_filter["minQty"]) if lot_size_filter else 0.00000001
            ),
            "maxQty": (
                float(lot_size_filter["maxQty"]) if lot_size_filter else 999999999
            ),
            "tickSize": float(price_filter["tickSize"]) if price_filter else 0.00000001,
            "minNotional": (
                float(min_notional_filter["minNotional"])
                if min_notional_filter
                else 10.0
            ),
        }
    except:
        return {
            "stepSize": 0.00000001,
            "minQty": 0.00000001,
            "maxQty": 999999999,
            "tickSize": 0.00000001,
            "minNotional": 10.0,
        }


def format_quantity(quantity, step_size):
    """Format quantity according to step size"""
    if step_size >= 1:
        return int(quantity)

    precision = 0
    step_str = f"{step_size:.10f}".rstrip("0")
    if "." in step_str:
        precision = len(step_str.split(".")[1])

    formatted = math.floor(quantity / step_size) * step_size
    return round(formatted, precision)


def main():
    api_key = os.getenv("BINANCEUS_KEY")
    api_secret = os.getenv("BINANCEUS_SECRET")

    if not api_key or not api_secret:
        print("❌ Error: Binance API credentials not found!")
        sys.exit(1)

    client = Client(api_key, api_secret, tld="us")
    target_symbol = "MAGICUSDT"

    print(f"🔧 ROBUST CONSOLIDATION TO {target_symbol}")
    print("=" * 50)

    try:
        # Get current holdings
        account = client.get_account()
        total_usdt_received = 0.0

        print("📊 Current holdings:")

        # Get current USDT balance
        for balance in account["balances"]:
            if balance["asset"] == "USDT":
                usdt_balance = float(balance["free"])
                total_usdt_received += usdt_balance
                print(f"   USDT: ${usdt_balance:.2f}")
                break

        # Process each non-USDT, non-MAGIC asset
        for balance in account["balances"]:
            asset = balance["asset"]
            free_balance = float(balance["free"])

            if free_balance > 0 and asset not in ["USDT", "MAGIC"]:
                try:
                    symbol = f"{asset}USDT"

                    # Get current price
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    price = float(ticker["price"])
                    usdt_value = free_balance * price

                    print(f"   {asset}: {free_balance:.8f} = ${usdt_value:.2f}")

                    if usdt_value >= 5.0:  # Only liquidate positions worth > $5
                        # Get precision info
                        precision_info = get_precision_info(client, symbol)

                        # Format quantity according to step size
                        sell_quantity = format_quantity(
                            free_balance, precision_info["stepSize"]
                        )

                        # Check if quantity meets minimum requirements
                        if (
                            sell_quantity >= precision_info["minQty"]
                            and sell_quantity * price >= precision_info["minNotional"]
                        ):

                            print(f"🔄 Selling {sell_quantity} {asset}...")

                            order = client.order_market_sell(
                                symbol=symbol, quantity=sell_quantity
                            )

                            usdt_received = float(order["cummulativeQuoteQty"])
                            total_usdt_received += usdt_received

                            print(f"✅ Sold {asset}: ${usdt_received:.2f}")
                            time.sleep(1)  # Rate limiting
                        else:
                            print(f"⚠️  {asset}: Below minimum trade requirements")
                    else:
                        print(f"⚠️  {asset}: Value too small (${usdt_value:.2f})")

                except Exception as e:
                    print(f"❌ Error with {asset}: {e}")
                    continue

        print(f"\n💰 Total USDT available: ${total_usdt_received:.2f}")

        # Buy MAGICUSDT with proper precision
        if total_usdt_received >= 10.0:
            try:
                # Use 99% to leave buffer for fees
                buy_amount = total_usdt_received * 0.99

                # Get precision info for MAGICUSDT
                precision_info = get_precision_info(client, target_symbol)

                # Round down to acceptable precision
                buy_amount = (
                    math.floor(buy_amount * 100) / 100
                )  # Round to 2 decimal places

                print(f"🎯 Buying {target_symbol} with ${buy_amount:.2f}...")

                order = client.order_market_buy(
                    symbol=target_symbol, quoteOrderQty=buy_amount
                )

                executed_qty = float(order["executedQty"])
                total_cost = float(order["cummulativeQuoteQty"])
                avg_price = total_cost / executed_qty if executed_qty > 0 else 0

                print(
                    f"✅ Bought {target_symbol}: {executed_qty:.8f} @ ${avg_price:.6f}"
                )
                print(f"   Total cost: ${total_cost:.2f}")
                print(f"🎉 CONSOLIDATION COMPLETE!")

                # Show final portfolio
                print(f"\n📊 FINAL PORTFOLIO:")
                account = client.get_account()
                total_final_value = 0.0

                for balance in account["balances"]:
                    total_bal = float(balance["free"]) + float(balance["locked"])
                    if total_bal > 0:
                        asset = balance["asset"]

                        if asset == "USDT":
                            print(f"   💰 {asset}: {total_bal:.8f} (${total_bal:.2f})")
                            total_final_value += total_bal
                        else:
                            try:
                                symbol = f"{asset}USDT"
                                ticker = client.get_symbol_ticker(symbol=symbol)
                                price = float(ticker["price"])
                                usdt_value = total_bal * price
                                print(
                                    f"   📈 {asset}: {total_bal:.8f} = ${usdt_value:.2f}"
                                )
                                total_final_value += usdt_value
                            except:
                                print(f"   ❓ {asset}: {total_bal:.8f}")

                print(f"\n💼 TOTAL FINAL VALUE: ${total_final_value:.2f}")

            except Exception as e:
                print(f"❌ Error buying {target_symbol}: {e}")
        else:
            print(f"⚠️  Not enough USDT (${total_usdt_received:.2f}) for minimum trade")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
