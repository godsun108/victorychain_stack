#!/usr/bin/env python3
"""Plot equity & realized PnL from equity_curve.csv.
Usage:
  python3 plot_equity.py reports/equity_curve.csv reports/equity_curve.png
"""
import sys, csv
from pathlib import Path
import matplotlib

matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt


def read_csv(p: Path):
    rows = []
    with p.open(newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                rows.append(
                    {
                        "iso": row["iso"],
                        "realized": float(row["realized"]),
                        "equity_mtm": float(row["equity_mtm"]),
                    }
                )
            except Exception:
                pass
    return rows


def main():
    if len(sys.argv) < 3:
        print("Usage: plot_equity.py <equity_curve.csv> <out.png>")
        sys.exit(2)
    inp = Path(sys.argv[1])
    outp = Path(sys.argv[2])
    if not inp.exists():
        print("Missing input CSV", inp)
        sys.exit(1)
    rows = read_csv(inp)
    if not rows:
        print("No rows in equity CSV:", inp)
        sys.exit(1)
    xs = [r["iso"] for r in rows]
    yr = [r["realized"] for r in rows]
    ymt = [r["equity_mtm"] for r in rows]
    plt.figure(figsize=(10, 4))
    plt.plot(xs, yr, label="Realized PnL")
    plt.plot(xs, ymt, label="Equity (MTM)")
    plt.title("Equity curve (ledger replay)")
    plt.xlabel("time (UTC)")
    plt.ylabel("USD")
    plt.xticks(rotation=45, ha="right")
    plt.legend()
    plt.tight_layout()
    outp.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(outp, dpi=150)
    print("wrote", outp)


if __name__ == "__main__":
    main()
