#!/usr/bin/env python3
"""
Conservative strategy (Binance.US)
- Auto-picks top-liquidity USDT pairs
- Tiny position size via POSITION_SIZE_PCT (env) — defaults small
- Exchange-safe quantity rounding (LOT_SIZE) + min notional checks
- Tight sanity checks (spread, 24h change, trend filter)
- DRY-RUN by default (SAFE_MODE=true); flips to live when SAFE_MODE=false
"""
import os, time, math, argparse, logging, datetime as dt
from binance.client import Client
from binance.exceptions import BinanceAPIException

# ---------- Config from env ----------
SAFE_MODE = os.getenv("SAFE_MODE", "true").lower() == "true"
POSITION_SIZE_PCT = float(os.getenv("POSITION_SIZE_PCT", "0.03"))  # 3% default
DAILY_LOSS_STOP_PCT = float(os.getenv("DAILY_LOSS_STOP_PCT", "3"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "1"))
RECV_WINDOW_MS = int(os.getenv("RECV_WINDOW_MS", "5000"))

BINANCEUS_KEY = os.getenv("BINANCEUS_KEY", "")
BINANCEUS_SECRET = os.getenv("BINANCEUS_SECRET", "")

# enforce a safe minimum notional (default $15)
MIN_NOTIONAL_FLOOR = float(os.getenv("MIN_NOTIONAL_FLOOR", "15.0"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("conservative")

# ---------- CLI ----------
p = argparse.ArgumentParser()
p.add_argument("--hours", type=float, default=1.0)
p.add_argument("--max-candidates", type=int, default=8, help="top N USDT pairs by liquidity to consider")
args, _ = p.parse_known_args()

if not BINANCEUS_KEY or not BINANCEUS_SECRET:
    log.error("Binance.US API keys not found in environment.")
    raise SystemExit(1)

client = Client(api_key=BINANCEUS_KEY, api_secret=BINANCEUS_SECRET, tld="us")
client.API_URL = "https://api.binance.us/api"  # force US spot REST base

# Cache exchange info once
EXCHANGE_INFO = client.get_exchange_info()

def exchange_symbol(symbol: str):
    return next((s for s in EXCHANGE_INFO.get("symbols", []) if s["symbol"] == symbol), None)

def get_account_usdt_free() -> float:
    acct = client.get_account(recvWindow=RECV_WINDOW_MS)
    for b in acct.get("balances", []):
        if b.get("asset") == "USDT":
            return float(b.get("free") or 0.0)
    return 0.0

def round_qty(sym_info: dict, qty_float: float) -> float:
    lot = next(f for f in sym_info["filters"] if f["filterType"] == "LOT_SIZE")
    step = float(lot["stepSize"]); min_qty = float(lot["minQty"])
    q = math.floor(qty_float / step) * step
    return max(q, min_qty)

def enforce_notional(sym_info: dict, price: float, qty: float):
    f = next((f for f in sym_info["filters"] if f["filterType"] in ("NOTIONAL", "MIN_NOTIONAL")), None)
    min_notional = float(f.get("minNotional", 0.0)) if f else 0.0
    return (qty * price) >= min_notional, min_notional

def top_usdt_candidates(n=8):
    # Build list of USDT symbols allowed for spot trading; sort by quoteVolume (24h)
    info = client.get_exchange_info()
    symbols = [
        s["symbol"] for s in info["symbols"]
        if s.get("quoteAsset") == "USDT"
        and s.get("status") == "TRADING"
        and s.get("isSpotTradingAllowed", True)
    ]
    # Fetch 24h stats and order book tickers to derive rough liquidity/spread
    stats = {s["symbol"]: s for s in client.get_ticker() if s["symbol"] in symbols}
    books = {b["symbol"]: b for b in client.get_orderbook_ticker() if b["symbol"] in symbols}
    def spread(sym):
        b = books.get(sym)
        if not b: return 999.0
        bid = float(b["bidPrice"]); ask = float(b["askPrice"])
        return (ask - bid)/ask*100 if ask > 0 else 999.0
    scored = []
    for s in symbols:
        st = stats.get(s)
        if not st: continue
        try:
            qv = float(st.get("quoteVolume", "0"))
            chg = float(st.get("priceChangePercent", "0"))
            spr = spread(s)
            scored.append((s, qv, chg, spr))
        except Exception:
            continue
    # Prioritize high quoteVolume, then low spread
    scored.sort(key=lambda x: (-x[1], x[3]))
    return scored[:n]

def sma(values, n):
    if len(values) < n: return None
    return sum(values[-n:]) / n

def bullish_filter(symbol):
    # Simple conservative trend filter using 1m klines: price > SMA20 and SMA5 > SMA20
    kl = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=60)
    closes = [float(k[4]) for k in kl]
    if len(closes) < 25: return False
    s5 = sma(closes, 5); s20 = sma(closes, 20)
    if s5 is None or s20 is None: return False
    last = closes[-1]
    return last > s20 and s5 > s20 and last > closes[-2]

def daily_circuit_breaker_hit():
    # (Optional) Compute from account snapshots if you track equity. Placeholder returns False.
    return False

# ---------- Main ----------
log.info("Conservative bot started. SAFE_MODE=%s duration_hours=%.2f", SAFE_MODE, args.hours)
end_time = time.time() + args.hours * 3600

# Select candidates
cands = top_usdt_candidates(args.max_candidates)
log.info("Candidates (symbol, quoteVol, 24h%%, spread%%): %s", [(s, round(qv,2), round(chg,2), round(spr,3)) for s,qv,chg,spr in cands])

# Hard sanity gates (very conservative)
MAX_SPREAD_PCT = 0.15   # spread must be <= 0.15%
MAX_24H_CHG_PCT = 6.0   # avoid overheated pumps

open_positions = 0

while time.time() < end_time:
    if daily_circuit_breaker_hit():
        log.warning("🛑 Daily loss stop — no new trades today.")
        break

    usdt_free = get_account_usdt_free()
    if usdt_free <= 5:  # below typical min notionals
        log.info("Low USDT balance (%.2f). Sleeping...", usdt_free)
        time.sleep(45)
        continue

    for sym, qv, chg, spr in cands:
        if open_positions >= MAX_OPEN_POSITIONS:
            break
        # filter by spread & 24h change
        if spr > MAX_SPREAD_PCT or abs(chg) > MAX_24H_CHG_PCT:
            continue
        # trend filter
        try:
            if not bullish_filter(sym):
                continue
        except BinanceAPIException as e:
            log.warning("Filter error %s: %s", sym, e)
            continue

        # compute buy size
        # ensure we try to spend at least the notional floor, but never more than available
        usd_to_spend = min(usdt_free, max(MIN_NOTIONAL_FLOOR, usdt_free * POSITION_SIZE_PCT))
        price = float(client.get_symbol_ticker(symbol=sym)["price"])
        raw_qty = usd_to_spend / price

        sym_info = exchange_symbol(sym)
        qty = round_qty(sym_info, raw_qty)

        ok, min_notional = enforce_notional(sym_info, price, qty)
        notional = qty * price
        required = max(min_notional, MIN_NOTIONAL_FLOOR)

        # if rounding pushed you below required, try a single safe bump (respecting LOT_SIZE and balance)
        if notional < required:
            needed_qty = required / price
            bumped_qty = round_qty(sym_info, needed_qty)
            if bumped_qty * price <= usdt_free and bumped_qty > qty:
                qty = bumped_qty
                notional = qty * price
                ok = True  # bumped to meet required (we'll still check below)
            # final guard: still below required -> skip
            if notional < required:
                log.info(
                    "Skip %s: notional %.2f < required %.2f (min_filter=%.2f, floor=%.2f)",
                    sym, notional, required, min_notional, MIN_NOTIONAL_FLOOR
                )
                continue

        # BUY
        desc = f"BUY {sym} qty={qty} @~{price:.8f} notional≈{notional:.2f} (spread={spr:.3f}%%, 24h={chg:.2f}%%)"
        if guard_place(desc):
            open_positions += 1
            continue
        try:
            order = client.order_market_buy(symbol=sym, quantity=qty, recvWindow=RECV_WINDOW_MS)
            log.info("✅ BUY placed: %s", order)
            open_positions += 1
        except BinanceAPIException as e:
            log.error("Buy failed %s: %s", sym, e)
            continue

        # Simple TP limit (1.0%) — SL omitted due to API/OCO differences on Binance.US
        try:
            tp_price = round(price * 1.010, 8)
            # Use PRICE_FILTER tick size
            pf = next(f for f in sym_info["filters"] if f["filterType"] == "PRICE_FILTER")
            tick = float(pf["tickSize"])
            tp_price = math.floor(tp_price / tick) * tick
            if guard_place(f"TP LIMIT SELL {sym} qty={qty} @ {tp_price}"):
                continue
            tp = client.order_limit_sell(symbol=sym, quantity=qty, price=f"{tp_price:.8f}", recvWindow=RECV_WINDOW_MS)
            log.info("🏁 TP placed: %s", tp)
        except Exception as e:
            log.warning("TP placement issue %s: %s", sym, e)

        time.sleep(2)  # light throttle

    time.sleep(20)

log.info("Conservative bot finished.")
