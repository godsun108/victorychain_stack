#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from binance.client import Client

load_dotenv()
client = Client(
    api_key=os.getenv("BINANCEUS_KEY"),
    api_secret=os.getenv("BINANCEUS_SECRET"),
    tld="us",
)

print("🏦 CURRENT PORTFOLIO BALANCE:")
print("=" * 50)
account = client.get_account()
total_value = 0

for balance in account["balances"]:
    free = float(balance["free"])
    locked = float(balance["locked"])
    total = free + locked

    if total > 0.01:  # Only show meaningful balances
        if balance["asset"] == "USDT":
            usd_value = total
            print(f'{balance["asset"]:8s} | {total:12.4f} | ${usd_value:8.2f}')
            total_value += usd_value
        else:
            try:
                ticker = client.get_symbol_ticker(symbol=balance["asset"] + "USDT")
                price = float(ticker["price"])
                usd_value = total * price
                if usd_value > 0.01:
                    total_value += usd_value
                    print(
                        f'{balance["asset"]:8s} | {total:12.4f} | ${usd_value:8.2f} (@ ${price:.6f})'
                    )
            except Exception as e:
                if total > 0.1:  # Only show if significant amount
                    print(
                        f'{balance["asset"]:8s} | {total:12.4f} | ${0:8.2f} (no USDT pair)'
                    )

print("-" * 50)
print(f"TOTAL VALUE: ${total_value:.2f}")
