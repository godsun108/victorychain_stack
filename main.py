#!/usr/bin/env python3
"""
🏆 VICTORYCHAIN MAIN APPLICATION
Entry point for the VictoryChain trading system
Author: Senior Developer
Version: 2.0.0
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def main():
    parser = argparse.ArgumentParser(description="VictoryChain Trading System")
    parser.add_argument(
        "--mode",
        choices=["core", "web", "momentum", "analyze"],
        default="core",
        help="Application mode to run",
    )
    parser.add_argument(
        "--config",
        default="config/victorychain_config.toml",
        help="Configuration file path",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print("🏆 VictoryChain Trading System v2.0.0")
    print("=" * 50)

    try:
        if args.mode == "core":
            from core.victorychain_core_v2 import VictoryChainCore

            print("🚀 Starting VictoryChain Core...")
            app = VictoryChainCore()
            app.run()

        elif args.mode == "web":
            from web.web_dashboard import main as web_main

            print("🌐 Starting Web Dashboard...")
            web_main()

        elif args.mode == "momentum":
            from strategies.momentum_trader_v2 import MomentumTrader

            print("📈 Starting Momentum Trader...")
            trader = MomentumTrader()
            trader.run()

        elif args.mode == "analyze":
            from utilities.all_tokens_report import main as analyze_main

            print("📊 Starting Token Analysis...")
            analyze_main()

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print(
            "Please ensure all dependencies are installed with: pip install -r requirements.txt"
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
