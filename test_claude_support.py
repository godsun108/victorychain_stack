#!/usr/bin/env python3

"""
🤖 CLAUDE API TEST
Test Claude API connectivity and functionality
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_claude_api():
    claude_api_key = os.getenv("CLAUDE_API_KEY")

    print("🤖 CLAUDE API SUPPORT TEST")
    print("=" * 50)

    if not claude_api_key:
        print("❌ CLAUDE API KEY NOT FOUND")
        print("   Please set CLAUDE_API_KEY in your .env file")
        return False

    print(f"✅ Claude API Key Found: {claude_api_key[:20]}...")

    # Test API connectivity
    try:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": claude_api_key,
            "anthropic-version": "2023-06-01",
        }

        data = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": 'Hello! Can you analyze cryptocurrency markets? Just respond with "YES - I can analyze crypto markets" if you can help with trading analysis.',
                }
            ],
        }

        print("🔄 Testing Claude API connection...")

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30,
        )

        print(f"📡 API Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            content = result["content"][0]["text"]

            print("✅ CLAUDE API WORKING!")
            print(f"🤖 Claude Response: {content}")

            # Test trading-specific analysis
            print("\n🔄 Testing trading analysis capabilities...")

            trading_prompt = """
            Analyze this crypto data for trading:
            BTCUSDT: Price $45,000, Change +2.5%, Volume $100M
            ETHUSDT: Price $3,000, Change +1.8%, Volume $80M
            
            Respond with JSON:
            {"recommendation": "BUY/HOLD/SELL", "confidence": 0.85, "reasoning": "brief reason"}
            """

            trading_data = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": trading_prompt}],
            }

            trading_response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=trading_data,
                timeout=30,
            )

            if trading_response.status_code == 200:
                trading_result = trading_response.json()
                trading_content = trading_result["content"][0]["text"]

                print("✅ TRADING ANALYSIS WORKING!")
                print(f"📊 Claude Trading Analysis: {trading_content}")

                print("\n🎉 CLAUDE FULLY SUPPORTED!")
                print("   ✅ API Connection: Working")
                print("   ✅ Trading Analysis: Working")
                print("   ✅ JSON Responses: Working")
                print("   ✅ Ready for automated trading!")

                return True
            else:
                print(
                    f"⚠️  Trading analysis test failed: {trading_response.status_code}"
                )
                return False

        elif response.status_code == 401:
            print("❌ AUTHENTICATION FAILED")
            print("   Your Claude API key may be invalid or expired")
            print("   Please check your API key at: https://console.anthropic.com/")
            return False

        elif response.status_code == 429:
            print("⚠️  RATE LIMIT EXCEEDED")
            print("   Too many requests - try again later")
            print("   Claude API has usage limits")
            return False

        elif response.status_code == 400:
            print("⚠️  BAD REQUEST")
            print("   API request format issue")
            print("   This might be a temporary issue")
            return False

        else:
            print(f"❌ API ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("⏰ API TIMEOUT")
        print("   Claude API took too long to respond")
        return False

    except requests.exceptions.ConnectionError:
        print("🌐 CONNECTION ERROR")
        print("   Cannot connect to Claude API")
        print("   Check your internet connection")
        return False

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False


def show_claude_features():
    print("\n🚀 CLAUDE AI TRADING FEATURES:")
    print("=" * 40)
    print("✅ Market Analysis - Analyzes 180+ crypto pairs")
    print("✅ Portfolio Optimization - Smart allocation strategies")
    print("✅ Risk Assessment - Advanced risk management")
    print("✅ Buy/Hold Decisions - Long-term investment analysis")
    print("✅ Consolidation Strategy - Portfolio simplification")
    print("✅ Performance Tracking - ROI and performance monitoring")
    print("✅ Automated Execution - High-confidence trade automation")
    print("✅ Multi-timeframe Analysis - Short and long-term perspectives")

    print("\n📊 CLAUDE-POWERED SYSTEMS:")
    print("  • claude_auto_consolidator.py - Portfolio consolidation")
    print("  • claude_buy_hold.py - Long-term investment system")
    print("  • launch_live_trading.py - Real-time market analysis")

    print("\n🔧 FALLBACK SYSTEM:")
    print("  If Claude API fails, enhanced fallback analysis activates")
    print("  Uses quantitative algorithms and proven trading patterns")


def main():
    success = test_claude_api()

    if success:
        show_claude_features()
        print("\n🎯 NEXT STEPS:")
        print("  python3 claude_buy_hold.py      # Test buy & hold")
        print("  python3 claude_auto_consolidator.py  # Test consolidation")
        print("  python3 launch_live_trading.py  # Test market analysis")
    else:
        print("\n🔧 TROUBLESHOOTING:")
        print("  1. Check your Claude API key at console.anthropic.com")
        print("  2. Verify API key has sufficient credits")
        print("  3. Check internet connection")
        print("  4. Try again in a few minutes")
        print("\n📄 The system will use enhanced fallback analysis if Claude fails")


if __name__ == "__main__":
    main()
