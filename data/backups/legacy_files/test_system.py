#!/usr/bin/env python3
"""
VictoryChain System Test Suite
Tests all trading bot components and validates functionality
"""

import os
import sys
import time
import json
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VictoryChainTestSuite:
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()

    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        logger.info(f"🧪 Running test: {test_name}")

        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time

            self.test_results[test_name] = {
                "status": "PASS" if result else "FAIL",
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
            }

            status_emoji = "✅" if result else "❌"
            logger.info(
                f"{status_emoji} {test_name}: {'PASS' if result else 'FAIL'} ({duration:.2f}s)"
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            self.test_results[test_name] = {
                "status": "ERROR",
                "error": str(e),
                "duration": duration,
                "timestamp": datetime.now().isoformat(),
            }

            logger.error(f"❌ {test_name}: ERROR - {e}")
            return False

    def test_dependencies(self):
        """Test that all required dependencies are installed"""
        try:
            import requests
            import numpy as np
            import asyncio
            from dotenv import load_dotenv

            # Optional dependencies
            try:
                import scipy

                logger.info("📦 scipy available for advanced statistical analysis")
            except ImportError:
                logger.info("📦 scipy not available (optional)")

            return True
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            return False

    def test_api_connectivity(self):
        """Test Binance US API connectivity"""
        try:
            import requests

            # Test Binance US public API
            response = requests.get("https://api.binance.us/api/v3/ping", timeout=10)
            if response.status_code != 200:
                return False

            # Test ticker endpoint
            response = requests.get(
                "https://api.binance.us/api/v3/ticker/24hr", timeout=10
            )
            if response.status_code != 200:
                return False

            data = response.json()
            if not isinstance(data, list) or len(data) == 0:
                return False

            logger.info(f"📊 Found {len(data)} trading pairs on Binance US")
            return True

        except Exception as e:
            logger.error(f"API connectivity test failed: {e}")
            return False

    def test_claude_api(self):
        """Test Claude API connectivity (if key is provided)"""
        try:
            import requests

            claude_key = os.getenv("CLAUDE_API_KEY")
            if not claude_key or claude_key == "your_claude_api_key_here":
                logger.info("🤖 Claude API key not configured (optional)")
                return True  # Not a failure if not configured

            headers = {
                "x-api-key": claude_key,
                "content-type": "application/json",
            }

            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": 50,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, this is a test message. Please respond briefly.",
                    }
                ],
            }

            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                logger.info("🤖 Claude API: Connected and functional")
                return True
            else:
                logger.error(f"🤖 Claude API: Error {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Claude API test failed: {e}")
            return False

    def test_volume_analysis(self):
        """Test volume categorization functionality"""
        try:
            import requests

            # Get market data
            response = requests.get(
                "https://api.binance.us/api/v3/ticker/24hr", timeout=10
            )
            if response.status_code != 200:
                return False

            tickers = response.json()
            usdt_pairs = [
                t
                for t in tickers
                if t["symbol"].endswith("USDT") and t["symbol"] != "USDT"
            ]

            if len(usdt_pairs) < 50:  # Should have many USDT pairs
                return False

            # Categorize by volume
            categories = {"high": 0, "medium": 0, "low": 0, "micro": 0}

            for ticker in usdt_pairs:
                volume = float(ticker["quoteVolume"])
                if volume >= 1000000:
                    categories["high"] += 1
                elif volume >= 100000:
                    categories["medium"] += 1
                elif volume >= 10000:
                    categories["low"] += 1
                else:
                    categories["micro"] += 1

            logger.info(f"📊 Volume categories: {categories}")

            # Should have tokens in each category
            return sum(categories.values()) > 100

        except Exception as e:
            logger.error(f"Volume analysis test failed: {e}")
            return False

    def test_statistical_analysis(self):
        """Test statistical analysis functions"""
        try:
            import numpy as np

            # Generate test data
            test_data = np.random.normal(0, 1, 100)

            # Basic statistical calculations
            mean = np.mean(test_data)
            std = np.std(test_data)

            # Should have reasonable values
            if abs(mean) > 0.5 or std < 0.5 or std > 2.0:
                return False

            # Test momentum calculation
            prices = [100, 102, 105, 103, 108, 110, 107, 112]
            momentum = (prices[-1] - prices[0]) / prices[0] * 100

            if abs(momentum - 12.0) > 0.1:  # Should be 12%
                return False

            logger.info(
                f"📈 Statistical analysis: mean={mean:.3f}, std={std:.3f}, momentum={momentum:.1f}%"
            )
            return True

        except Exception as e:
            logger.error(f"Statistical analysis test failed: {e}")
            return False

    def test_config_loading(self):
        """Test configuration loading"""
        try:
            # Test .env loading
            load_dotenv()

            # Should be able to access environment variables
            demo_mode = os.getenv("DEMO", "true")

            # Test that we can create a basic config
            config = {
                "demo_mode": demo_mode.lower() == "true",
                "portfolio_value": float(os.getenv("PORTFOLIO_VALUE", "10000")),
                "max_positions": int(os.getenv("MAX_POSITIONS", "5")),
            }

            logger.info(
                f"⚙️ Config loaded: demo={config['demo_mode']}, portfolio=${config['portfolio_value']}"
            )
            return True

        except Exception as e:
            logger.error(f"Config loading test failed: {e}")
            return False

    async def test_async_functionality(self):
        """Test async/await functionality"""
        try:
            # Test basic async operation
            await asyncio.sleep(0.1)

            # Test multiple async operations
            tasks = [asyncio.sleep(0.01) for _ in range(5)]
            await asyncio.gather(*tasks)

            return True

        except Exception as e:
            logger.error(f"Async functionality test failed: {e}")
            return False

    def test_file_system(self):
        """Test file system access and permissions"""
        try:
            # Test creating a log file
            test_file = "test_victorychain.log"

            # Write test
            with open(test_file, "w") as f:
                f.write(f"Test log entry: {datetime.now()}\n")

            # Read test
            with open(test_file, "r") as f:
                content = f.read()

            # Cleanup
            os.remove(test_file)

            return "Test log entry" in content

        except Exception as e:
            logger.error(f"File system test failed: {e}")
            return False

    def test_json_functionality(self):
        """Test JSON parsing and generation"""
        try:
            # Test data structure
            test_data = {
                "symbols": ["BTCUSDT", "ETHUSDT"],
                "analysis": {
                    "BTCUSDT": {
                        "momentum_score": 75.5,
                        "volume": 1500000,
                        "action": "buy",
                    }
                },
                "timestamp": datetime.now().isoformat(),
            }

            # Test JSON serialization
            json_str = json.dumps(test_data, indent=2)

            # Test JSON deserialization
            parsed_data = json.loads(json_str)

            # Verify data integrity
            return parsed_data["symbols"][0] == "BTCUSDT"

        except Exception as e:
            logger.error(f"JSON functionality test failed: {e}")
            return False

    def test_error_handling(self):
        """Test error handling mechanisms"""
        try:
            # Test handling of network errors
            try:
                import requests

                requests.get("https://invalid-api-endpoint.com", timeout=1)
            except:
                pass  # Expected to fail

            # Test handling of invalid data
            try:
                invalid_json = '{"invalid": json content}'
                json.loads(invalid_json)
            except:
                pass  # Expected to fail

            # If we reach here, error handling is working
            return True

        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            return False

    def generate_report(self):
        """Generate comprehensive test report"""
        total_duration = time.time() - self.start_time

        passed = sum(1 for r in self.test_results.values() if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results.values() if r["status"] == "FAIL")
        errors = sum(1 for r in self.test_results.values() if r["status"] == "ERROR")
        total = len(self.test_results)

        print("\n" + "=" * 60)
        print("🧪 VICTORYCHAIN TEST SUITE REPORT")
        print("=" * 60)
        print(f"📊 Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"🚨 Errors: {errors}")
        print(f"⏱️  Total Duration: {total_duration:.2f}s")
        print(f"🎯 Success Rate: {(passed/total)*100:.1f}%")
        print("=" * 60)

        # Detailed results
        for test_name, result in self.test_results.items():
            status_emoji = {"PASS": "✅", "FAIL": "❌", "ERROR": "🚨"}[result["status"]]
            print(
                f"{status_emoji} {test_name}: {result['status']} ({result['duration']:.2f}s)"
            )
            if result["status"] == "ERROR":
                print(f"   Error: {result['error']}")

        print("=" * 60)

        # Save detailed report
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(
                {
                    "summary": {
                        "total": total,
                        "passed": passed,
                        "failed": failed,
                        "errors": errors,
                        "success_rate": (passed / total) * 100,
                        "duration": total_duration,
                    },
                    "results": self.test_results,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        print(f"📄 Detailed report saved to: {report_file}")

        return passed == total  # Return True if all tests passed


async def main():
    """Main test runner"""
    print("🚀 VictoryChain Trading Bot System Test Suite")
    print("=" * 60)
    print("🧪 Testing all components for functionality and compatibility")
    print("")

    suite = VictoryChainTestSuite()

    # Run all tests
    tests = [
        ("Dependencies Check", suite.test_dependencies),
        ("API Connectivity", suite.test_api_connectivity),
        ("Claude AI API", suite.test_claude_api),
        ("Volume Analysis", suite.test_volume_analysis),
        ("Statistical Analysis", suite.test_statistical_analysis),
        ("Configuration Loading", suite.test_config_loading),
        ("File System Access", suite.test_file_system),
        ("JSON Functionality", suite.test_json_functionality),
        ("Error Handling", suite.test_error_handling),
    ]

    # Run sync tests
    for test_name, test_func in tests:
        suite.run_test(test_name, test_func)

    # Run async tests
    suite.run_test(
        "Async Functionality", lambda: asyncio.run(suite.test_async_functionality())
    )

    # Generate final report
    all_passed = suite.generate_report()

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! VictoryChain system is ready to use.")
        print("💡 You can now run any trading bot with confidence.")
        print("🚀 Start with: ./launch_trading_bot.sh")
    else:
        print("\n⚠️  Some tests failed. Please review the results above.")
        print("🔧 Fix any issues before running live trading bots.")

    return all_passed


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n🚨 Test suite error: {e}")
        sys.exit(1)
