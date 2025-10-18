#!/usr/bin/env python3
"""Print BinanceUS symbol filter sanity based on env + ccxt markets.
Usage:
  python3 scripts/binance_filters.py .env.live
Optional ENV file argument (defaults .env.live). Loads MODE/keys then prints minQty/step/tick/minNotional.
"""
import os, sys, json
from typing import Dict, Any
from dotenv import load_dotenv

if len(sys.argv) > 1:
    envp = sys.argv[1]
else:
    envp = ".env.live"
if os.path.exists(envp):
    load_dotenv(envp)

MODE = os.getenv("MODE", "paper")
print(f"MODE={MODE}")

try:
    import ccxt
except Exception as e:
    print("ccxt import failed:", e)
    sys.exit(1)

try:
    ex = ccxt.binanceus(
        {
            "apiKey": os.getenv("BINANCEUS_API_KEY") or os.getenv("BINANCEUS_KEY"),
            "secret": os.getenv("BINANCEUS_API_SECRET")
            or os.getenv("BINANCEUS_SECRET"),
            "enableRateLimit": True,
            "timeout": 20000,
        }
    )
    mkts = ex.load_markets()
except Exception as e:
    print("load_markets_failed", e)
    sys.exit(1)

symbols = [
    s.strip() for s in os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT").split(",") if s.strip()
]
print("Checking symbols:", symbols)


def filt(m: Dict[str, Any]):
    info = (m or {}).get("info", {})
    out = {}
    for f in info.get("filters", []):
        t = f.get("filterType")
        if t == "LOT_SIZE":
            out["minQty"] = f.get("minQty")
            out["stepSize"] = f.get("stepSize")
        elif t == "PRICE_FILTER":
            out["tickSize"] = f.get("tickSize")
        elif t in ("MIN_NOTIONAL", "NOTIONAL"):
            out["minNotional"] = f.get("minNotional") or f.get("notional")
    return out


rows = []
for s in symbols:
    m = mkts.get(s)
    rows.append({"symbol": s, **filt(m)})

print(json.dumps(rows, indent=2))
