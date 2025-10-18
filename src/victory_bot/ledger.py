"""
victory_bot/ledger.py
Trade/event ledger for Victory Trading Bot
"""

import csv
import json
from datetime import datetime
from .config import LEDGER_DIR, REPORTS_DIR
from pathlib import Path


class LedgerWriter:
    def __init__(self, name: str):
        self.ledger_file = (
            LEDGER_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.jsonl"
        )
        self.csv_file = REPORTS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.csv"
        Path(LEDGER_DIR).mkdir(parents=True, exist_ok=True)
        Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)

    def log(self, event: dict):
        event["timestamp"] = datetime.utcnow().isoformat()
        with open(self.ledger_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        # Write to CSV (flattened)
        with open(self.csv_file, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=event.keys())
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(event)
