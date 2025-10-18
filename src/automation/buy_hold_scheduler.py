#!/usr/bin/env python3

"""
⏰ BUY AND HOLD SCHEDULER
Automated scheduling for Claude-powered buy and hold system
"""

import os
import sys
import time
import json
import schedule
import threading
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BuyHoldScheduler:
    def __init__(self):
        self.is_running = False
        self.last_execution = None
        self.execution_history = []

        # Buy and Hold Schedule Settings
        self.settings = {
            "enabled": True,
            "frequency": "daily",  # daily, weekly, bi-weekly, monthly
            "execution_time": "09:00",  # Time to run (09:00 AM)
            "max_executions_per_day": 1,  # Safety limit
            "cooldown_hours": 12,  # Minimum hours between executions
            "weekend_trading": False,  # Trade on weekends
            "auto_execute_threshold": 0.75,  # Auto-execute if confidence >= 75%
        }

        print("⏰ Buy and Hold Scheduler Initialized")
        print(f"📅 Frequency: {self.settings['frequency']}")
        print(f"🕘 Execution Time: {self.settings['execution_time']}")

    def load_execution_history(self):
        """Load execution history"""
        try:
            if os.path.exists("buy_hold_schedule_log.json"):
                with open("buy_hold_schedule_log.json", "r") as f:
                    self.execution_history = json.load(f)

                if self.execution_history:
                    last_entry = self.execution_history[-1]
                    self.last_execution = datetime.fromisoformat(
                        last_entry["timestamp"]
                    )

                print(f"📜 Loaded {len(self.execution_history)} execution records")

        except Exception as e:
            print(f"⚠️  Error loading history: {e}")

    def save_execution_log(self, result):
        """Save execution result to log"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "result": result,
                "frequency": self.settings["frequency"],
                "auto_executed": True,
            }

            self.execution_history.append(log_entry)

            with open("buy_hold_schedule_log.json", "w") as f:
                json.dump(self.execution_history, f, indent=2)

        except Exception as e:
            print(f"⚠️  Error saving log: {e}")

    def should_execute(self):
        """Check if execution should proceed"""
        now = datetime.now()

        # Check if enabled
        if not self.settings["enabled"]:
            print("⏸️  Buy and hold scheduler disabled")
            return False

        # Check weekend trading
        if (
            not self.settings["weekend_trading"] and now.weekday() >= 5
        ):  # Saturday=5, Sunday=6
            print("📅 Weekend trading disabled")
            return False

        # Check cooldown period
        if self.last_execution:
            hours_since_last = (now - self.last_execution).total_seconds() / 3600
            if hours_since_last < self.settings["cooldown_hours"]:
                print(
                    f"⏳ Cooldown active: {hours_since_last:.1f}h since last execution"
                )
                return False

        # Check daily execution limit
        today = now.date()
        today_executions = sum(
            1
            for entry in self.execution_history
            if datetime.fromisoformat(entry["timestamp"]).date() == today
        )

        if today_executions >= self.settings["max_executions_per_day"]:
            print(f"📊 Daily limit reached: {today_executions} executions today")
            return False

        return True

    def execute_buy_hold_cycle(self):
        """Execute the buy and hold analysis and actions"""
        if not self.should_execute():
            return

        try:
            print(f"\n💎 SCHEDULED BUY & HOLD EXECUTION")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            # Run the buy and hold system
            result = subprocess.run(
                ["python3", "claude_buy_hold.py", "run"],
                capture_output=True,
                text=True,
                timeout=300,
            )  # 5 minute timeout

            print(result.stdout)

            if result.stderr:
                print(f"⚠️  Warnings: {result.stderr}")

            # Determine success
            success = result.returncode == 0

            execution_result = {
                "success": success,
                "return_code": result.returncode,
                "output_length": len(result.stdout),
                "has_errors": bool(result.stderr),
                "execution_duration": "completed",
            }

            if success:
                print("✅ Buy and hold cycle completed successfully")
                self.last_execution = datetime.now()

                # Check if any actions were executed
                if "BUY EXECUTED" in result.stdout or "AUTO-EXECUTING" in result.stdout:
                    execution_result["actions_executed"] = True
                    print("💎 Investment actions were executed")
                else:
                    execution_result["actions_executed"] = False
                    print("📊 Analysis completed, no actions needed")
            else:
                print(f"❌ Buy and hold cycle failed with code {result.returncode}")
                execution_result["error_details"] = result.stderr

            # Save execution log
            self.save_execution_log(execution_result)

        except subprocess.TimeoutExpired:
            print("⏰ Buy and hold execution timed out")
            self.save_execution_log(
                {"success": False, "error": "timeout", "execution_duration": "timeout"}
            )
        except Exception as e:
            print(f"❌ Execution error: {e}")
            self.save_execution_log(
                {"success": False, "error": str(e), "execution_duration": "error"}
            )

    def daily_status_report(self):
        """Generate daily status report"""
        print(f"\n📊 DAILY BUY & HOLD STATUS REPORT")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        print("=" * 50)

        # Portfolio status
        try:
            result = subprocess.run(
                ["python3", "claude_buy_hold.py", "status"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print(result.stdout)
            else:
                print("⚠️  Could not fetch portfolio status")
        except:
            print("⚠️  Portfolio status check failed")

        # Scheduler status
        print(f"\n⏰ SCHEDULER STATUS:")
        print(f"   Enabled: {'✅' if self.settings['enabled'] else '❌'}")
        print(f"   Frequency: {self.settings['frequency']}")
        print(
            f"   Last Execution: {self.last_execution.strftime('%Y-%m-%d %H:%M:%S') if self.last_execution else 'Never'}"
        )
        print(f"   Total Executions: {len(self.execution_history)}")

        # Recent performance
        if self.execution_history:
            recent_executions = [
                e
                for e in self.execution_history
                if datetime.fromisoformat(e["timestamp"])
                > datetime.now() - timedelta(days=7)
            ]
            successful_executions = sum(
                1 for e in recent_executions if e.get("success", False)
            )

            print(
                f"   This Week: {len(recent_executions)} executions, {successful_executions} successful"
            )

    def start_scheduler(self):
        """Start the buy and hold scheduler"""
        self.load_execution_history()

        # Schedule based on frequency
        if self.settings["frequency"] == "daily":
            schedule.every().day.at(self.settings["execution_time"]).do(
                self.execute_buy_hold_cycle
            )
        elif self.settings["frequency"] == "weekly":
            schedule.every().monday.at(self.settings["execution_time"]).do(
                self.execute_buy_hold_cycle
            )
        elif self.settings["frequency"] == "bi-weekly":
            schedule.every(14).days.at(self.settings["execution_time"]).do(
                self.execute_buy_hold_cycle
            )
        elif self.settings["frequency"] == "monthly":
            schedule.every(30).days.at(self.settings["execution_time"]).do(
                self.execute_buy_hold_cycle
            )

        # Schedule daily status report
        schedule.every().day.at("18:00").do(self.daily_status_report)

        # Initial status
        self.daily_status_report()

        print(f"\n⏰ BUY & HOLD SCHEDULER STARTED")
        print(f"📅 Frequency: {self.settings['frequency']}")
        print(f"🕘 Next execution: {self.settings['execution_time']}")
        print("Press Ctrl+C to stop")

        self.is_running = True

        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            print("\n⏹️  Buy and hold scheduler stopped by user")
            self.is_running = False
        except Exception as e:
            print(f"\n❌ Scheduler error: {e}")
            self.is_running = False

    def manual_execution(self):
        """Manual execution for testing"""
        print("🔧 MANUAL BUY & HOLD EXECUTION")
        self.execute_buy_hold_cycle()

    def update_settings(self, **kwargs):
        """Update scheduler settings"""
        for key, value in kwargs.items():
            if key in self.settings:
                old_value = self.settings[key]
                self.settings[key] = value
                print(f"✅ Updated {key}: {old_value} → {value}")
            else:
                print(f"⚠️  Unknown setting: {key}")


def main():
    """Main function with command line options"""
    scheduler = BuyHoldScheduler()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "start":
            scheduler.start_scheduler()
        elif command == "run-now":
            scheduler.manual_execution()
        elif command == "status":
            scheduler.daily_status_report()
        elif command == "enable":
            scheduler.update_settings(enabled=True)
        elif command == "disable":
            scheduler.update_settings(enabled=False)
        elif command == "daily":
            scheduler.update_settings(frequency="daily")
        elif command == "weekly":
            scheduler.update_settings(frequency="weekly")
        elif command == "monthly":
            scheduler.update_settings(frequency="monthly")
        else:
            print(
                """
💎 BUY & HOLD SCHEDULER OPTIONS:

Usage: python3 buy_hold_scheduler.py [COMMAND]

Commands:
  start     - Start the automated scheduler
  run-now   - Execute buy and hold cycle immediately
  status    - Show scheduler and portfolio status
  enable    - Enable automatic execution
  disable   - Disable automatic execution
  daily     - Set to daily frequency
  weekly    - Set to weekly frequency
  monthly   - Set to monthly frequency

Examples:
  python3 buy_hold_scheduler.py start     # Start scheduler
  python3 buy_hold_scheduler.py run-now   # Manual execution
  python3 buy_hold_scheduler.py daily     # Switch to daily
            """
            )
    else:
        # Default: start scheduler
        scheduler.start_scheduler()


if __name__ == "__main__":
    main()
