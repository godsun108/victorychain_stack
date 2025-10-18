#!/usr/bin/env python3

"""
💎 BUY AND HOLD SYSTEM LAUNCHER
Comprehensive launcher for Claude-powered buy and hold investing
"""

import os
import sys
import subprocess
from datetime import datetime


def main():
    print("💎 CLAUDE-POWERED BUY AND HOLD SYSTEM")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "run":
            print("💎 Running buy and hold analysis and execution...")
            subprocess.run(["python3", "claude_buy_hold.py", "run"])

        elif command == "status":
            print("📊 Checking portfolio and system status...")
            subprocess.run(["python3", "claude_buy_hold.py", "status"])

        elif command == "history":
            print("📊 Showing performance history...")
            subprocess.run(["python3", "claude_buy_hold.py", "history"])

        elif command == "schedule-start":
            print("⏰ Starting automated buy and hold scheduler...")
            subprocess.run(["python3", "buy_hold_scheduler.py", "start"])

        elif command == "schedule-daily":
            print("📅 Setting up daily automated buy and hold...")
            subprocess.run(["python3", "buy_hold_scheduler.py", "daily"])
            subprocess.run(["python3", "buy_hold_scheduler.py", "enable"])

        elif command == "schedule-weekly":
            print("📅 Setting up weekly automated buy and hold...")
            subprocess.run(["python3", "buy_hold_scheduler.py", "weekly"])
            subprocess.run(["python3", "buy_hold_scheduler.py", "enable"])

        elif command == "portfolio":
            print("💼 Viewing complete portfolio...")
            subprocess.run(["python3", "view_portfolio.py"])

        elif command == "test":
            print("🧪 Running test buy and hold cycle...")
            subprocess.run(["python3", "buy_hold_scheduler.py", "run-now"])

        else:
            show_help()
    else:
        # Default: run single buy and hold cycle
        print("💎 Running single buy and hold cycle...")
        subprocess.run(["python3", "claude_buy_hold.py", "run"])


def show_help():
    print(
        """
💎 BUY AND HOLD SYSTEM OPTIONS:

Usage: python3 launch_buy_hold.py [COMMAND]

Commands:
  run             - Run single buy and hold analysis and execution
  status          - Show portfolio status and metrics
  history         - Show performance history and logs
  portfolio       - View complete portfolio breakdown
  test            - Run test cycle immediately
  
  schedule-start  - Start automated scheduler service
  schedule-daily  - Enable daily automated investing
  schedule-weekly - Enable weekly automated investing

Investment Strategy:
  • Claude AI analyzes market for high-quality long-term opportunities
  • Builds diversified portfolio of 3-5 positions
  • Targets 20% allocation per position
  • Focuses on fundamental strength over short-term momentum
  • Automated profit taking at 100% gains
  • Stop loss protection at 60% losses
  • Minimum $25 per investment for cost efficiency

Examples:
  python3 launch_buy_hold.py run              # Single cycle
  python3 launch_buy_hold.py status           # Portfolio status
  python3 launch_buy_hold.py schedule-daily   # Daily automation
  python3 launch_buy_hold.py schedule-weekly  # Weekly automation
    """
    )


if __name__ == "__main__":
    main()
