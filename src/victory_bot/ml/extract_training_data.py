# extract_training_data.py
"""
Extracts training data for ML from dashboard_results.json and symbol_performance.json.
Appends to a CSV for model training.
"""
import json
import csv
import os
from datetime import datetime

DASHBOARD_PATH = "runtime/dashboard_results.json"
PERF_PATH = "runtime/symbol_performance.json"
OUT_CSV = "runtime/training_data.csv"


def extract():
    if not os.path.exists(DASHBOARD_PATH):
        print("No dashboard_results.json found.")
        return
    with open(DASHBOARD_PATH, "r") as f:
        dash = json.load(f)
    if not os.path.exists(PERF_PATH):
        symbol_perf = {}
    else:
        with open(PERF_PATH, "r") as f:
            symbol_perf = json.load(f)
    analytics = dash.get("analytics", [])
    # Use allocations as positive label, others as negative
    alloc_syms = set((dash.get("allocations") or {}).keys())
    rows = []
    for row in analytics:
        sym, vol, trend, liq = row
        pnl = symbol_perf.get(sym, 0)
        label = 1 if sym in alloc_syms and pnl > 0 else 0
        rows.append([sym, vol, trend, liq, pnl, label])
    # Write/append to CSV
    write_header = not os.path.exists(OUT_CSV)
    with open(OUT_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(
                ["symbol", "volatility", "trend", "liquidity", "pnl", "label"]
            )
        writer.writerows(rows)
    print(f"Appended {len(rows)} rows to {OUT_CSV}")


if __name__ == "__main__":
    extract()
