#!/usr/bin/env python3
"""
Test Stop-Loss Mechanism with Fixed Precision
"""

import os
import json
from datetime import datetime
from binance.client import Client
from dotenv import load_dotenv


def get_lot_size_precision(client, symbol):
    """Get LOT_SIZE filter information for precise quantity formatting"""
    try:
        info = client.get_symbol_info(symbol)
        for f in info["filters"]:
            if f["filterType"] == "LOT_SIZE":
                return {
                    "minQty": float(f["minQty"]),
                    "maxQty": float(f["maxQty"]),
                    "stepSize": float(f["stepSize"]),
                }
        return {"minQty": 0.00000001, "maxQty": 1000000000, "stepSize": 0.00000001}
    except:
        return {"minQty": 0.00000001, "maxQty": 1000000000, "stepSize": 0.00000001}


def format_quantity(quantity, client, symbol):
    """Format quantity according to LOT_SIZE requirements"""
    lot_info = get_lot_size_precision(client, symbol)
    step_size = lot_info["stepSize"]
    min_qty = lot_info["minQty"]

    # Round to step size precision
    if step_size >= 1:
        # For step sizes like 0.1, 1.0, etc.
        precision = 0
        temp_step = step_size
        while temp_step < 1:
            temp_step *= 10
            precision += 1
        formatted_qty = round(quantity / step_size) * step_size
        formatted_qty = round(formatted_qty, precision)
    else:
        # For very small step sizes
        precision = len(str(step_size).split(".")[-1]) if "." in str(step_size) else 0
        formatted_qty = round(quantity / step_size) * step_size
        formatted_qty = round(formatted_qty, precision)

    # Ensure minimum quantity
    if formatted_qty < min_qty:
        formatted_qty = min_qty

    return formatted_qty


def main():
    load_dotenv()
    client = Client(
        api_key=os.getenv("BINANCEUS_KEY"),
        api_secret=os.getenv("BINANCEUS_SECRET"),
        tld="us",
    )

    # Get LOKA balance and test stop-loss calculation
    print("🛑 TESTING STOP-LOSS MECHANISM")
    print("=" * 50)

    # Get current LOKA balance
    account = client.get_account()
    loka_balance = 0
    for balance in account["balances"]:
        if balance["asset"] == "LOKA" and float(balance["free"]) > 0:
            loka_balance = float(balance["free"])
            print(f"Current LOKA Balance: {loka_balance}")
            break

    if loka_balance == 0:
        print("❌ No LOKA balance found")
        return

    # Get LOT_SIZE info
    lot_info = get_lot_size_precision(client, "LOKAUSDT")
    print(f"LOKAUSDT LOT_SIZE: {lot_info}")

    # Calculate 80% stop-loss amount
    stop_loss_percentage = 0.8
    raw_amount = loka_balance * stop_loss_percentage
    formatted_amount = format_quantity(raw_amount, client, "LOKAUSDT")

    print(f"\nSTOP-LOSS CALCULATION:")
    print(f"  Raw 80% amount: {raw_amount:.8f}")
    print(f"  Formatted amount: {formatted_amount:.8f}")
    print(f"  Difference: {abs(raw_amount - formatted_amount):.8f}")

    # Test if this would work
    if formatted_amount >= lot_info["minQty"] and formatted_amount <= loka_balance:
        print(f"✅ STOP-LOSS WOULD WORK - Selling {formatted_amount} LOKA")

        # Ask user if they want to execute
        response = input(
            f"\n⚠️  EXECUTE STOP-LOSS? This will sell {formatted_amount} LOKA (y/N): "
        )
        if response.lower() == "y":
            try:
                order = client.order_market_sell(
                    symbol="LOKAUSDT", quantity=formatted_amount
                )
                print(f"✅ STOP-LOSS EXECUTED! Order ID: {order['orderId']}")
                print(f"   Sold: {formatted_amount} LOKA")

                # Log the action
                with open(
                    f'stop_loss_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                    "w",
                ) as f:
                    json.dump(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "action": "stop_loss_executed",
                            "asset": "LOKA",
                            "quantity_sold": formatted_amount,
                            "order_id": order["orderId"],
                            "reason": "Manual stop-loss test execution",
                        },
                        f,
                        indent=2,
                    )

            except Exception as e:
                print(f"❌ STOP-LOSS FAILED: {e}")
        else:
            print("⏸️  Stop-loss test cancelled")
    else:
        print(
            f"❌ STOP-LOSS WOULD FAIL - Formatted amount {formatted_amount} is invalid"
        )


if __name__ == "__main__":
    main()
