#!/usr/bin/env python3

"""
CURRENT ALLOCATION DATA GENERATOR
"""

import asyncio
import json
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(__file__))


async def main():
    try:
        from real_time_opportunity_maximizer import RealTimeOpportunityMaximizer

        print("🎯 GENERATING CURRENT ALLOCATION DATA")
        print("=" * 50)

        maximizer = RealTimeOpportunityMaximizer(initial_capital=100000)

        # Get opportunities
        opportunities = await maximizer.scan_all_tokens_for_opportunities()
        print(f"📊 Found {len(opportunities)} opportunities")

        # Calculate allocations
        allocations = maximizer.calculate_optimal_allocations(opportunities)
        print(f"💰 Generated {len(allocations)} allocations")

        # Show top 5
        print(f"\n🏆 TOP 5 CURRENT ALLOCATIONS:")
        for i, alloc in enumerate(allocations[:5]):
            print(
                f"{i+1}. {alloc.symbol}: {alloc.allocation_percentage:.1%} (${alloc.allocation_amount:,.0f})"
            )
            print(f"   Expected Return: {alloc.expected_return:.1%}")

        total_allocation = sum(a.allocation_percentage for a in allocations)
        portfolio_return = sum(
            a.expected_return * a.allocation_percentage for a in allocations
        )

        print(f"\n📊 SUMMARY:")
        print(f"Total Exposure: {total_allocation:.1%}")
        print(f"Expected Return: {portfolio_return:.2%}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
