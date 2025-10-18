#!/usr/bin/env python3
import os
import json
from typing import Any, Dict, List, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Governance / ledger helpers
from governance import prompt_version as pv

# Exchange adapter for market metadata
from libs.exchange_adapters.binance_us import get_client


def load_env():
    env_file = os.getenv("ENV", ".env.live")
    if os.path.exists(env_file):
        load_dotenv(env_file)
    # honor LEDGER_PATH override
    lp = os.getenv("LEDGER_PATH")
    if lp:
        pv.LEDGER_PATH = lp


def read_jsonl(path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
    except FileNotFoundError:
        return []
    if limit:
        return rows[-limit:]
    return rows


def read_json(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def compute_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    trades_open = [r for r in rows if r.get("event") == "trade_open"]
    trades_close = [r for r in rows if r.get("event") == "trade_close"]
    iso_banks = [r for r in rows if r.get("event") == "iso_bank"]
    pauses = [r for r in rows if r.get("event") == "AUTO_PAUSE"]
    order_failed = [
        r for r in rows if r.get("event") in ("ORDER_FAILED", "WITHDRAW_FAILED")
    ]
    lockdown_blocks = [r for r in rows if r.get("event") == "LOCKDOWN_BLOCK"]

    pnl_usd = 0.0
    for r in trades_close:
        try:
            entry = float(r.get("entry_price", 0))
            exitp = float(r.get("exit_price", 0))
            amt = float(r.get("amount", 0))
            pnl_usd += (exitp - entry) * amt
        except Exception:
            pass
    iso_total = sum(float(x.get("bank_usd", 0) or 0) for x in iso_banks)

    return {
        "opens": len(trades_open),
        "closes": len(trades_close),
        "order_errors": len(order_failed),
        "lockdown_blocks": len(lockdown_blocks),
        "pnl_usd": round(pnl_usd, 6),
        "iso_bank_usd": round(iso_total, 6),
        "last_pause_reason": (pauses[-1].get("reason") if pauses else None),
    }


def get_open_positions(state_path: str) -> List[Dict[str, Any]]:
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("positions", [])
    except Exception:
        return []


def build_iso_map() -> Dict[str, Optional[str]]:
    # Determine availability of ISO_COINS on preferred quotes
    coins = [
        s.strip().upper()
        for s in os.getenv("ISO_COINS", "XRP,XLM,XDC,ALGO,IOTA,HBAR,QNT").split(",")
        if s.strip()
    ]
    quotes = [
        s.strip().upper()
        for s in os.getenv("QUOTE_PREFS", "USDT,USD,USDC").split(",")
        if s.strip()
    ]
    symmap: Dict[str, Optional[str]] = {}
    try:
        client = get_client(os.getenv("MODE", "paper"))
        mkts = client.load_markets() or {}
    except Exception:
        mkts = {}
    for c in coins:
        symmap[c] = None
        for q in quotes:
            s = f"{c}/{q}"
            if s in mkts:
                symmap[c] = s
                break
    return symmap


def main():
    load_env()
    st.set_page_config(page_title="Trillion Momentum Dashboard", layout="wide")

    mode = os.getenv("MODE", "paper")
    exchange = os.getenv("EXCHANGE", "binanceus")
    state_path = os.getenv("STATE_PATH", "runtime/state/state.json")
    ledger_path = pv.LEDGER_PATH
    pause_file = os.getenv("PAUSE_FILE", "runtime/PAUSE")
    exports_dir = os.getenv("EXPORTS_DIR", "runtime/exports")

    ph, gc = pv.current_version()

    st.title("Trillion Bot Momentum — Stewardship Dashboard")
    col1, col2, col3, col4 = st.columns([1, 1, 2, 2])
    with col1:
        st.metric("Mode", mode)
        st.metric("Exchange", exchange)
    with col2:
        st.metric("Prompt Hash", ph[:8] if isinstance(ph, str) else ph)
        st.metric("Git Commit", (gc or "")[:7])
    with col3:
        st.write("Ledger Path:", f"`{ledger_path}`")
        st.write("State Path:", f"`{state_path}`")
    with col4:
        st.write("Approval Required:", os.getenv("REQUIRE_APPROVALS", "true"))
        st.write("Pause File:", "present" if os.path.exists(pause_file) else "absent")

    rows = read_jsonl(ledger_path)
    metrics = compute_metrics(rows)

    st.subheader("Key Metrics")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Opens", metrics["opens"])
    m2.metric("Closes", metrics["closes"])
    m3.metric("Order Errors", metrics["order_errors"])
    m4.metric("Lockdown Blocks", metrics["lockdown_blocks"])
    m5.metric("PnL (USD)", metrics["pnl_usd"])
    m6.metric("ISO Banked (USD)", metrics["iso_bank_usd"])

    if metrics.get("last_pause_reason"):
        st.warning(f"AUTO-PAUSE active: {metrics['last_pause_reason']}")

    st.subheader("Open Positions")
    pos = get_open_positions(state_path)
    if pos:
        st.dataframe(pd.DataFrame(pos))
    else:
        st.write("No open positions.")

    st.subheader("ISO Banking Map (Available Pairs)")
    iso_map = build_iso_map()
    iso_df = pd.DataFrame([{"coin": k, "symbol": v} for k, v in iso_map.items()])
    st.dataframe(iso_df)

    # --- ISO Reserves (Vault Feed) ---
    st.subheader("ISO Reserves (Vault Feed)")
    reserves_path = os.path.join(exports_dir, "iso_reserves.json")
    reserves = read_json(reserves_path)
    if reserves:
        r1, r2 = st.columns(2)
        with r1:
            st.metric("Total ISO Reserves (USD)", f"{reserves.get('total_est_usd', 0)}")
        with r2:
            st.metric("As Of", reserves.get("as_of", "-"))
        entries = reserves.get("iso_reserves") or []
        if isinstance(entries, list) and entries:
            # Normalize to dataframe with asset, amount, est_usd
            try:
                df = pd.DataFrame(entries)
                st.dataframe(df)
            except Exception:
                st.write(entries)
        else:
            st.info("No ISO reserve entries yet.")
        st.caption(f"Source: {reserves_path}")
    else:
        st.info(
            "No ISO reserves snapshot found yet. It will appear after profitable closes or periodic exports."
        )

    st.subheader("Recent Ledger Events (last 200)")
    recent = rows[-200:]
    if recent:
        st.dataframe(pd.json_normalize(recent))
    else:
        st.write("No ledger entries yet.")

    st.caption("Refresh the page to update, or enable auto-refresh below.")
    with st.expander("Auto-refresh"):
        interval = st.slider("Seconds", 5, 60, 15)
        st.experimental_rerun  # no-op to keep static analyzers happy
        st_autoref = st.checkbox("Enable auto-refresh", value=False)
        if st_autoref:
            st.experimental_set_query_params(auto="1")
            st.experimental_rerun()


if __name__ == "__main__":
    main()
