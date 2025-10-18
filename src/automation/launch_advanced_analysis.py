#!/usr/bin/env python3
"""
Advanced Trading Analysis Launcher
Launch and manage all advanced analysis systems
"""

import os
import sys
import subprocess
import time
from datetime import datetime


def print_banner():
    print("⚛️" + "=" * 78 + "⚛️")
    print("🚀 ADVANCED TRADING ANALYSIS SYSTEM LAUNCHER 🚀")
    print("   Quantum-Level Market Intelligence & Statistical Arbitrage")
    print("⚛️" + "=" * 78 + "⚛️")


def check_dependencies():
    """Check if required packages are installed"""

    print("\n🔍 Checking dependencies...")

    required_packages = [
        "pandas",
        "numpy",
        "scipy",
        "scikit-learn",
        "statsmodels",
        "python-binance",
        "python-dotenv",
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("🔧 Run: pip install " + " ".join(missing_packages))
        return False

    print("✅ All dependencies satisfied!")
    return True


def run_quantum_analysis():
    """Run quantum data analysis"""

    print("\n⚛️  Starting Quantum Data Analysis...")
    try:
        result = subprocess.run(
            [sys.executable, "quantum_data_analyst.py"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print("✅ Quantum analysis completed successfully!")
            return True
        else:
            print(f"❌ Quantum analysis failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Quantum analysis timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running quantum analysis: {e}")
        return False


def run_statistical_arbitrage():
    """Run statistical arbitrage analysis"""

    print("\n📊 Starting Statistical Arbitrage Analysis...")
    try:
        result = subprocess.run(
            [sys.executable, "statistical_arbitrage_system.py"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print("✅ Statistical arbitrage analysis completed successfully!")
            return True
        else:
            print(f"❌ Statistical arbitrage analysis failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Statistical arbitrage analysis timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running statistical arbitrage analysis: {e}")
        return False


def run_microstructure_analysis():
    """Run market microstructure analysis"""

    print("\n🔬 Starting Market Microstructure Analysis...")
    try:
        result = subprocess.run(
            [sys.executable, "market_microstructure_analyzer.py"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print("✅ Microstructure analysis completed successfully!")
            return True
        else:
            print(f"❌ Microstructure analysis failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Microstructure analysis timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running microstructure analysis: {e}")
        return False


def run_master_analysis():
    """Run complete master analysis"""

    print("\n🧠 Starting Master Advanced Analysis...")
    try:
        result = subprocess.run(
            [sys.executable, "master_advanced_analysis.py"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            print("✅ Master analysis completed successfully!")
            print(result.stdout)
            return True
        else:
            print(f"❌ Master analysis failed: {result.stderr}")
            # Try to print partial output
            if result.stdout:
                print("Partial output:")
                print(result.stdout)
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Master analysis timed out (10 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running master analysis: {e}")
        return False


def run_simplified_analysis():
    """Run simplified analysis for quick results"""

    print("\n🎯 Starting Simplified Advanced Analysis...")
    try:
        result = subprocess.run(
            [sys.executable, "advanced_data_analyst_simplified.py"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print("✅ Simplified analysis completed successfully!")
            return True
        else:
            print(f"❌ Simplified analysis failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Simplified analysis timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error running simplified analysis: {e}")
        return False


def show_menu():
    """Show the main menu"""

    print("\n📋 ANALYSIS OPTIONS:")
    print("  1. 🎯 Quick Analysis (Simplified)")
    print("  2. ⚛️  Quantum Data Analysis")
    print("  3. 📊 Statistical Arbitrage Analysis")
    print("  4. 🔬 Market Microstructure Analysis")
    print("  5. 🧠 Master Analysis (All modules)")
    print("  6. 🔧 Check Dependencies")
    print("  7. 📁 Show Recent Results")
    print("  0. 🚪 Exit")
    print()


def show_recent_results():
    """Show recent analysis results"""

    print("\n📁 Recent Analysis Results:")

    # Look for recent result files
    result_patterns = [
        "quantum_data_analysis_*.json",
        "statistical_arbitrage_analysis_*.json",
        "market_microstructure_analysis_*.json",
        "master_advanced_analysis_*.json",
        "comprehensive_data_analysis_*.json",
    ]

    import glob

    all_files = []
    for pattern in result_patterns:
        files = glob.glob(pattern)
        all_files.extend([(f, os.path.getmtime(f)) for f in files])

    # Sort by modification time
    all_files.sort(key=lambda x: x[1], reverse=True)

    if not all_files:
        print("  📭 No recent analysis results found")
        return

    print("  📊 Recent files (most recent first):")
    for i, (filename, mtime) in enumerate(all_files[:10], 1):
        mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        file_size = os.path.getsize(filename) / 1024  # KB
        print(f"    {i:2d}. {filename:<40} ({mod_time}, {file_size:.1f}KB)")


def main():
    """Main launcher function"""

    print_banner()

    # Check if we're in the right directory
    if not os.path.exists("quantum_data_analyst.py"):
        print("❌ Please run this script from the victorychain_stack directory")
        print("   cd /Users/nicholaskramer/Downloads/victorychain_stack")
        return

    # Check dependencies
    if not check_dependencies():
        print("\n🔧 Please install missing dependencies first:")
        print(
            "   pip install pandas numpy scipy scikit-learn statsmodels python-binance python-dotenv"
        )
        print("   Or run: ./install_advanced_deps.sh")
        return

    while True:
        show_menu()

        try:
            choice = input("🎯 Select option (0-7): ").strip()

            if choice == "0":
                print("\n👋 Goodbye! Happy trading!")
                break
            elif choice == "1":
                run_simplified_analysis()
            elif choice == "2":
                run_quantum_analysis()
            elif choice == "3":
                run_statistical_arbitrage()
            elif choice == "4":
                run_microstructure_analysis()
            elif choice == "5":
                run_master_analysis()
            elif choice == "6":
                check_dependencies()
            elif choice == "7":
                show_recent_results()
            else:
                print("❌ Invalid choice. Please select 0-7.")

            if choice in ["1", "2", "3", "4", "5"]:
                input("\n⏸️  Press Enter to continue...")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("⏸️  Press Enter to continue...")


if __name__ == "__main__":
    main()
