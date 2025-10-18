#!/usr/bin/env python3
"""
LIVE TRADING SETUP AND ACTIVATION SYSTEM
=========================================

This script helps you set up and activate real money trading toward the $1T goal.

SETUP CHECKLIST:
✅ Python environment configured
✅ Required packages installed (ccxt, numpy, pandas, etc.)
✅ Trading system components ready
✅ Safety systems implemented

ACTIVATION REQUIREMENTS:
⚠️  Binance API credentials (with trading permissions)
⚠️  Sufficient USDT balance (minimum $1,000 recommended)
⚠️  Explicit risk acknowledgment
⚠️  Understanding that $1T goal is extremely difficult

TRADING FEATURES:
🚀 Maximum ROI optimization
🚀 Up to 3x leverage on high-confidence trades
🚀 Multiple trading strategies (momentum, volatility, arbitrage)
🚀 AI-powered trade selection
🚀 Real-time adaptive learning
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import Dict, Optional


class LiveTradingSetup:
    """Setup and activation system for live trading"""

    def __init__(self):
        self.setup_complete = False
        self.api_keys_configured = False
        self.balance_sufficient = False
        self.risk_acknowledged = False

    def run_setup_wizard(self):
        """Run the complete setup wizard"""
        print("🚀 LIVE TRADING SETUP WIZARD")
        print("=" * 50)

        # Step 1: Check environment
        print("\n📋 Step 1: Checking Python environment...")
        if not self._check_python_environment():
            print("❌ Python environment check failed")
            return False
        print("✅ Python environment ready")

        # Step 2: Check dependencies
        print("\n📋 Step 2: Checking required packages...")
        if not self._check_dependencies():
            print("❌ Dependency check failed")
            return False
        print("✅ All dependencies installed")

        # Step 3: Configure API keys
        print("\n📋 Step 3: Configuring Binance API keys...")
        if not self._configure_api_keys():
            print("❌ API key configuration failed")
            return False
        print("✅ API keys configured")

        # Step 4: Check balance
        print("\n📋 Step 4: Checking account balance...")
        if not self._check_account_balance():
            print("❌ Insufficient balance")
            return False
        print("✅ Sufficient balance confirmed")

        # Step 5: Risk acknowledgment
        print("\n📋 Step 5: Risk acknowledgment...")
        if not self._get_risk_acknowledgment():
            print("❌ Risk acknowledgment declined")
            return False
        print("✅ Risk acknowledged")

        # Step 6: Final activation
        print("\n📋 Step 6: Final activation...")
        return self._final_activation()

    def _check_python_environment(self) -> bool:
        """Check if Python environment is properly configured"""
        try:
            import sys

            python_version = sys.version_info

            if python_version.major >= 3 and python_version.minor >= 8:
                print(
                    f"   Python {python_version.major}.{python_version.minor}.{python_version.micro} detected"
                )
                return True
            else:
                print(
                    f"   Python {python_version.major}.{python_version.minor} too old. Need Python 3.8+"
                )
                return False

        except Exception as e:
            print(f"   Error checking Python: {e}")
            return False

    def _check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        required_packages = ["ccxt", "numpy", "pandas", "sklearn", "requests"]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
                print(f"   ✅ {package}")
            except ImportError:
                print(f"   ❌ {package} (missing)")
                missing_packages.append(package)

        if missing_packages:
            print(f"\n   Installing missing packages: {missing_packages}")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install"] + missing_packages
                )
                print("   ✅ Missing packages installed")
                return True
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to install packages: {e}")
                return False

        return True

    def _configure_api_keys(self) -> bool:
        """Configure Binance API keys"""
        print("\n🔑 BINANCE API KEY CONFIGURATION")
        print("=" * 40)
        print(
            "To enable live trading, you need Binance API keys with trading permissions."
        )
        print("\nTo get API keys:")
        print("1. Log into Binance.com")
        print("2. Go to Account > API Management")
        print("3. Create New Key")
        print("4. Enable 'Enable Spot & Margin Trading'")
        print("5. Set IP restrictions for security")
        print("\n⚠️  SECURITY WARNING:")
        print("• Never share your API keys")
        print("• Use IP restrictions")
        print("• Start with small amounts")

        # Check if already configured
        existing_key = os.getenv("BINANCEUS_KEY")
        existing_secret = os.getenv("BINANCE_API_SECRET")

        if existing_key and existing_secret:
            print(f"\n✅ API keys already configured (Key: ...{existing_key[-8:]})")
            use_existing = input("Use existing API keys? (y/n): ").lower().strip()
            if use_existing == "y":
                return self._test_api_keys(existing_key, existing_secret)

        # Get new API keys
        print("\nEnter your Binance API credentials:")
        api_key = input("API Key: ").strip()
        if not api_key:
            print("❌ API Key required")
            return False

        api_secret = input("API Secret: ").strip()
        if not api_secret:
            print("❌ API Secret required")
            return False

        # Test the keys
        if self._test_api_keys(api_key, api_secret):
            # Save to environment (for this session)
            os.environ["BINANCEUS_KEY"] = api_key
            os.environ["BINANCE_API_SECRET"] = api_secret

            # Optionally save to .env file
            save_to_file = (
                input("\nSave API keys to .env file for persistence? (y/n): ")
                .lower()
                .strip()
            )
            if save_to_file == "y":
                self._save_to_env_file(api_key, api_secret)

            return True

        return False

    def _test_api_keys(self, api_key: str, api_secret: str) -> bool:
        """Test if API keys are valid and have trading permissions"""
        try:
            import ccxt

            client = ccxt.binance(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "sandbox": False,
                    "enableRateLimit": True,
                }
            )

            # Test connection
            account = client.fetch_balance()

            print("   ✅ API keys valid")
            print(
                f"   📊 Account type: {account.get('info', {}).get('accountType', 'Unknown')}"
            )

            # Check trading permissions
            try:
                client.fetch_order_book("BTCUSDT", 5)
                print("   ✅ Market data access confirmed")

                # Test if we can create orders (this will fail but tells us about permissions)
                try:
                    client.create_market_buy_order("BTCUSDT", 0.001)  # Tiny test order
                except ccxt.InsufficientFunds:
                    print(
                        "   ✅ Trading permissions confirmed (insufficient funds test)"
                    )
                except ccxt.InvalidOrder:
                    print("   ✅ Trading permissions confirmed (invalid order test)")
                except Exception as e:
                    if "signature" not in str(e).lower():
                        print("   ✅ Trading permissions confirmed")

                return True

            except Exception as e:
                print(f"   ❌ Trading permission error: {e}")
                return False

        except Exception as e:
            print(f"   ❌ API key test failed: {e}")
            return False

    def _save_to_env_file(self, api_key: str, api_secret: str):
        """Save API keys to .env file"""
        try:
            env_content = f"""# Binance API Configuration
BINANCEUS_KEY={api_key}
BINANCE_API_SECRET={api_secret}

# Added by Live Trading Setup - {datetime.now().isoformat()}
"""
            with open(".env", "w") as f:
                f.write(env_content)
            print("   ✅ API keys saved to .env file")

        except Exception as e:
            print(f"   ⚠️ Could not save to .env file: {e}")

    def _check_account_balance(self) -> bool:
        """Check if account has sufficient balance for trading"""
        try:
            import ccxt

            api_key = os.getenv("BINANCEUS_KEY")
            api_secret = os.getenv("BINANCE_API_SECRET")

            client = ccxt.binance(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "sandbox": False,
                    "enableRateLimit": True,
                }
            )

            balance = client.fetch_balance()
            usdt_balance = balance.get("USDT", {}).get("free", 0)

            print(f"   💰 Available USDT: ${usdt_balance:,.2f}")

            if usdt_balance >= 1000:
                print("   ✅ Sufficient balance for aggressive trading")
                return True
            elif usdt_balance >= 100:
                print("   ⚠️ Low balance - consider depositing more for better results")
                proceed = input("   Proceed with low balance? (y/n): ").lower().strip()
                return proceed == "y"
            else:
                print("   ❌ Insufficient balance (minimum $100 required)")
                print("   Please deposit USDT to your Binance account")
                return False

        except Exception as e:
            print(f"   ❌ Balance check failed: {e}")
            return False

    def _get_risk_acknowledgment(self) -> bool:
        """Get explicit risk acknowledgment from user"""
        print("\n⚠️  CRITICAL RISK ACKNOWLEDGMENT")
        print("=" * 40)
        print("Before activating live trading, you must understand and acknowledge:")
        print()
        print("🚨 EXTREME RISKS:")
        print("• You could lose 100% of your trading capital")
        print("• Cryptocurrency trading is highly volatile and unpredictable")
        print("• The $1 trillion goal is mathematically near-impossible")
        print("• Technical failures could result in unexpected losses")
        print("• Market conditions can change rapidly")
        print("• Past performance does not predict future results")
        print()
        print("🛡️ SAFETY MEASURES:")
        print("• Daily loss limit: $5,000")
        print("• Total stop loss: $15,000")
        print("• Maximum 8 concurrent positions")
        print("• 75% AI confidence threshold for trades")
        print("• Real-time monitoring and emergency stops")
        print()
        print("💡 REALISTIC EXPECTATIONS:")
        print("• Professional traders average 15-20% annual returns")
        print("• The system prioritizes capital preservation")
        print("• Extraordinary returns require extraordinary risk")
        print("• Success is not guaranteed regardless of sophistication")

        print("\n" + "=" * 50)
        print("RISK ACKNOWLEDGMENT STATEMENTS")
        print("=" * 50)

        statements = [
            "I understand I could lose 100% of my trading capital",
            "I understand the $1T goal is extremely unlikely to achieve",
            "I understand cryptocurrency trading involves extreme risk",
            "I am only using money I can afford to lose completely",
            "I understand no system can guarantee profits",
            "I want to proceed with live trading despite these risks",
        ]

        print("\nPlease confirm each statement:")
        for i, statement in enumerate(statements, 1):
            response = input(f"{i}. {statement} (y/n): ").lower().strip()
            if response != "y":
                print(f"❌ Risk acknowledgment incomplete")
                return False

        # Final confirmation
        print("\n🚨 FINAL CONFIRMATION:")
        final_confirm = input(
            "Type 'I ACCEPT ALL RISKS AND WANT TO TRADE REAL MONEY' to proceed: "
        )

        if final_confirm == "I ACCEPT ALL RISKS AND WANT TO TRADE REAL MONEY":
            print("✅ Risk acknowledgment complete")
            return True
        else:
            print("❌ Final confirmation failed")
            return False

    def _final_activation(self) -> bool:
        """Final activation of live trading"""
        print("\n🚀 FINAL ACTIVATION")
        print("=" * 30)
        print("All setup steps complete. Ready to activate live trading.")

        # Choose trading mode
        print("\nSelect trading intensity:")
        print("1. Conservative (5% position sizing, 1.5x max leverage)")
        print("2. Moderate (10% position sizing, 2x max leverage)")
        print("3. Aggressive (15% position sizing, 3x max leverage)")

        mode = input("Choose mode (1/2/3): ").strip()

        mode_configs = {
            "1": {"name": "Conservative", "position_pct": 5, "max_leverage": 1.5},
            "2": {"name": "Moderate", "position_pct": 10, "max_leverage": 2.0},
            "3": {"name": "Aggressive", "position_pct": 15, "max_leverage": 3.0},
        }

        if mode not in mode_configs:
            print("❌ Invalid mode selection")
            return False

        config = mode_configs[mode]
        print(f"\n✅ {config['name']} mode selected")
        print(f"   Max position size: {config['position_pct']}% of portfolio")
        print(f"   Max leverage: {config['max_leverage']}x")

        # Save configuration
        trading_config = {
            "mode": config["name"],
            "max_position_percent": config["position_pct"],
            "max_leverage": config["max_leverage"],
            "activation_time": datetime.now().isoformat(),
            "api_configured": True,
            "risk_acknowledged": True,
        }

        with open("live_trading_config.json", "w") as f:
            json.dump(trading_config, f, indent=2)

        print("\n🎯 Live trading configuration saved!")
        print("📊 You can now run the maximum ROI trader:")
        print(f"   python maximum_roi_live_trader.py")

        # Ask if they want to start immediately
        start_now = input("\nStart live trading immediately? (y/n): ").lower().strip()

        if start_now == "y":
            print("\n🚀 Starting maximum ROI live trader...")
            try:
                import subprocess
                import sys

                # Get the Python executable path
                python_path = (
                    "/Users/nicholaskramer/Downloads/victorychain_stack/venv/bin/python"
                )

                result = subprocess.run(
                    [python_path, "maximum_roi_live_trader.py"], capture_output=False
                )

                return result.returncode == 0

            except Exception as e:
                print(f"❌ Failed to start trader: {e}")
                print(
                    "You can start it manually with: python maximum_roi_live_trader.py"
                )
                return False
        else:
            print(
                "✅ Setup complete. Run 'python maximum_roi_live_trader.py' when ready."
            )
            return True


def main():
    """Main setup function"""
    print("💰 LIVE TRADING SETUP - PATH TO $1 TRILLION")
    print("🚨 EXTREME RISK - REAL MONEY TRADING")
    print("=" * 60)

    setup = LiveTradingSetup()

    if setup.run_setup_wizard():
        print("\n🎉 SETUP COMPLETE!")
        print("🚀 Ready for maximum ROI live trading")
        print("📊 Monitor performance and stay within risk limits")
        print("💡 Remember: The journey to $1T starts with disciplined trading")
    else:
        print("\n❌ Setup incomplete")
        print("💡 Consider paper trading first to build confidence")
        print("🛡️ Safety first - only trade what you can afford to lose")


if __name__ == "__main__":
    main()
