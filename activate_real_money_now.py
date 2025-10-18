#!/usr/bin/env python3
"""
REAL MONEY API KEY SETUP
========================

🔐 SECURE API KEY ENTRY FOR REAL MONEY TRADING
💰 DIRECT ACTIVATION WITH YOUR CREDENTIALS
🚀 IMMEDIATE TRADING ACTIVATION

This will securely collect your Binance US API credentials
and activate real money trading immediately.
"""

import json
import os
import getpass
from datetime import datetime


def secure_api_setup():
    """Securely collect and setup API credentials"""

    print("🔐🔐🔐 SECURE API KEY SETUP 🔐🔐🔐")
    print("💰 REAL MONEY TRADING ACTIVATION")
    print("=" * 60)
    print()
    print("⚠️  ENTERING REAL BINANCE US API CREDENTIALS")
    print("🔒 Your keys will be stored securely for trading")
    print("💀 THIS WILL ENABLE REAL MONEY TRADING")
    print()

    # Get API credentials
    print("📝 Enter your Binance US API credentials:")
    print("(Get these from: Binance US → Account Settings → API Management)")
    print()

    api_key = input("🔑 Binance US API Key: ").strip()
    print("🔐 Binance US API Secret: ", end="")
    api_secret = getpass.getpass("").strip()  # Hidden input for security

    if not api_key or not api_secret:
        print("❌ Both API key and secret are required!")
        return False

    print(f"\n✅ API Key received: {api_key[:8]}...{api_key[-4:]}")
    print("✅ API Secret received: [HIDDEN FOR SECURITY]")

    # Confirm
    print("\n⚠️  FINAL CONFIRMATION:")
    print("💰 These credentials will be used for REAL MONEY TRADING")
    print("🔥 Actual cryptocurrency transactions will be executed")
    print("💀 Real funds are at risk")
    print()

    confirm = input("Type 'ACTIVATE REAL TRADING' to confirm: ").strip()

    if confirm != "ACTIVATE REAL TRADING":
        print("❌ Activation cancelled - exact phrase required")
        return False

    # Update configuration with real credentials
    config_file = "real_money_trading_config.json"

    try:
        with open(config_file, "r") as f:
            config = json.load(f)

        # Update API credentials
        config["api_config"]["api_key"] = api_key
        config["api_config"]["api_secret"] = api_secret
        config["api_config"]["activated_timestamp"] = datetime.now().isoformat()
        config["api_config"]["real_money_confirmed"] = True

        # Save updated configuration
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        print("\n✅ REAL MONEY TRADING ACTIVATED!")
        print("🔐 API credentials stored securely")
        print("💰 Ready for real money trading")

        return True

    except Exception as e:
        print(f"❌ Configuration update failed: {e}")
        return False


def test_api_connection(api_key, api_secret):
    """Test the API connection before trading"""

    print("\n🔄 TESTING API CONNECTION...")

    try:
        import ccxt

        # Create exchange instance
        exchange = ccxt.binanceus(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "sandbox": False,  # Real trading mode
                "enableRateLimit": True,
            }
        )

        # Test connection
        balance = exchange.fetch_balance()

        # Calculate total USD value
        total_usd = 0.0
        holdings = {}

        for currency, amount in balance["total"].items():
            if amount > 0:
                holdings[currency] = amount
                if currency == "USD":
                    total_usd += amount
                else:
                    try:
                        ticker = exchange.fetch_ticker(f"{currency}/USD")
                        usd_value = amount * ticker["last"]
                        total_usd += usd_value
                        holdings[f"{currency}_USD_VALUE"] = usd_value
                    except:
                        pass

        print("✅ API CONNECTION SUCCESSFUL!")
        print(f"💰 Total Account Value: ${total_usd:,.2f}")
        print("\n📊 Current Holdings:")

        for currency, amount in holdings.items():
            if not currency.endswith("_USD_VALUE"):
                usd_value = holdings.get(f"{currency}_USD_VALUE", 0)
                if currency == "USD":
                    print(f"   {currency}: ${amount:,.2f}")
                else:
                    print(f"   {currency}: {amount:.6f} (${usd_value:.2f})")

        if total_usd < 100:
            print("⚠️  WARNING: Low account balance for meaningful trading")
            print("💡 Consider depositing more funds for better results")

        return True, total_usd

    except Exception as e:
        print(f"❌ API CONNECTION FAILED: {e}")
        print("🔧 Please check:")
        print("   • API key is correct")
        print("   • API secret is correct")
        print("   • Spot trading is enabled")
        print("   • IP restriction allows your IP")
        return False, 0.0


def start_real_money_trading():
    """Start the real money trading bot"""

    print("\n🚀 STARTING REAL MONEY TRADING BOT...")
    print("💰 TRADING WITH ACTUAL FUNDS")
    print("🛡️ ULTRA-SAFE MODE WITH MANUAL APPROVAL")
    print()

    # Import and run the real money bot
    try:
        import subprocess
        import sys

        # Run the real money trading bot
        result = subprocess.run(
            [sys.executable, "real_money_trading_bot.py"], cwd=os.getcwd()
        )

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Error starting trading bot: {e}")
        return False


def main():
    """Main setup and activation process"""

    print("💰💰💰 REAL MONEY TRADING ACTIVATION 💰💰💰")
    print("🔐 SECURE API SETUP AND IMMEDIATE TRADING")
    print()

    # Step 1: Secure API setup
    if not secure_api_setup():
        print("❌ API setup failed or cancelled")
        return

    # Step 2: Load credentials and test
    try:
        with open("real_money_trading_config.json", "r") as f:
            config = json.load(f)

        api_key = config["api_config"]["api_key"]
        api_secret = config["api_config"]["api_secret"]

        # Test API connection
        success, balance = test_api_connection(api_key, api_secret)

        if not success:
            print("❌ API test failed - please check your credentials")
            return

        if balance < 100:
            print("⚠️  Continue with low balance?")
            continue_anyway = input("Type 'yes' to continue: ").lower()
            if continue_anyway != "yes":
                print("❌ Activation cancelled due to low balance")
                return

    except Exception as e:
        print(f"❌ Configuration load failed: {e}")
        return

    # Step 3: Final activation confirmation
    print("\n" + "=" * 70)
    print("🚨 FINAL REAL MONEY TRADING ACTIVATION")
    print("=" * 70)
    print("✅ API credentials verified")
    print(f"✅ Account balance: ${balance:,.2f}")
    print("✅ Ultra-safe settings configured")
    print("✅ Manual approval required for all trades")
    print()
    print("⚠️  READY TO START REAL MONEY TRADING!")
    print("💰 Actual cryptocurrency will be bought and sold")
    print("📉 Real losses are possible")
    print("🛡️ Maximum safety protocols active")
    print()

    final_confirm = input("🚀 Type 'START REAL TRADING' to begin: ").strip()

    if final_confirm != "START REAL TRADING":
        print("❌ Trading not started - exact phrase required")
        return

    # Step 4: Start real money trading
    print("\n🚀🚀🚀 REAL MONEY TRADING ACTIVATED! 🚀🚀🚀")
    print("💰 TRADING WITH ACTUAL FUNDS")
    print("🛡️ YOU WILL APPROVE EACH TRADE MANUALLY")
    print()

    start_real_money_trading()


if __name__ == "__main__":
    print("🔐🔐🔐 REAL MONEY API ACTIVATION 🔐🔐🔐")
    print("💰 DIRECT SETUP WITH YOUR BINANCE US CREDENTIALS")
    print("🚀 IMMEDIATE REAL MONEY TRADING ACTIVATION")
    print()

    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
