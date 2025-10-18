#!/usr/bin/env python3

"""
⏰ AUTOMATED CONSOLIDATION SCHEDULER
Runs Claude-powered portfolio consolidation on schedule
"""

import os
import sys
import time
import json
import schedule
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()


class ConsolidationScheduler:
    def __init__(self):
        self.last_consolidation = None
        self.consolidation_history = []
        self.is_running = False

        # Load settings
        self.settings = {
            "auto_consolidation_enabled": True,
            "check_interval_hours": 6,  # Check every 6 hours
            "min_diversification_threshold": 3,  # Consolidate if 3+ positions
            "min_confidence_threshold": 0.75,  # Require 75% confidence
            "max_consolidations_per_day": 2,  # Max 2 consolidations per day
            "consolidation_cooldown_hours": 4,  # Wait 4 hours between consolidations
        }

        print("⏰ Automated Consolidation Scheduler Initialized")

    def load_consolidation_history(self):
        """Load previous consolidation history"""
        try:
            if os.path.exists("consolidation_log.json"):
                with open("consolidation_log.json", "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.strip():
                            entry = json.loads(line.strip())
                            self.consolidation_history.append(entry)

                # Get last consolidation time
                if self.consolidation_history:
                    last_entry = self.consolidation_history[-1]
                    self.last_consolidation = datetime.fromisoformat(
                        last_entry["timestamp"]
                    )

                print(
                    f"📜 Loaded {len(self.consolidation_history)} consolidation records"
                )

        except Exception as e:
            print(f"⚠️  Error loading history: {e}")

    def should_run_consolidation(self):
        """Check if consolidation should run based on conditions"""
        now = datetime.now()

        # Check cooldown period
        if self.last_consolidation:
            hours_since_last = (now - self.last_consolidation).total_seconds() / 3600
            if hours_since_last < self.settings["consolidation_cooldown_hours"]:
                print(
                    f"⏳ Cooldown active: {hours_since_last:.1f}h since last consolidation"
                )
                return False

        # Check daily limit
        today = now.date()
        today_consolidations = sum(
            1
            for entry in self.consolidation_history
            if datetime.fromisoformat(entry["timestamp"]).date() == today
        )

        if today_consolidations >= self.settings["max_consolidations_per_day"]:
            print(
                f"📊 Daily limit reached: {today_consolidations} consolidations today"
            )
            return False

        # Check if portfolio needs consolidation
        try:
            result = subprocess.run(
                ["python3", "claude_auto_consolidator.py", "--check-only"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Parse output to check diversification
                output = result.stdout
                if "positions" in output.lower():
                    return True

        except Exception as e:
            print(f"⚠️  Portfolio check failed: {e}")

        return True

    def run_consolidation(self):
        """Execute the consolidation process"""
        if not self.settings["auto_consolidation_enabled"]:
            print("⏸️  Auto-consolidation disabled")
            return

        if not self.should_run_consolidation():
            return

        try:
            print(f"\n🚀 STARTING AUTOMATED CONSOLIDATION")
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            # Run the consolidation
            result = subprocess.run(
                ["python3", "claude_auto_consolidator.py"],
                capture_output=True,
                text=True,
                timeout=300,
            )  # 5 minute timeout

            print(result.stdout)

            if result.stderr:
                print(f"⚠️  Errors: {result.stderr}")

            if result.returncode == 0:
                print("✅ Consolidation process completed")
                self.last_consolidation = datetime.now()
            else:
                print(f"❌ Consolidation failed with code {result.returncode}")

        except subprocess.TimeoutExpired:
            print("⏰ Consolidation timed out")
        except Exception as e:
            print(f"❌ Consolidation error: {e}")

    def status_check(self):
        """Periodic status check and logging"""
        print(f"\n📊 CONSOLIDATION SCHEDULER STATUS")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(
            f"Auto-consolidation: {'✅ Enabled' if self.settings['auto_consolidation_enabled'] else '❌ Disabled'}"
        )
        print(f"Check interval: {self.settings['check_interval_hours']} hours")
        print(
            f"Last consolidation: {self.last_consolidation.strftime('%Y-%m-%d %H:%M:%S') if self.last_consolidation else 'Never'}"
        )
        print(f"Total consolidations: {len(self.consolidation_history)}")

        # Show recent activity
        if self.consolidation_history:
            recent = [
                entry
                for entry in self.consolidation_history
                if datetime.fromisoformat(entry["timestamp"])
                > datetime.now() - timedelta(days=7)
            ]
            print(f"This week: {len(recent)} consolidations")

    def emergency_stop(self):
        """Emergency stop function"""
        self.settings["auto_consolidation_enabled"] = False
        print("🚨 EMERGENCY STOP ACTIVATED - Auto-consolidation disabled")

    def start_scheduler(self):
        """Start the automated scheduler"""
        self.load_consolidation_history()

        # Schedule regular consolidation checks
        schedule.every(self.settings["check_interval_hours"]).hours.do(
            self.run_consolidation
        )

        # Schedule status checks
        schedule.every(1).hours.do(self.status_check)

        # Initial status
        self.status_check()

        print(f"\n⏰ SCHEDULER STARTED")
        print(
            f"Next consolidation check: {datetime.now() + timedelta(hours=self.settings['check_interval_hours'])}"
        )
        print("Press Ctrl+C to stop")

        self.is_running = True

        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            print("\n⏹️  Scheduler stopped by user")
            self.is_running = False
        except Exception as e:
            print(f"\n❌ Scheduler error: {e}")
            self.is_running = False


def main():
    """Main function with command line options"""
    scheduler = ConsolidationScheduler()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "start":
            scheduler.start_scheduler()
        elif command == "run-now":
            scheduler.run_consolidation()
        elif command == "status":
            scheduler.load_consolidation_history()
            scheduler.status_check()
        elif command == "stop":
            scheduler.emergency_stop()
        elif command == "enable":
            scheduler.settings["auto_consolidation_enabled"] = True
            print("✅ Auto-consolidation enabled")
        elif command == "disable":
            scheduler.settings["auto_consolidation_enabled"] = False
            print("❌ Auto-consolidation disabled")
        else:
            print(
                "Usage: python3 auto_consolidation_scheduler.py [start|run-now|status|stop|enable|disable]"
            )
    else:
        # Default: start scheduler
        scheduler.start_scheduler()


if __name__ == "__main__":
    main()
