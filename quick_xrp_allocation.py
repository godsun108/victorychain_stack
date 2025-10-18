#!/usr/bin/env python3
"""
Quick XRP Allocation and Profit Banking (Binance US)
- Uses available USDT/USD balance (prefers the quote you actually have)
- Buys XRP with an allocation (now: up to 100% of free, $185 cap)
- Places adaptive multi-target take-profit sells
- Monitors and banks realized profit into ISO 20022 tokens (bias to XRP if momentum strong)
"""
import os
import time
import math
import json
from datetime import datetime
import sys
import statistics

import ccxt
from dotenv import load_dotenv

ISO_DEFAULT_ALLOCATION = {
    "XRP": 0.30,
    "XLM": 0.25,
    "ALGO": 0.20,
    "USDC": 0.15,
    "HBAR": 0.10,
}

BASE_TP1_PCT = 0.03  # 3%
STRONG_MOM_THRESHOLD = 0.02  # 2% in ~15m considered strong
TP2_WEAK = 0.05  # 5% second target when momentum is weak/moderate
TP2_STRONG = 0.06  # 6% second target when momentum is strong
TP_SPLIT_WEAK = (0.70, 0.30)  # 70% at TP1, 30% at TP2
TP_SPLIT_STRONG = (0.40, 0.60)  # 40% at TP1, 60% at TP2

ALLOC_CAP_USD = 185.0  # cap per user note
ALLOC_FRACTION = 1.00  # allocate 100% of free quote up to cap
MIN_BANK_USD = 5.0  # only bank profit if >= $5 (else keep as USDT)

# Governance adapter
try:
    from libs.exchange_adapters.binance_us import BinanceUSAdapter
except Exception:
    BinanceUSAdapter = None


def get_env_api():
    load_dotenv()
    # Prefer BINANCEUS_* names, fallback to BINANCE_*
    api_key = os.getenv("BINANCEUS_API_KEY") or os.getenv("BINANCEUS_KEY")
    api_secret = (
        os.getenv("BINANCEUS_API_SECRET")
        or os.getenv("BINANCE_API_SECRET")
        or os.getenv("BINANCEUS_SECRET")
    )
    return api_key, api_secret


def amount_to_step(amount, step):
    if step is None or step == 0:
        return amount
    return math.floor(amount / step) * step


def round_to_precision(x, decs):
    try:
        if isinstance(decs, int):
            return float(f"{x:.{decs}f}")
    except Exception:
        pass
    return x


def get_symbol(exchange, base, quote):
    sym = f"{base}/{quote}"
    markets = exchange.markets or exchange.load_markets()
    return sym if sym in markets else None


def choose_best_xrp_symbol(exchange, free_usdt: float, free_usd: float):
    """Pick XRP pair based on which quote you have available; fallback to any available."""
    sym_usdt = get_symbol(exchange, "XRP", "USDT")
    sym_usd = get_symbol(exchange, "XRP", "USD")
    # Prefer quote with sufficient balance
    if sym_usdt and free_usdt >= 10:
        return sym_usdt
    if sym_usd and free_usd >= 10:
        return sym_usd
    # Otherwise prefer USDT if exists, else USD
    return sym_usdt or sym_usd


def convert_usd_to_usdt_if_needed(
    ex, needed_usdt: float, free_usdt: float, free_usd: float
):
    """If XRP/USDT is chosen but USDT free < needed and USD is available, convert USD->USDT."""
    try:
        if free_usdt >= needed_usdt or free_usd < 10:
            return 0.0
        markets = ex.markets or ex.load_markets()
        if "USDT/USD" in markets:
            t = ex.fetch_ticker("USDT/USD")
            price = float(t.get("last") or 1.0)
            usd_to_use = min((needed_usdt - free_usdt) * price, free_usd, ALLOC_CAP_USD)
            if usd_to_use < 10:
                return 0.0
            amount_usdt = usd_to_use / price
            order = ex.create_order("USDT/USD", "market", "buy", amount_usdt)
            print(
                f"🔄 Converted ~USD {usd_to_use:.2f} -> USDT (order {order.get('id')})"
            )
            time.sleep(0.5)
            return usd_to_use / price
        if "USD/USDT" in markets:
            usd_to_use = min((needed_usdt - free_usdt), free_usd, ALLOC_CAP_USD)
            if usd_to_use < 10:
                return 0.0
            order = ex.create_order("USD/USDT", "market", "sell", usd_to_use)
            print(
                f"🔄 Converted ~USD {usd_to_use:.2f} -> USDT via USD/USDT sell (order {order.get('id')})"
            )
            time.sleep(0.5)
            return usd_to_use
    except Exception as e:
        print(f"⚠️ USD->USDT conversion skipped: {e}")
    return 0.0


def get_free_balances(exchange):
    bal = exchange.fetch_balance()
    free = bal.get("free") or {}
    return free.get("USDT", 0.0), free.get("USD", 0.0)


def read_iso_allocation_from_config():
    try:
        with open("advanced_optimizer_config.json", "r") as f:
            cfg = json.load(f)
        alloc = cfg["advanced_position_optimizer_config"]["iso_20022_reserves"].get(
            "preferred_allocation"
        )
        if isinstance(alloc, dict) and alloc:
            return alloc
    except Exception:
        pass
    return ISO_DEFAULT_ALLOCATION


def fetch_momentum(exchange, symbol):
    """Compute ~15-minute momentum and simple realized volatility from 1m candles."""
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe="1m", limit=60)
        closes = [c[4] for c in ohlcv if c and c[4] is not None]
        if len(closes) < 20:
            return 0.0, 0.0
        # momentum over last 15 minutes
        lookback = 15
        if len(closes) > lookback:
            m = (closes[-1] - closes[-1 - lookback]) / closes[-1 - lookback]
        else:
            m = (closes[-1] - closes[0]) / closes[0]
        # realized vol as stdev of 1m returns
        rets = []
        for i in range(1, len(closes)):
            if closes[i - 1] > 0:
                rets.append((closes[i] - closes[i - 1]) / closes[i - 1])
        vol = statistics.pstdev(rets) if rets else 0.0
        return float(m), float(vol)
    except Exception:
        return 0.0, 0.0


def summarize_order_costs(order, quote_ccy):
    """Compute gross quote spent/received and fee in quote for an order if possible."""
    filled = float(order.get("filled") or 0.0)
    avg = float(order.get("average") or order.get("price") or 0.0)
    gross = filled * avg
    fee_cost = 0.0
    fee_ccy = None
    fee = order.get("fee")
    fees = order.get("fees")
    if fee and isinstance(fee, dict):
        fee_cost = float(fee.get("cost") or 0.0)
        fee_ccy = fee.get("currency")
    elif fees and isinstance(fees, list) and fees:
        fee_cost = sum(float(x.get("cost") or 0.0) for x in fees)
        # pick first currency if mixed
        fee_ccy = fees[0].get("currency")
    if fee_ccy and fee_ccy != quote_ccy:
        fee_cost = 0.0
    return gross, fee_cost, filled, avg


def bank_profit(ex, profit_quote, quote_ccy):
    """Bank realized profit into ISO tokens per allocation, biased to XRP if momentum is strong."""
    if profit_quote < MIN_BANK_USD:
        print(
            f"ℹ️ Profit {quote_ccy} {profit_quote:.2f} below banking threshold; keeping in {quote_ccy}."
        )
        return

    alloc = read_iso_allocation_from_config().copy()

    # Momentum bias: overweight XRP if strong momentum
    try:
        xrp_sym = get_symbol(ex, "XRP", quote_ccy)
        if xrp_sym:
            mom, _ = fetch_momentum(ex, xrp_sym)
            if mom >= STRONG_MOM_THRESHOLD:
                alloc["XRP"] = alloc.get("XRP", 0) * 1.5
                # renormalize
                total = sum(alloc.values())
                if total > 0:
                    alloc = {k: v / total for k, v in alloc.items()}
    except Exception:
        pass

    markets = ex.markets or ex.load_markets()

    successes = 0
    # Use adapter backstop
    adapter = BinanceUSAdapter(ex) if BinanceUSAdapter else None
    for token, weight in alloc.items():
        if weight <= 0:
            continue
        spend = profit_quote * float(weight)
        if spend < 5.0:
            continue
        sym = f"{token}/{quote_ccy}"
        if sym not in markets:
            continue
        try:
            market = ex.market(sym)
            ticker = ex.fetch_ticker(sym)
            price = float(ticker.get("last") or ticker.get("close") or 0)
            if price <= 0:
                continue
            # step size handling
            step = None
            try:
                for flt in market.get("info", {}).get("filters", []):
                    if flt.get("filterType") == "LOT_SIZE":
                        step = float(flt.get("stepSize"))
                        break
            except Exception:
                pass
            amount_raw = spend / price
            amt = amount_to_step(amount_raw, step) if step else amount_raw
            if amt <= 0:
                continue
            if adapter:
                order = adapter.guarded_create_order(sym, "market", "buy", amt)
            else:
                order = ex.create_order(sym, "market", "buy", amt)
            if order is None:
                print(f"🧪 Paper mode: skipped banking into {token} ({sym})")
            else:
                print(
                    f"✅ Banked ~{quote_ccy} {spend:.2f} into {token} (order {order.get('id')})"
                )
                successes += 1
            time.sleep(0.25)
        except Exception as e:
            print(f"⚠️ Failed banking into {token}: {e}")
            continue

    if successes == 0:
        # Fallback to USDC if available
        sym = f"USDC/{quote_ccy}"
        if sym in (ex.markets or ex.load_markets()):
            try:
                ticker = ex.fetch_ticker(sym)
                price = float(ticker.get("last") or 0)
                if price > 0:
                    amt = profit_quote / price
                    if adapter:
                        order = adapter.guarded_create_order(sym, "market", "buy", amt)
                    else:
                        order = ex.create_order(sym, "market", "buy", amt)
                    if order is None:
                        print("🧪 Paper mode: skipped USDC banking")
                    else:
                        print(f"✅ Banked profit into USDC (order {order.get('id')})")
                        return
            except Exception as e:
                print(f"⚠️ USDC fallback failed: {e}")
        print(
            "ℹ️ Could not bank profit due to market/size constraints; left in quote currency."
        )


def monitor_and_bank(state_path="quick_xrp_allocation_state.json"):
    api_key, api_secret = get_env_api()
    if not api_key or not api_secret:
        print(
            "❌ Missing API env vars. Set BINANCEUS_API_KEY & BINANCEUS_API_SECRET or BINANCEUS_KEY & BINANCE_API_SECRET (or BINANCEUS_SECRET)"
        )
        return 1

    ex = ccxt.binanceus(
        {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "timeout": 30000,
            "options": {"defaultType": "spot"},
        }
    )
    adapter = BinanceUSAdapter(ex) if BinanceUSAdapter else None

    try:
        with open(state_path, "r") as f:
            state = json.load(f)
    except Exception as e:
        print(f"❌ Failed to read state: {e}")
        return 1

    symbol = state.get("symbol")
    sell_ids = state.get("sell_order_ids") or (
        [] if not state.get("sell_order_id") else [state.get("sell_order_id")]
    )
    buy_id = state.get("buy_order_id")
    quote = state.get("quote_ccy", "USDT")

    if not symbol or not sell_ids:
        print("❌ State missing symbol/sell order IDs")
        return 1

    # Track which sells already banked
    banked = state.get("banked_flags") or {}

    print(f"👀 Monitoring sell orders on {symbol} for fills...")
    deadline = time.time() + 60 * 60 * 12  # monitor up to 12 hours

    while time.time() < deadline:
        try:
            for sid in list(sell_ids):
                if banked.get(sid):
                    continue
                sell = ex.fetch_order(sid, symbol)
                status = (sell.get("status") or "").lower()
                if status == "closed":
                    print(f"✅ Take-profit order filled (id={sid}).")
                    # Compute realized PnL approximately for this partial
                    profit = 0.0
                    try:
                        sell_gross, sell_fee, sell_qty, _ = summarize_order_costs(
                            sell, quote
                        )
                        if buy_id:
                            buy = ex.fetch_order(buy_id, symbol)
                            _, _, buy_qty, _ = summarize_order_costs(buy, quote)
                        else:
                            buy_qty = float(state.get("amount", 0))
                        # proportional buy cost using order price from state
                        buy_price = float(state.get("buy_price", 0))
                        buy_fee_est = 0.0  # unknown if non-quote fee; conservative 0
                        buy_gross_alloc = sell_qty * buy_price
                        profit = (sell_gross - sell_fee) - (
                            buy_gross_alloc + buy_fee_est
                        )
                    except Exception as e:
                        print(f"⚠️ Could not compute precise PnL: {e}")
                        profit = max(0.0, sell.get("cost") or 0.0) - float(
                            state.get("buy_price", 0)
                        ) * float(sell.get("filled") or 0)
                    print(f"💵 Realized profit (approx): {quote} {profit:.2f}")
                    bank_profit(ex, max(0.0, profit), quote)
                    banked[sid] = True
                    state["banked_flags"] = banked
                    with open(state_path, "w") as f:
                        json.dump(state, f, indent=2)
            # Exit when all banked
            if sell_ids and all(banked.get(sid) for sid in sell_ids):
                print("🥳 All targets filled and profits banked.")
                return 0
        except Exception as e:
            print(f"⚠️ Monitor error: {e}")
        time.sleep(10)

    print("⌛ Monitoring window elapsed without all fills.")
    return 0


def main():
    api_key, api_secret = get_env_api()
    if not api_key or not api_secret:
        print(
            "❌ Missing API env vars. Set BINANCEUS_API_KEY & BINANCEUS_API_SECRET or BINANCEUS_KEY & BINANCE_API_SECRET (or BINANCEUS_SECRET)"
        )
        return 1

    ex = ccxt.binanceus(
        {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "timeout": 30000,
            "options": {"defaultType": "spot"},
        }
    )

    try:
        markets = ex.load_markets()
    except Exception as e:
        print(f"❌ Failed to load markets: {e}")
        return 1

    adapter = BinanceUSAdapter(ex) if BinanceUSAdapter else None

    # Balances first
    free_usdt, free_usd = get_free_balances(ex)

    # Choose pair based on balances
    xrp_symbol = choose_best_xrp_symbol(ex, free_usdt, free_usd)
    if not xrp_symbol:
        print("❌ XRP/USD or XRP/USDT not available on this account/exchange")
        return 1

    try:
        ticker = ex.fetch_ticker(xrp_symbol)
        price = float(ticker["last"]) if ticker.get("last") else None
        if not price or price <= 0:
            print("❌ Could not fetch current XRP price")
            return 1
    except Exception as e:
        print(f"❌ Failed to fetch XRP ticker: {e}")
        return 1

    # Momentum/vol
    momentum, vol = fetch_momentum(ex, xrp_symbol)
    strong = momentum >= STRONG_MOM_THRESHOLD

    tp1_pct = BASE_TP1_PCT
    tp2_pct = TP2_STRONG if strong else TP2_WEAK
    split = TP_SPLIT_STRONG if strong else TP_SPLIT_WEAK

    quote_ccy = xrp_symbol.split("/")[1]
    free_quote = free_usdt if quote_ccy == "USDT" else free_usd

    # Auto-convert USD->USDT if needed and only USDT pair was chosen
    if quote_ccy == "USDT" and free_quote < 10 and free_usd >= 10:
        converted = convert_usd_to_usdt_if_needed(
            ex, needed_usdt=ALLOC_CAP_USD, free_usdt=free_usdt, free_usd=free_usd
        )
        if converted > 0:
            # refresh balances
            time.sleep(0.5)
            free_usdt, free_usd = get_free_balances(ex)
            free_quote = free_usdt

    if not free_quote or free_quote < 10:
        print(
            f"❌ Not enough free {quote_ccy} to trade (have: {free_quote:.2f}, USD free: {free_usd:.2f}, USDT free: {free_usdt:.2f})."
        )
        print(
            "ℹ️ If funds are in open orders, cancel them or wait. If funds are in USD, script will auto-convert when using XRP/USDT."
        )
        return 1

    budget = min(free_quote * ALLOC_FRACTION, ALLOC_CAP_USD)
    if budget < 10:
        print(f"❌ Allocation below minimum notional: ${budget:.2f}")
        return 1

    market = ex.market(xrp_symbol)
    amount_step = None
    min_cost = None
    try:
        # amount step from filters
        for flt in market.get("info", {}).get("filters", []):
            if flt.get("filterType") == "LOT_SIZE":
                step_size = float(flt.get("stepSize"))
                amount_step = step_size if step_size > 0 else amount_step
            if flt.get("filterType") == "MIN_NOTIONAL":
                min_cost = float(flt.get("minNotional"))
    except Exception:
        pass

    # Compute amount
    raw_amount = budget / price
    amount = (
        amount_to_step(raw_amount, amount_step)
        if isinstance(amount_step, float) and amount_step > 0
        else raw_amount
    )
    # Fallback to decimals precision
    if amount == raw_amount:
        prec = market.get("precision", {}).get("amount")
        amount = round_to_precision(raw_amount, prec)

    cost = amount * price
    if min_cost and cost < min_cost:
        target_amount = min_cost / price
        if target_amount * price <= free_quote:
            amount = target_amount
            cost = amount * price

    if amount <= 0 or cost < 10:
        print("❌ Computed trade size too small after precision/min-notional checks")
        return 1

    print("🚀 Preparing purchase:")
    print(f"   Pair: {xrp_symbol}")
    print(f"   Price: ${price:.4f}")
    print(f"   Budget: {quote_ccy} {budget:.2f}")
    print(f"   Momentum(≈15m): {momentum*100:.2f}% | Vol(1m stdev): {vol*100:.2f}%")
    print(f"   Amount: {amount} XRP (cost ~ {quote_ccy} {cost:.2f})")

    # Execute market buy
    try:
        if adapter:
            order = adapter.guarded_create_order(xrp_symbol, "market", "buy", amount)
        else:
            order = ex.create_order(xrp_symbol, "market", "buy", amount)
        if order is None:
            print("🧪 Paper mode: skipped market buy")
        else:
            print(f"✅ Market buy placed. Order id: {order.get('id')}")
    except Exception as e:
        print(f"❌ Buy order failed: {e}")
        return 1

    # Build TP targets and split amounts
    amt_tp1 = amount * split[0]
    amt_tp2 = max(0.0, amount - amt_tp1)

    # Round to step
    if isinstance(amount_step, float) and amount_step > 0:
        amt_tp1 = amount_to_step(amt_tp1, amount_step)
        amt_tp2 = amount_to_step(amt_tp2, amount_step)
        # ensure total not exceeding bought amount due to rounding
        if amt_tp1 + amt_tp2 > amount:
            amt_tp2 = amount_to_step(amount - amt_tp1, amount_step)

    # Compute prices (rounded to price precision if provided)
    pprec = market.get("precision", {}).get("price")
    tp1_price = round_to_precision(price * (1.0 + tp1_pct), pprec)
    tp2_price = round_to_precision(price * (1.0 + tp2_pct), pprec)

    sell_order_ids = []

    # Place limit sell TP1
    if amt_tp1 > 0:
        try:
            if adapter:
                sell1 = adapter.guarded_create_order(
                    xrp_symbol, "limit", "sell", amt_tp1, tp1_price
                )
            else:
                sell1 = ex.create_order(xrp_symbol, "limit", "sell", amt_tp1, tp1_price)
            if sell1 is None:
                print("🧪 Paper mode: skipped TP1 placement")
            else:
                print(
                    f"✅ TP1 placed: {amt_tp1} @ ${tp1_price:.4f} (+{tp1_pct*100:.1f}%) id={sell1.get('id')}"
                )
                sell_order_ids.append(sell1.get("id"))
        except Exception as e:
            print(f"⚠️ Failed to place TP1: {e}")
    # Place limit sell TP2
    if amt_tp2 > 0:
        try:
            if adapter:
                sell2 = adapter.guarded_create_order(
                    xrp_symbol, "limit", "sell", amt_tp2, tp2_price
                )
            else:
                sell2 = ex.create_order(xrp_symbol, "limit", "sell", amt_tp2, tp2_price)
            if sell2 is None:
                print("🧪 Paper mode: skipped TP2 placement")
            else:
                print(
                    f"✅ TP2 placed: {amt_tp2} @ ${tp2_price:.4f} (+{tp2_pct*100:.1f}%) id={sell2.get('id')}"
                )
                sell_order_ids.append(sell2.get("id"))
        except Exception as e:
            print(f"⚠️ Failed to place TP2: {e}")

    # Save state for banking monitor
    state = {
        "symbol": xrp_symbol,
        "buy_price": price,
        "amount": amount,
        "tp1_pct": tp1_pct,
        "tp2_pct": tp2_pct,
        "sell_order_ids": sell_order_ids,
        "buy_order_id": order.get("id") if order else None,
        "timestamp": datetime.now().isoformat(),
        "quote_ccy": quote_ccy,
        "banked_flags": {},
    }
    with open("quick_xrp_allocation_state.json", "w") as f:
        json.dump(state, f, indent=2)

    print("📄 State saved to quick_xrp_allocation_state.json")
    print("🏁 Allocation complete. Monitor open orders for fills and banking.")
    return 0


if __name__ == "__main__":
    # Modes:
    #   no args -> place buy and adaptive TP sells, then exit
    #   monitor  -> monitor existing state and bank profit on each fill
    #   auto     -> place buy+TPs then monitor and bank
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if mode == "monitor":
        raise SystemExit(monitor_and_bank())
    elif mode == "auto":
        rc = main()
        if rc == 0:
            time.sleep(3)
            raise SystemExit(monitor_and_bank())
        raise SystemExit(rc)
    else:
        raise SystemExit(main())
