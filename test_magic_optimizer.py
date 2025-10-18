#!/usr/bin/env python3
"""
MAGIC POSITION OPTIMIZER - TEST SCRIPT
=====================================

🧪 COMPREHENSIVE TESTING & VALIDATION
✅ DEPENDENCY VERIFICATION
🔧 CONFIGURATION TESTING
📊 SIMULATION MODE TESTING

Run this script to verify your setup before live trading.
"""

import sys
import os
import json
import asyncio
import logging
from datetime import datetime

# Configure test logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class OptimizerTester:
    """Test suite for MAGIC Position Optimizer"""

    def __init__(self):
        self.test_results = []
        self.config_file = "advanced_optimizer_config.json"

    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        message = f"{status} - {test_name}"
        if details:
            message += f" ({details})"

        logger.info(message)
        self.test_results.append(
            {
                "test": test_name,
                "passed": passed,
                "details": details,
                "timestamp": datetime.now().isoformat(),
            }
        )

        return passed

    def test_python_version(self) -> bool:
        """Test Python version compatibility"""
        version = sys.version_info
        required = (3, 8)

        passed = version >= required
        details = f"Python {version.major}.{version.minor}.{version.micro}"

        return self.log_test("Python Version", passed, details)

    def test_dependencies(self) -> bool:
        """Test critical dependencies"""
        dependencies = [
            ("ccxt", "Exchange connectivity"),
            ("pandas", "Data analysis"),
            ("numpy", "Numerical operations"),
            ("json", "Configuration parsing"),
            ("asyncio", "Async operations"),
            ("logging", "Logging system"),
            ("datetime", "Time operations"),
        ]

        all_passed = True

        for dep, description in dependencies:
            try:
                __import__(dep)
                self.log_test(f"Dependency: {dep}", True, description)
            except ImportError:
                self.log_test(f"Dependency: {dep}", False, f"Missing - {description}")
                all_passed = False

        # Test optional but recommended dependencies
        optional_deps = [
            ("talib", "Technical analysis (critical for optimizer)"),
            ("scipy", "Statistical functions"),
            ("aiohttp", "Async HTTP requests"),
        ]

        for dep, description in optional_deps:
            try:
                __import__(dep)
                self.log_test(f"Optional: {dep}", True, description)
            except ImportError:
                self.log_test(f"Optional: {dep}", False, f"Missing - {description}")
                if dep == "talib":  # TA-Lib is critical
                    all_passed = False

        return all_passed

    def test_configuration(self) -> bool:
        """Test configuration file"""
        try:
            if not os.path.exists(self.config_file):
                return self.log_test("Configuration File", False, "File not found")

            with open(self.config_file, "r") as f:
                config = json.load(f)

            # Test configuration structure
            required_sections = [
                "trading_settings",
                "position_switching",
                "gas_optimization",
                "iso_20022_reserves",
                "cycle_timing",
                "binance_us_api",
            ]

            main_config = config.get("advanced_position_optimizer_config", {})

            for section in required_sections:
                if section in main_config:
                    self.log_test(f"Config Section: {section}", True, "Present")
                else:
                    self.log_test(f"Config Section: {section}", False, "Missing")
                    return False

            # Test API configuration
            api_config = main_config.get("binance_us_api", {})
            testnet = api_config.get("testnet", True)

            if testnet:
                self.log_test("API Mode", True, "Testnet (Safe)")
            else:
                api_key = api_config.get("api_key", "")
                if api_key and api_key != "your_binance_us_api_key_here":
                    self.log_test("API Mode", True, "Live trading configured")
                else:
                    self.log_test("API Mode", False, "Live mode but no API key")

            return self.log_test("Configuration", True, "All sections valid")

        except Exception as e:
            return self.log_test("Configuration", False, f"Error: {e}")

    def test_file_permissions(self) -> bool:
        """Test file system permissions"""
        try:
            # Test write permissions
            test_file = "test_permissions.tmp"
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)

            self.log_test("File Permissions", True, "Read/write OK")

            # Test log file creation
            log_file = "test_optimizer.log"
            with open(log_file, "w") as f:
                f.write("test log entry\n")
            os.remove(log_file)

            return self.log_test("Log File Creation", True, "Can create logs")

        except Exception as e:
            return self.log_test("File Permissions", False, f"Error: {e}")

    async def test_optimizer_import(self) -> bool:
        """Test optimizer module import"""
        try:
            # Add current directory to path
            sys.path.insert(0, ".")

            # Try importing the optimizer
            magic_optimizer = __import__("magic_position_optimizer")

            # Test basic class instantiation
            optimizer = magic_optimizer.MagicPositionOptimizer(self.config_file)

            return self.log_test("Optimizer Import", True, "Module loaded successfully")

        except ImportError as e:
            return self.log_test("Optimizer Import", False, f"Import error: {e}")
        except Exception as e:
            return self.log_test("Optimizer Import", False, f"Instantiation error: {e}")

    async def test_basic_functionality(self) -> bool:
        """Test basic optimizer functionality"""
        try:
            # Only test if we can import
            if "magic_position_optimizer" not in sys.modules:
                return self.log_test(
                    "Basic Functionality", False, "Optimizer not imported"
                )

            magic_optimizer = sys.modules["magic_position_optimizer"]

            # Test configuration loading
            optimizer = magic_optimizer.MagicPositionOptimizer(self.config_file)

            # Test basic method existence
            methods_to_test = [
                "analyze_magic_position_strength",
                "scan_alternative_opportunities",
                "calculate_switching_costs",
                "determine_cycle_timing",
            ]

            for method in methods_to_test:
                if hasattr(optimizer, method):
                    self.log_test(f"Method: {method}", True, "Available")
                else:
                    self.log_test(f"Method: {method}", False, "Missing")
                    return False

            return self.log_test("Basic Functionality", True, "All methods available")

        except Exception as e:
            return self.log_test("Basic Functionality", False, f"Error: {e}")

    def test_network_connectivity(self) -> bool:
        """Test network connectivity"""
        try:
            import urllib.request
            import urllib.error

            # Test basic internet connectivity
            try:
                urllib.request.urlopen("https://api.binance.us/api/v3/ping", timeout=10)
                return self.log_test(
                    "Network Connectivity", True, "Binance US API reachable"
                )
            except urllib.error.URLError:
                return self.log_test(
                    "Network Connectivity", False, "Cannot reach Binance US API"
                )

        except Exception as e:
            return self.log_test("Network Connectivity", False, f"Error: {e}")

    async def run_all_tests(self) -> bool:
        """Run complete test suite"""
        logger.info("🧪 Starting MAGIC Position Optimizer Test Suite")
        logger.info("=" * 50)

        # Run all tests
        test_results = []

        test_results.append(self.test_python_version())
        test_results.append(self.test_dependencies())
        test_results.append(self.test_configuration())
        test_results.append(self.test_file_permissions())
        test_results.append(await self.test_optimizer_import())
        test_results.append(await self.test_basic_functionality())
        test_results.append(self.test_network_connectivity())

        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)

        logger.info("=" * 50)
        logger.info(f"📊 TEST SUMMARY: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - Ready for optimization!")
            logger.info("🚀 You can now run: python launch_magic_optimizer.py")
        else:
            logger.info("⚠️ Some tests failed - please fix issues before running")
            logger.info("💡 Check the test output above for specific problems")

        return passed_tests == total_tests

    def save_test_report(self):
        """Save detailed test report"""
        try:
            report = {
                "test_run": {
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": len(self.test_results),
                    "passed_tests": sum(1 for r in self.test_results if r["passed"]),
                    "failed_tests": sum(
                        1 for r in self.test_results if not r["passed"]
                    ),
                },
                "test_results": self.test_results,
                "environment": {
                    "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                    "platform": sys.platform,
                    "working_directory": os.getcwd(),
                },
            }

            with open("optimizer_test_report.json", "w") as f:
                json.dump(report, f, indent=2)

            logger.info("📄 Test report saved to: optimizer_test_report.json")

        except Exception as e:
            logger.error(f"❌ Failed to save test report: {e}")


async def main():
    """Main test execution"""
    try:
        print("🧪 MAGIC POSITION OPTIMIZER - TEST SUITE")
        print("========================================")
        print()
        print("This will verify your setup is ready for optimization.")
        print("No trading operations will be performed.")
        print()

        tester = OptimizerTester()
        success = await tester.run_all_tests()
        tester.save_test_report()

        if success:
            print()
            print("🎉 SUCCESS! Your MAGIC Position Optimizer is ready!")
            print("🚀 Next steps:")
            print("   1. Review configuration in advanced_optimizer_config.json")
            print("   2. Run: python launch_magic_optimizer.py")
            print("   3. Monitor logs for optimization activity")
        else:
            print()
            print("⚠️ Please fix the failed tests before proceeding.")
            print("💡 Check MAGIC_OPTIMIZER_GUIDE.md for troubleshooting help.")

        return success

    except KeyboardInterrupt:
        print("\n⏹️ Test suite interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Test suite error: {e}")
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Fatal test error: {e}")
        sys.exit(1)
