#!/usr/bin/env python3

"""
🎮 ENHANCED VICTORYCHAIN MAIN BOT
Intelligent trading bot with continuous learning and dynamic reallocation
Integrates all analysis systems for optimal momentum-based trading

Features:
- Continuous learning from all past allocations
- Dynamic reallocation without waiting for position maturity
- Advanced pattern recognition and AI-driven decisions
- Real-time opportunity detection and execution
- Adaptive risk management with evolving stop-loss
"""

import os
import sys
import time
import json
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(__file__))

# Import our advanced systems
try:
    from continuous_learning_reallocation_engine import (
        ContinuousLearningReallocationEngine,
    )
    from intelligent_learning_momentum_bot import IntelligentLearningMomentumBot
    from enhanced_magic_learning_system import EnhancedMagicLearningSystem
    from comprehensive_momentum_gain_analyzer import run_momentum_analysis
    from low_cost_token_predictor import run_low_cost_prediction
    from microcap_all_in_system import run_microcap_all_in_analysis
    from all_in_100_percent_system import run_all_in_100_percent_analysis
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("📝 Some analysis modules may not be available")


class EnhancedVictoryChainBot:
    """Enhanced main bot with continuous learning integration"""

    def __init__(self):
        print("🎮 ENHANCED VICTORYCHAIN BOT INITIALIZING...")
        print("=" * 60)

        # Initialize core systems
        self.continuous_engine = None
        self.momentum_bot = None
        self.magic_system = None

        # Bot configuration
        self.config = {
            "operation_mode": "continuous_learning",
            "enable_realtime_reallocation": True,
            "enable_momentum_analysis": True,
            "enable_pattern_learning": True,
            "enable_ai_predictions": True,
            "risk_management_level": "adaptive",
            "learning_aggressiveness": "high",
            "reallocation_frequency_minutes": 5,
            "analysis_frequency_minutes": 15,
            "reporting_frequency_minutes": 30,
        }

        # Performance tracking
        self.performance_metrics = {
            "total_sessions": 0,
            "successful_reallocations": 0,
            "total_profit_usd": 0.0,
            "best_gain_percentage": 0.0,
            "learning_accuracy": 0.0,
            "active_since": datetime.now(),
        }

        # Initialize all systems
        self.initialize_systems()

    def initialize_systems(self):
        """Initialize all trading and learning systems"""
        print("🔧 Initializing trading systems...")

        try:
            # Initialize continuous learning engine
            print("🧠 Starting Continuous Learning Reallocation Engine...")
            self.continuous_engine = ContinuousLearningReallocationEngine()
            print("✅ Continuous Learning Engine ready")

            # Initialize momentum bot
            print("📈 Starting Intelligent Learning Momentum Bot...")
            self.momentum_bot = IntelligentLearningMomentumBot()
            print("✅ Momentum Bot ready")

            # Initialize MAGIC learning system
            print("🎮 Starting Enhanced MAGIC Learning System...")
            self.magic_system = EnhancedMagicLearningSystem()
            print("✅ MAGIC Learning System ready")

        except Exception as e:
            print(f"⚠️ System initialization error: {e}")
            print("🔄 Continuing with available systems...")

    def run_comprehensive_analysis_suite(self):
        """Run comprehensive analysis of all available systems"""
        print("\n🔍 RUNNING COMPREHENSIVE ANALYSIS SUITE")
        print("=" * 60)

        analysis_results = {}

        # 1. Momentum Gain Analysis
        print("📈 Running momentum gain analysis...")
        try:
            momentum_result = run_momentum_analysis()
            analysis_results["momentum"] = momentum_result
            print("✅ Momentum analysis complete")
        except Exception as e:
            print(f"⚠️ Momentum analysis error: {e}")

        # 2. Low-Cost Token Prediction
        print("💰 Running low-cost token prediction...")
        try:
            lowcost_result = run_low_cost_prediction()
            analysis_results["low_cost"] = lowcost_result
            print("✅ Low-cost prediction complete")
        except Exception as e:
            print(f"⚠️ Low-cost prediction error: {e}")

        # 3. Microcap All-In Analysis
        print("🚀 Running microcap all-in analysis...")
        try:
            microcap_result = run_microcap_all_in_analysis()
            analysis_results["microcap"] = microcap_result
            print("✅ Microcap analysis complete")
        except Exception as e:
            print(f"⚠️ Microcap analysis error: {e}")

        # 4. 100% All-In Analysis
        print("💯 Running 100% all-in analysis...")
        try:
            allin_result = run_all_in_100_percent_analysis()
            analysis_results["all_in_100"] = allin_result
            print("✅ 100% all-in analysis complete")
        except Exception as e:
            print(f"⚠️ 100% all-in analysis error: {e}")

        return analysis_results

    def start_continuous_operation(self):
        """Start continuous operation with all systems"""
        print("\n🚀 STARTING CONTINUOUS OPERATION")
        print("=" * 60)
        print("🔄 Bot will continuously learn, analyze, and reallocate...")
        print("⏰ Real-time monitoring and decision-making active")
        print()

        # Start background threads for different operations
        threads = []

        # Continuous learning and reallocation thread
        if self.continuous_engine:
            learning_thread = threading.Thread(
                target=self.continuous_learning_loop, daemon=True
            )
            learning_thread.start()
            threads.append(learning_thread)

        # Analysis and reporting thread
        analysis_thread = threading.Thread(
            target=self.analysis_reporting_loop, daemon=True
        )
        analysis_thread.start()
        threads.append(analysis_thread)

        # Performance monitoring thread
        monitoring_thread = threading.Thread(
            target=self.performance_monitoring_loop, daemon=True
        )
        monitoring_thread.start()
        threads.append(monitoring_thread)

        # Main control loop
        try:
            self.main_control_loop()
        except KeyboardInterrupt:
            print("\n⏹️ Stopping VictoryChain Bot...")
            self.shutdown_gracefully()

    def continuous_learning_loop(self):
        """Continuous learning and reallocation loop"""
        while True:
            try:
                if self.continuous_engine:
                    # Run learning cycle
                    report = self.continuous_engine.generate_learning_report()

                    # Check for high-priority reallocations
                    reallocation_actions = (
                        self.continuous_engine.analyze_reallocation_opportunities()
                    )

                    for action in reallocation_actions:
                        if action.urgency_score > 0.8:
                            print(f"🔥 URGENT REALLOCATION: {action.reasoning}")
                            self.continuous_engine.execute_reallocation(action)
                            self.performance_metrics["successful_reallocations"] += 1

                # Wait before next cycle
                time.sleep(self.config["reallocation_frequency_minutes"] * 60)

            except Exception as e:
                print(f"⚠️ Continuous learning loop error: {e}")
                time.sleep(60)

    def analysis_reporting_loop(self):
        """Periodic analysis and reporting loop"""
        while True:
            try:
                # Run periodic comprehensive analysis
                print(f"\n📊 PERIODIC ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")

                # Quick opportunity scan
                if self.continuous_engine:
                    opportunities = self.continuous_engine.analyze_opportunities()
                    if opportunities:
                        top_opp = opportunities[0]
                        print(f"🎯 Top Opportunity: {top_opp.token}")
                        print(f"   Score: {top_opp.opportunity_score:.3f}")
                        print(f"   Predicted Gain: {top_opp.predicted_gain:.1%}")
                        print(f"   Confidence: {top_opp.confidence:.2f}")

                # Momentum analysis
                if self.momentum_bot:
                    momentum_signals = self.momentum_bot.generate_ai_trading_signals()
                    if momentum_signals:
                        print(f"📈 Momentum Signals: {len(momentum_signals)} detected")

                # MAGIC pattern analysis
                if self.magic_system:
                    magic_opportunities = (
                        self.magic_system.analyze_all_in_opportunities()
                    )
                    if magic_opportunities:
                        print(
                            f"🎮 MAGIC Opportunities: {len(magic_opportunities)} patterns found"
                        )

                # Wait before next analysis
                time.sleep(self.config["analysis_frequency_minutes"] * 60)

            except Exception as e:
                print(f"⚠️ Analysis reporting loop error: {e}")
                time.sleep(300)

    def performance_monitoring_loop(self):
        """Performance monitoring and metrics loop"""
        while True:
            try:
                # Update performance metrics
                if self.continuous_engine:
                    report = self.continuous_engine.generate_learning_report()

                    if "overall_performance" in report:
                        perf = report["overall_performance"]
                        self.performance_metrics["total_profit_usd"] = perf.get(
                            "total_profit_usd", 0
                        )
                        self.performance_metrics["learning_accuracy"] = report.get(
                            "learning_metrics", {}
                        ).get("model_accuracy", 0)

                # Generate performance report
                self.generate_performance_report()

                # Wait before next monitoring cycle
                time.sleep(self.config["reporting_frequency_minutes"] * 60)

            except Exception as e:
                print(f"⚠️ Performance monitoring error: {e}")
                time.sleep(300)

    def main_control_loop(self):
        """Main control loop for bot operation"""
        print("🎮 MAIN CONTROL LOOP ACTIVE")
        print("Commands: 'status', 'report', 'analyze', 'quit'")
        print()

        while True:
            try:
                # Check for user input (non-blocking)
                command = input("VictoryChain> ").strip().lower()

                if command == "quit" or command == "exit":
                    break
                elif command == "status":
                    self.show_status()
                elif command == "report":
                    self.generate_detailed_report()
                elif command == "analyze":
                    self.run_comprehensive_analysis_suite()
                elif command == "help":
                    self.show_help()
                else:
                    print("❓ Unknown command. Type 'help' for available commands.")

            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"⚠️ Control loop error: {e}")

    def show_status(self):
        """Show current bot status"""
        print("\n📊 VICTORYCHAIN BOT STATUS")
        print("=" * 40)
        print(f"Operation Mode: {self.config['operation_mode']}")
        print(
            f"Active Since: {self.performance_metrics['active_since'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print(f"Sessions: {self.performance_metrics['total_sessions']}")
        print(
            f"Successful Reallocations: {self.performance_metrics['successful_reallocations']}"
        )
        print(f"Total Profit: ${self.performance_metrics['total_profit_usd']:.2f}")
        print(f"Learning Accuracy: {self.performance_metrics['learning_accuracy']:.1%}")

        # System status
        print("\n🔧 System Status:")
        print(
            f"   Continuous Engine: {'✅ Active' if self.continuous_engine else '❌ Offline'}"
        )
        print(f"   Momentum Bot: {'✅ Active' if self.momentum_bot else '❌ Offline'}")
        print(f"   MAGIC System: {'✅ Active' if self.magic_system else '❌ Offline'}")

        # Active positions
        if self.continuous_engine and self.continuous_engine.active_positions:
            print("\n💼 Active Positions:")
            for token, position in self.continuous_engine.active_positions.items():
                print(
                    f"   {token}: {position.actual_gain:.1%} gain, {position.holding_period_hours:.1f}h"
                )
        else:
            print("\n💼 No active positions")
        print()

    def show_help(self):
        """Show available commands"""
        print("\n📋 AVAILABLE COMMANDS:")
        print("=" * 30)
        print("status    - Show current bot status")
        print("report    - Generate detailed performance report")
        print("analyze   - Run comprehensive analysis suite")
        print("help      - Show this help message")
        print("quit/exit - Stop the bot")
        print()

    def generate_performance_report(self):
        """Generate periodic performance report"""
        if not self.continuous_engine:
            return

        try:
            report = self.continuous_engine.generate_learning_report()

            print(f"\n📈 PERFORMANCE UPDATE - {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 50)

            if "overall_performance" in report:
                perf = report["overall_performance"]
                print(f"💰 Profit: ${perf.get('total_profit_usd', 0):.2f}")
                print(f"🎯 Success Rate: {perf.get('success_rate', 0):.1%}")
                print(f"📊 Active Positions: {perf.get('active_positions', 0)}")

            if "current_opportunities" in report and report["current_opportunities"]:
                top_opp = report["current_opportunities"][0]
                print(
                    f"🚀 Top Opportunity: {top_opp['token']} ({top_opp['predicted_gain']:.1%})"
                )

        except Exception as e:
            print(f"⚠️ Performance report error: {e}")

    def generate_detailed_report(self):
        """Generate detailed comprehensive report"""
        print("\n📊 GENERATING DETAILED REPORT...")

        try:
            # Continuous learning report
            if self.continuous_engine:
                cl_report = self.continuous_engine.generate_learning_report()

                print("\n🧠 CONTINUOUS LEARNING REPORT")
                print("=" * 50)

                if "overall_performance" in cl_report:
                    perf = cl_report["overall_performance"]
                    print(f"Total Allocations: {perf['total_allocations']}")
                    print(f"Success Rate: {perf['success_rate']:.1%}")
                    print(f"Average Gain: {perf['average_gain']:.1%}")
                    print(f"Total Profit: ${perf['total_profit_usd']:.2f}")

                if "learning_metrics" in cl_report:
                    metrics = cl_report["learning_metrics"]
                    print(f"\nLearning Metrics:")
                    print(f"  Model Accuracy: {metrics['model_accuracy']:.3f}")
                    print(
                        f"  Prediction Accuracy: {metrics['prediction_accuracy']:.3f}"
                    )
                    print(f"  Adaptation Score: {metrics['adaptation_score']:.3f}")

                print("\n🎯 Token Performance:")
                if "token_performance" in cl_report:
                    for token, perf in cl_report["token_performance"].items():
                        print(
                            f"  {token}: {perf['success_rate']:.1%} success, {perf['avg_gain']:.1%} avg gain"
                        )

            # Momentum bot report
            if self.momentum_bot:
                print("\n📈 MOMENTUM BOT STATUS")
                print("=" * 50)
                signals = self.momentum_bot.generate_ai_trading_signals()
                print(f"Active Signals: {len(signals)}")

                for signal in signals[:3]:  # Show top 3
                    print(f"  {signal.symbol}: {signal.ai_confidence:.2f} confidence")

            # Save report to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"victorychain_report_{timestamp}.json"

            combined_report = {
                "timestamp": datetime.now().isoformat(),
                "bot_config": self.config,
                "performance_metrics": self.performance_metrics,
                "continuous_learning": cl_report if self.continuous_engine else None,
            }

            with open(report_file, "w") as f:
                json.dump(combined_report, f, indent=2, default=str)

            print(f"\n💾 Detailed report saved: {report_file}")

        except Exception as e:
            print(f"⚠️ Detailed report error: {e}")

    def shutdown_gracefully(self):
        """Shutdown bot gracefully"""
        print("\n🛑 SHUTTING DOWN VICTORYCHAIN BOT...")

        try:
            # Save final performance data
            if self.continuous_engine:
                self.continuous_engine.save_learning_data()
                print("✅ Learning data saved")

            # Generate final report
            final_report = {
                "shutdown_time": datetime.now().isoformat(),
                "total_runtime_hours": (
                    datetime.now() - self.performance_metrics["active_since"]
                ).total_seconds()
                / 3600,
                "final_metrics": self.performance_metrics,
            }

            with open("victorychain_final_session.json", "w") as f:
                json.dump(final_report, f, indent=2, default=str)

            print("✅ Final session data saved")
            print("🎮 VictoryChain Bot shutdown complete")

        except Exception as e:
            print(f"⚠️ Shutdown error: {e}")


def main():
    """Main function to run Enhanced VictoryChain Bot"""
    print("🎮 ENHANCED VICTORYCHAIN BOT")
    print("=" * 60)
    print("🚀 Advanced AI Trading Bot with Continuous Learning")
    print("🧠 Real-time Analysis | Dynamic Reallocation | Pattern Learning")
    print("💎 Gaming Sector Focus | MAGIC-like Pattern Detection")
    print()

    try:
        # Create and start the bot
        bot = EnhancedVictoryChainBot()

        # Run initial analysis suite
        print("🔍 Running initial comprehensive analysis...")
        initial_analysis = bot.run_comprehensive_analysis_suite()

        print("\n✅ Initial analysis complete!")
        print("🚀 Starting continuous operation...")

        # Start continuous operation
        bot.start_continuous_operation()

    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
