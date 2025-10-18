#!/usr/bin/env python3
"""
Auto-Start Automated Trading - No confirmation needed
Immediately starts the automated trading system
"""

import subprocess
import sys
import os
from datetime import datetime


def auto_start_trading():
    """Auto-start the trading system"""
    print("🚀 AUTO-STARTING AUTOMATED TRADING SYSTEM")
    print("=" * 50)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("🤖 System Configuration:")
    print("• Monitor every 5 minutes")
    print("• Profit taking: +10%")
    print("• Stop loss: -5%")
    print("• Follow trends: >5%")
    print("• Min trade: $10")
    print("• Max allocation: 80%")
    print()
    print("🔥 SYSTEM IS NOW RUNNING AUTOMATICALLY!")
    print("🔄 Check status anytime with: python3 quick_status.py")
    print("🛑 Stop with: Ctrl+C or kill the process")
    print()
    print("=" * 50)

    # Create auto-trading script
    auto_script = """#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from binance.client import Client
from dotenv import load_dotenv
import time
import logging
from datetime import datetime
import json

# Import our trading system
exec(open('automated_trading_system.py').read())

# Auto-start without confirmation
trader = AutomatedTradingSystem()
print("🚀 AUTO-STARTING...")
trader.start_automated_trading()
"""

    # Write and execute
    with open("auto_trader.py", "w") as f:
        f.write(auto_script)

    # Make executable
    os.chmod("auto_trader.py", 0o755)

    # Start in background
    print("🔄 Launching automated trader...")

    # Use subprocess to run in background
    process = subprocess.Popen(
        [sys.executable, "auto_trader.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print(f"✅ Automated trading started! Process ID: {process.pid}")
    print()
    print("📊 Monitor with: python3 quick_status.py")
    print("🏠 This script will now exit, but trading continues in background")

    return process.pid


if __name__ == "__main__":
    try:
        pid = auto_start_trading()
        print(f"\n🎉 SUCCESS! Automated trading is running (PID: {pid})")
    except Exception as e:
        print(f"❌ Error starting automated trading: {e}")
