#!/usr/bin/env python3
"""
All Tokens List - Shows ALL available tokens on Binance US
"""

import requests
import json
from typing import List, Dict


def get_all_binance_us_symbols() -> List[Dict]:
    """Get all available symbols from Binance US"""
    try:
        # Get exchange info
        url = "https://api.binance.us/api/v3/exchangeInfo"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        symbols = data.get("symbols", [])

        # Filter for active trading pairs
        active_symbols = [
            symbol for symbol in symbols if symbol.get("status") == "TRADING"
        ]

        return active_symbols
    except Exception as e:
        print(f"Error fetching symbols: {e}")
        return []


def categorize_symbols(symbols: List[Dict]) -> Dict[str, List[str]]:
    """Categorize symbols by quote asset"""
    categories = {
        "USDT": [],
        "USD": [],
        "BTC": [],
        "ETH": [],
        "BNB": [],
        "BUSD": [],
        "Other": [],
    }

    for symbol in symbols:
        symbol_name = symbol.get("symbol", "")
        quote_asset = symbol.get("quoteAsset", "")

        if quote_asset in categories:
            categories[quote_asset].append(symbol_name)
        else:
            categories["Other"].append(symbol_name)

    return categories


def display_all_tokens():
    """Display all available tokens categorized by quote asset"""
    print("🏛️ ALL AVAILABLE TOKENS ON BINANCE US")
    print("=" * 60)

    symbols = get_all_binance_us_symbols()
    if not symbols:
        print("❌ Failed to fetch symbols")
        return

    categories = categorize_symbols(symbols)

    total_count = 0
    for category, tokens in categories.items():
        if tokens:
            print(f"\n💰 {category} PAIRS ({len(tokens)} tokens):")
            print("-" * 40)

            # Sort tokens for better readability
            tokens.sort()

            # Display in columns
            for i, token in enumerate(tokens):
                if i % 3 == 0:
                    print()
                print(f"{token:20}", end="")

            print()  # New line after each category
            total_count += len(tokens)

    print(f"\n📊 SUMMARY:")
    print(f"   Total Trading Pairs: {total_count}")
    print(f"   USDT Pairs: {len(categories['USDT'])}")
    print(f"   USD Pairs: {len(categories['USD'])}")
    print(f"   BTC Pairs: {len(categories['BTC'])}")
    print(f"   ETH Pairs: {len(categories['ETH'])}")
    print(f"   Other Pairs: {len(categories['Other'])}")


if __name__ == "__main__":
    display_all_tokens()
