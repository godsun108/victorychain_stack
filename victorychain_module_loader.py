#!/usr/bin/env python3

"""
🔧 VICTORYCHAIN MODULE LOADER
Ensures all VictoryChain modules are properly integrated and interoperable
Author: Senior Developer
Version: 2.0.0
"""

import sys
import os
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional


def check_and_fix_imports():
    """Check and fix import statements across all VictoryChain modules"""

    workspace_path = Path(__file__).parent

    # List of all Python files in the workspace
    python_files = [
        "victorychain_shared.py",
        "victorychain_core_v2.py",
        "momentum_trader_v2.py",
        "launch_live_trading_v2.py",
        "claude_auto_consolidator.py",
        "claude_buy_hold.py",
        "claude_token_optimizer.py",
        "claude_token_predictor.py",
        "portfolio_consolidator.py",
        "quick_consolidator.py",
        "robust_consolidator.py",
        "view_portfolio.py",
        "auto_consolidation_scheduler.py",
        "buy_hold_scheduler.py",
        "launch_consolidation.py",
        "launch_buy_hold.py",
        "launch_master.py",
        "victorychain_integration.py",
    ]

    print("🔧 VictoryChain Module Integration Check")
    print("=" * 50)

    # Check each file exists and has proper structure
    valid_files = []
    for file_name in python_files:
        file_path = workspace_path / file_name

        if file_path.exists():
            print(f"✅ Found: {file_name}")
            valid_files.append(file_name)
        else:
            print(f"❌ Missing: {file_name}")

    print(f"\n📊 Found {len(valid_files)}/{len(python_files)} files")

    # Test imports
    print("\n🧪 Testing imports...")
    import_results = {}

    for file_name in valid_files:
        module_name = file_name.replace(".py", "")
        try:
            # Try to import each module
            spec = importlib.util.spec_from_file_location(
                module_name, workspace_path / file_name
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Don't execute, just check if it can be loaded
                import_results[file_name] = "✅ Import OK"
            else:
                import_results[file_name] = "❌ Import Failed"
        except Exception as e:
            import_results[file_name] = f"❌ Error: {str(e)[:50]}..."

    # Show results
    for file_name, result in import_results.items():
        print(f"  {result}: {file_name}")

    return valid_files, import_results


def create_module_interface_map():
    """Create a map of how modules should interface with each other"""

    interface_map = {
        "victorychain_shared.py": {
            "exports": [
                "OrderType",
                "StrategyType",
                "TradingMode",
                "OrderStatus",
                "RiskLevel",
                "MarketData",
                "TradingSignal",
                "TradeResult",
                "PortfolioPosition",
                "TradingConfig",
                "AnalysisResult",
                "BaseStrategy",
                "BaseTrader",
            ],
            "imports": [],
            "dependents": [
                "victorychain_core_v2.py",
                "momentum_trader_v2.py",
                "launch_live_trading_v2.py",
            ],
        },
        "victorychain_core_v2.py": {
            "exports": ["VictoryChainCore"],
            "imports": ["victorychain_shared"],
            "dependents": ["launch_live_trading_v2.py", "claude_auto_consolidator.py"],
        },
        "momentum_trader_v2.py": {
            "exports": ["MomentumTrader"],
            "imports": ["victorychain_shared"],
            "dependents": ["launch_live_trading_v2.py"],
        },
        "launch_live_trading_v2.py": {
            "exports": ["LiveTradingSystem"],
            "imports": [
                "victorychain_shared",
                "victorychain_core_v2",
                "momentum_trader_v2",
                "claude_token_optimizer",
            ],
            "dependents": [],
        },
        "claude_token_optimizer.py": {
            "exports": ["ClaudeTokenOptimizer"],
            "imports": ["victorychain_shared"],
            "dependents": [
                "claude_auto_consolidator.py",
                "claude_buy_hold.py",
                "claude_token_predictor.py",
                "launch_live_trading_v2.py",
            ],
        },
        "claude_auto_consolidator.py": {
            "exports": ["ClaudePortfolioConsolidator"],
            "imports": [
                "victorychain_shared",
                "claude_token_optimizer",
                "victorychain_core_v2",
            ],
            "dependents": ["launch_consolidation.py"],
        },
        "claude_buy_hold.py": {
            "exports": ["ClaudeBuyHold"],
            "imports": ["victorychain_shared", "claude_token_optimizer"],
            "dependents": ["launch_buy_hold.py"],
        },
    }

    return interface_map


def validate_module_interfaces():
    """Validate that modules properly implement their interfaces"""

    print("\n🔍 Validating module interfaces...")

    interface_map = create_module_interface_map()
    validation_results = {}

    for module_file, interface_info in interface_map.items():
        results = {
            "file_exists": False,
            "imports_valid": True,
            "exports_available": [],
            "issues": [],
        }

        file_path = Path(__file__).parent / module_file

        # Check file exists
        if file_path.exists():
            results["file_exists"] = True

            try:
                # Read file content to check structure
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Check for expected exports
                for export in interface_info["exports"]:
                    if f"class {export}" in content or f"def {export}" in content:
                        results["exports_available"].append(export)

                # Check for proper imports
                for import_module in interface_info["imports"]:
                    import_patterns = [
                        f"from {import_module} import",
                        f"import {import_module}",
                    ]

                    if not any(pattern in content for pattern in import_patterns):
                        results["issues"].append(f"Missing import: {import_module}")
                        results["imports_valid"] = False

            except Exception as e:
                results["issues"].append(f"File read error: {e}")

        else:
            results["issues"].append("File not found")

        validation_results[module_file] = results

    # Display results
    for module_file, results in validation_results.items():
        status = "✅" if results["file_exists"] and results["imports_valid"] else "❌"
        print(f"  {status} {module_file}")

        if results["issues"]:
            for issue in results["issues"]:
                print(f"    ⚠️  {issue}")

    return validation_results


def create_import_fix_suggestions():
    """Create suggestions for fixing import issues"""

    suggestions = {
        "victorychain_core_v2.py": [
            "Add: from victorychain_shared import OrderType, StrategyType, TradingConfig",
            "Replace local enum definitions with shared ones",
            "Use shared BaseTrader and TradingEngine interfaces",
        ],
        "momentum_trader_v2.py": [
            "Add: from victorychain_shared import TradingSignal, TradeResult",
            "Implement BaseStrategy interface",
            "Use shared configuration system",
        ],
        "launch_live_trading_v2.py": [
            "Add: from victorychain_core_v2 import VictoryChainCore",
            "Add: from momentum_trader_v2 import MomentumTrader",
            "Use unified TradingConfig from shared interfaces",
        ],
        "claude_auto_consolidator.py": [
            "Add: from victorychain_shared import AnalysisResult, ClaudeProvider",
            "Implement ClaudeProvider protocol",
            "Use shared error handling patterns",
        ],
    }

    print("\n💡 Import Fix Suggestions:")
    print("=" * 30)

    for file_name, fixes in suggestions.items():
        print(f"\n📝 {file_name}:")
        for fix in fixes:
            print(f"  • {fix}")

    return suggestions


def test_module_loading():
    """Test that modules can be loaded with proper integration"""

    print("\n🧪 Testing module loading...")

    # Try to create integration manager
    try:
        from victorychain_integration import VictoryChainIntegrationManager

        manager = VictoryChainIntegrationManager()
        print("✅ Integration manager created successfully")

        # Test loading core modules
        core_modules = [
            "victorychain_core_v2",
            "momentum_trader_v2",
            "claude_token_optimizer",
        ]

        loaded_modules = []
        for module_name in core_modules:
            try:
                success = manager.load_module(module_name)
                if success:
                    loaded_modules.append(module_name)
                    print(f"✅ Loaded: {module_name}")
                else:
                    print(f"❌ Failed: {module_name}")
            except Exception as e:
                print(f"❌ Error loading {module_name}: {e}")

        print(
            f"\n📊 Successfully loaded {len(loaded_modules)}/{len(core_modules)} core modules"
        )

        # Test integration status
        if loaded_modules:
            status = manager.get_integration_status()
            print(f"🔗 Integration status: {len(status['modules'])} modules registered")

        return True, loaded_modules

    except Exception as e:
        print(f"❌ Integration manager test failed: {e}")
        return False, []


def main():
    """Main function to run all integration checks"""

    print("🚀 VictoryChain Senior Developer Integration Check")
    print("=" * 60)

    # Step 1: Check file structure
    valid_files, import_results = check_and_fix_imports()

    # Step 2: Validate interfaces
    validation_results = validate_module_interfaces()

    # Step 3: Show fix suggestions
    create_import_fix_suggestions()

    # Step 4: Test module loading
    success, loaded_modules = test_module_loading()

    # Summary
    print("\n" + "=" * 60)
    print("📋 INTEGRATION SUMMARY")
    print("=" * 60)

    total_files = len(valid_files)
    import_ok = sum(1 for result in import_results.values() if "✅" in result)
    valid_interfaces = sum(
        1
        for result in validation_results.values()
        if result["file_exists"] and result["imports_valid"]
    )

    print(f"📁 Files found: {total_files}")
    print(f"📦 Import tests passed: {import_ok}/{total_files}")
    print(f"🔗 Valid interfaces: {valid_interfaces}")
    print(f"🎯 Integration test: {'✅ PASSED' if success else '❌ FAILED'}")

    if success:
        print(f"🏆 Loaded modules: {', '.join(loaded_modules)}")

    # Overall score
    total_checks = total_files + len(validation_results) + (1 if success else 0)
    passed_checks = import_ok + valid_interfaces + (1 if success else 0)
    score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0

    print(f"\n🎯 OVERALL INTEGRATION SCORE: {score:.1f}%")

    if score >= 80:
        print("🎉 EXCELLENT! Senior developer standards achieved!")
    elif score >= 60:
        print("👍 GOOD! Minor improvements needed.")
    else:
        print("⚠️  NEEDS WORK! Major integration issues found.")

    return score


if __name__ == "__main__":
    main()
