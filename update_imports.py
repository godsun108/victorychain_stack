#!/usr/bin/env python3
"""
🔧 VICTORYCHAIN IMPORT PATH UPDATER
Updates all import paths to match the new directory structure
Author: Senior Developer
Version: 2.0.0
"""

import os
import re
from pathlib import Path


def update_imports_in_file(file_path: Path, replacements: dict):
    """Update import statements in a Python file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Apply replacements
        for old_import, new_import in replacements.items():
            # Match both 'from module import' and 'import module' patterns
            patterns = [
                rf"from {re.escape(old_import)} import",
                rf"import {re.escape(old_import)}(?!\w)",  # Negative lookahead to avoid partial matches
            ]

            for pattern in patterns:
                if "from" in pattern:
                    replacement = f"from {new_import} import"
                else:
                    replacement = f"import {new_import}"
                content = re.sub(pattern, replacement, content)

        # Only write if content changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Updated imports in {file_path}")
            return True

        return False

    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False


def main():
    """Update all import paths in the project"""

    # Define import replacements
    replacements = {
        "victorychain_shared": "core.victorychain_shared",
        "victorychain_integration": "core.victorychain_integration",
        "victorychain_core_v2": "core.victorychain_core_v2",
        "victorychain_module_loader": "core.victorychain_module_loader",
        "momentum_trader_v2": "strategies.momentum_trader_v2",
        "launch_live_trading_v2": "strategies.launch_live_trading_v2",
        "claude_auto_consolidator": "ai.claude_auto_consolidator",
        "claude_buy_hold": "ai.claude_buy_hold",
        "claude_diagnostic": "ai.claude_diagnostic",
        "claude_strategy_explained": "ai.claude_strategy_explained",
        "claude_token_optimizer": "ai.claude_token_optimizer",
        "claude_token_predictor": "ai.claude_token_predictor",
        "portfolio_consolidator": "portfolio.portfolio_consolidator",
        "portfolio_performance_tracker": "portfolio.portfolio_performance_tracker",
        "quick_consolidator": "portfolio.quick_consolidator",
        "robust_consolidator": "portfolio.robust_consolidator",
        "view_portfolio": "portfolio.view_portfolio",
        "auto_consolidation_scheduler": "automation.auto_consolidation_scheduler",
        "buy_hold_scheduler": "automation.buy_hold_scheduler",
        "launch_advanced_analysis": "automation.launch_advanced_analysis",
        "launch_buy_hold": "automation.launch_buy_hold",
        "launch_consolidation": "automation.launch_consolidation",
        "launch_master": "automation.launch_master",
        "all_tokens_list": "utilities.all_tokens_list",
        "all_tokens_report": "utilities.all_tokens_report",
        "check_all_tokens": "utilities.check_all_tokens",
        "check_holdings": "utilities.check_holdings",
        "check_portfolio": "utilities.check_portfolio",
        "holding_status": "utilities.holding_status",
        "quick_status": "utilities.quick_status",
        "trading_dashboard": "utilities.trading_dashboard",
        "victorychain_control": "utilities.victorychain_control",
        "web_dashboard": "web.web_dashboard",
    }

    project_root = Path(__file__).parent
    src_dir = project_root / "src"

    print("🔧 Updating import paths in VictoryChain project...")
    print("=" * 50)

    files_updated = 0
    total_files = 0

    # Process all Python files in src directory
    for py_file in src_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        total_files += 1
        if update_imports_in_file(py_file, replacements):
            files_updated += 1

    # Also update test files
    tests_dir = project_root / "tests"
    if tests_dir.exists():
        for py_file in tests_dir.rglob("*.py"):
            total_files += 1
            if update_imports_in_file(py_file, replacements):
                files_updated += 1

    # Update scripts
    scripts_dir = project_root / "scripts"
    if scripts_dir.exists():
        for py_file in scripts_dir.rglob("*.py"):
            total_files += 1
            if update_imports_in_file(py_file, replacements):
                files_updated += 1

    print("=" * 50)
    print(f"📊 Summary: Updated {files_updated}/{total_files} files")
    print("✅ Import path update completed!")


if __name__ == "__main__":
    main()
