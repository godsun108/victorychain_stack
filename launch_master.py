#!/usr/bin/env python3

"""
🚀 VICTORYCHAIN MASTER LAUNCHER
Complete automation suite for portfolio management
"""

import os
import sys
import subprocess
from datetime import datetime


def show_banner():
    print(
        """
🚀 VICTORYCHAIN AUTOMATION SUITE
═══════════════════════════════════════════════════════════════════════
🤖 Claude-Powered Portfolio Management System
💎 Automated Buy & Hold Investing
🔄 Intelligent Portfolio Consolidation
⚡ Real-time Market Analysis
═══════════════════════════════════════════════════════════════════════
    """
    )


def main():
    show_banner()
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        # Portfolio Consolidation Commands
        if command == "consolidate":
            print("🔄 Running automated portfolio consolidation...")
            subprocess.run(["python3", "claude_auto_consolidator.py"])

        elif command == "consolidate-schedule":
            print("⏰ Starting consolidation scheduler...")
            subprocess.run(["python3", "auto_consolidation_scheduler.py", "start"])

        # Buy and Hold Commands
        elif command == "buy-hold":
            print("💎 Running buy and hold analysis...")
            subprocess.run(["python3", "claude_buy_hold.py"])

        elif command == "buy-hold-daily":
            print("📅 Setting up daily buy and hold automation...")
            subprocess.run(["python3", "buy_hold_scheduler.py", "daily"])
            subprocess.run(["python3", "buy_hold_scheduler.py", "enable"])

        elif command == "buy-hold-weekly":
            print("📅 Setting up weekly buy and hold automation...")
            subprocess.run(["python3", "buy_hold_scheduler.py", "weekly"])
            subprocess.run(["python3", "buy_hold_scheduler.py", "enable"])

        # Portfolio Analysis Commands
        elif command == "portfolio":
            print("💼 Viewing portfolio status...")
            subprocess.run(["python3", "view_portfolio.py"])

        elif command == "analysis":
            print("📊 Running comprehensive market analysis...")
            subprocess.run(["python3", "launch_live_trading.py"])

        # System Management Commands
        elif command == "status":
            print("📊 SYSTEM STATUS OVERVIEW")
            print("=" * 50)

            print("\n💼 Portfolio Status:")
            subprocess.run(["python3", "view_portfolio.py"])

            print("\n💎 Buy & Hold Status:")
            subprocess.run(["python3", "claude_buy_hold.py", "status"])

            print("\n🔄 Consolidation History:")
            if os.path.exists("consolidation_log.json"):
                print("   ✅ Consolidation history available")
            else:
                print("   📄 No consolidation history")

            print("\n💎 Buy & Hold History:")
            if os.path.exists("buy_hold_history.json"):
                print("   ✅ Buy & hold history available")
            else:
                print("   📄 No buy & hold history")

        elif command == "help" or command == "-h" or command == "--help":
            show_help()

        else:
            print(f"❌ Unknown command: {command}")
            show_help()
    else:
        # Default: Interactive mode
        show_interactive_menu()


def show_help():
    print(
        """
🚀 VICTORYCHAIN MASTER LAUNCHER COMMANDS:

PORTFOLIO CONSOLIDATION:
  consolidate              - Run automated Claude-powered consolidation
  consolidate-schedule     - Start automated consolidation scheduler

BUY AND HOLD INVESTING:
  buy-hold                 - Run single buy and hold analysis cycle
  buy-hold-daily          - Enable daily automated investing
  buy-hold-weekly         - Enable weekly automated investing

PORTFOLIO ANALYSIS:
  portfolio               - View current portfolio breakdown
  analysis                - Run comprehensive market analysis
  status                  - Show complete system status

EXAMPLES:
  python3 launch_master.py consolidate        # Consolidate portfolio
  python3 launch_master.py buy-hold          # Buy and hold cycle
  python3 launch_master.py buy-hold-daily    # Daily automation
  python3 launch_master.py portfolio         # Portfolio status
  python3 launch_master.py status            # Full system status

AUTOMATION FEATURES:
• Claude AI analyzes market conditions and opportunities
• Automated portfolio consolidation to top performers
• Intelligent buy and hold investing with risk management
• Scheduled execution with safety limits and cooldowns
• Comprehensive logging and performance tracking
    """
    )


def show_interactive_menu():
    print("\n🎯 INTERACTIVE MODE - Choose an action:")
    print("=" * 50)
    print("1. 🔄 Consolidate Portfolio (All → Single Token)")
    print("2. 💎 Buy & Hold Analysis (Long-term Investing)")
    print("3. 💼 View Portfolio Status")
    print("4. 📊 Market Analysis")
    print("5. ⚙️  Setup Automation")
    print("6. 📊 System Status")
    print("7. ❓ Help")
    print("8. 🚪 Exit")

    try:
        choice = input("\nEnter choice (1-8): ").strip()

        if choice == "1":
            subprocess.run(["python3", "claude_auto_consolidator.py"])
        elif choice == "2":
            subprocess.run(["python3", "claude_buy_hold.py"])
        elif choice == "3":
            subprocess.run(["python3", "view_portfolio.py"])
        elif choice == "4":
            subprocess.run(["python3", "launch_live_trading.py"])
        elif choice == "5":
            show_automation_menu()
        elif choice == "6":
            subprocess.run([sys.executable, __file__, "status"])
        elif choice == "7":
            show_help()
        elif choice == "8":
            print("👋 Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice")

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)


def show_automation_menu():
    print("\n⚙️  AUTOMATION SETUP:")
    print("=" * 30)
    print("1. 📅 Daily Buy & Hold")
    print("2. 📅 Weekly Buy & Hold")
    print("3. ⏰ Consolidation Scheduler")
    print("4. 🔙 Back to Main Menu")

    try:
        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            subprocess.run(["python3", "buy_hold_scheduler.py", "daily"])
            subprocess.run(["python3", "buy_hold_scheduler.py", "enable"])
            print("✅ Daily buy & hold automation enabled")
        elif choice == "2":
            subprocess.run(["python3", "buy_hold_scheduler.py", "weekly"])
            subprocess.run(["python3", "buy_hold_scheduler.py", "enable"])
            print("✅ Weekly buy & hold automation enabled")
        elif choice == "3":
            subprocess.run(["python3", "auto_consolidation_scheduler.py", "start"])
        elif choice == "4":
            show_interactive_menu()
        else:
            print("❌ Invalid choice")

    except KeyboardInterrupt:
        print("\n👋 Returning to main menu...")
        show_interactive_menu()


if __name__ == "__main__":
    main()
