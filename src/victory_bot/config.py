"""
victory_bot/config.py
Central config for Victory Trading Bot
"""

import os
from pathlib import Path

# Base directory for all relative paths
BASE_DIR = Path(__file__).resolve().parents[2]

# Metrics port (single port for all modules)
METRICS_PORT = int(os.getenv("VICTORY_BOT_METRICS_PORT", 9400))
print(f"[VictoryBot][config] METRICS_PORT set to {METRICS_PORT}")

# Reserve assets for the Church
RESERVE_ASSETS = ["XRP", "HBAR", "LINK", "XLM"]

# Minimum reserve ratio (e.g. 10% of portfolio)
MIN_RESERVE_RATIO = float(os.getenv("VICTORY_BOT_MIN_RESERVE_RATIO", 0.10))

# Portion of profits to bank into reserves (e.g. 0.20 for 20%)
PROFIT_BANKING_RATIO = float(os.getenv("VICTORY_BOT_PROFIT_BANKING_RATIO", 0.20))

# Data, reports, runtime paths
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
LEDGER_DIR = BASE_DIR / "runtime" / "ledger"
AUDIT_DIR = BASE_DIR / "runtime" / "audit"

# ...add more config as needed...
