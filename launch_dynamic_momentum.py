#!/usr/bin/env python3
"""
Launch Dynamic Momentum Trading Strategy
========================================

Quick launcher for the dynamic momentum trading system.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.strategies.dynamic_momentum_trader import DynamicMomentumTrader


async def demo_momentum_trading():
    """Demo the dynamic momentum trading strategy"""
    print("🚀 DYNAMIC MOMENTUM TRADING DEMO")
    print("=" * 50)
    print("This strategy implements:")
    print("• Tracks highest momentum token continuously")
    print("• Tight stop losses (22% initial, 5% when profitable)")
    print("• Dynamic position sizing based on performance")
    print("• Trailing stops that tighten as profits increase")
    print("• Auto-rebalancing when momentum shifts")
    print("=" * 50)

    trader = DynamicMomentumTrader()

    # Get current highest momentum token
    print("\n🔍 Finding highest momentum token...")
    highest_token, momentum = await trader.get_highest_momentum_token()
    print(f"📈 Highest momentum: {highest_token} (score: {momentum:.2f})")

    # Get current price
    price = await trader.get_current_price(highest_token)
    print(f"💰 Current price: ${price:.4f}")

    # Calculate initial stop loss
    stop_loss = price * (1 - trader.config.initial_stop_loss_pct)
    print(
        f"🛑 Initial stop loss: ${stop_loss:.4f} ({trader.config.initial_stop_loss_pct*100:.0f}% below entry)"
    )

    # Show allocation progression
    print(f"\n📊 Allocation progression:")
    for gains in range(6):
        allocation = trader.calculate_allocation(gains, 0.15)
        print(f"   {gains} consecutive gains: {allocation*100:.1f}% allocation")

    # Show stop loss tightening
    print(f"\n🎯 Stop loss tightening as profit increases:")
    entry_price = price
    for profit in [0, 0.05, 0.10, 0.15, 0.20]:
        current_price = entry_price * (1 + profit)
        stop = trader.calculate_stop_loss(entry_price, current_price, profit)
        stop_pct = (entry_price - stop) / entry_price * 100
        print(
            f"   {profit*100:>3.0f}% profit: Stop at ${stop:.4f} ({stop_pct:.1f}% below entry)"
        )

    print(f"\n✅ Demo complete! Ready to trade with dynamic stops.")
    print(f"💡 Key features:")
    print(f"   • Max allocation: {trader.config.max_allocation_pct*100:.0f}%")
    print(f"   • Momentum threshold: {trader.config.min_momentum_threshold}")
    print(f"   • Check interval: {trader.config.momentum_check_interval}s")

    return trader


async def live_trading_session():
    """Start a live trading session (demo mode)"""
    print("\n🎮 Starting live trading session...")
    print("Press Ctrl+C to stop")

    trader = await demo_momentum_trading()

    try:
        # Start trading loop for a short demo
        print("\n🚀 Starting trading loop (demo mode)...")
        trader.config.momentum_check_interval = 30  # Check every 30 seconds for demo

        # Run for 5 minutes as demo
        demo_tasks = [trader.trading_loop(), asyncio.sleep(300)]  # 5 minute demo

        done, pending = await asyncio.wait(
            demo_tasks, return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel remaining tasks
        for task in pending:
            task.cancel()

        trader.stop_trading()
        print("\n✅ Demo trading session completed!")

    except KeyboardInterrupt:
        print("\n🛑 Trading stopped by user")
        trader.stop_trading()


def main():
    """Main function"""
    print("🎯 DYNAMIC MOMENTUM TRADING LAUNCHER")
    print("=" * 40)
    print("1. Demo mode - Show strategy features")
    print("2. Live trading session (5 min demo)")
    print("3. Exit")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == "1":
        asyncio.run(demo_momentum_trading())
    elif choice == "2":
        asyncio.run(live_trading_session())
    elif choice == "3":
        print("👋 Goodbye!")
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
