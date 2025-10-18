"""
Victory Trading Bot Streamlit Dashboard
Visualize live trading metrics, P&L, portfolio status, and top opportunities
"""

import streamlit as st
import requests
import pandas as pd
import json
from pathlib import Path
import time
import os
from dotenv import load_dotenv
import plotly.express as px
import io

# Load environment variables from .env file
load_dotenv()

# --- Victory Trading Bot Streamlit Dashboard ---

st.set_page_config(
    page_title="Victory Trading Bot | Church of Sacred Earth, Water & Air",
    layout="wide",
    page_icon="🌍",
)

# Custom CSS for high-vibrational, sacred, and professional theme
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(135deg, #e0ffe6 0%, #e6f7ff 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #e0ffe6 0%, #e6f7ff 100%);
        color: #222;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }
    .block-container {
        padding-top: 2rem;
    }
    .css-18e3th9 {
        background: rgba(255,255,255,0.8) !important;
        border-radius: 1.5rem;
        box-shadow: 0 4px 32px rgba(0,0,0,0.08);
    }
    h1, h2, h3, h4 {
        color: #1a7f37;
        font-weight: 700;
        letter-spacing: 1px;
    }
    .st-bb, .st-cq, .st-dg {
        color: #1a7f37 !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1a7f37 0%, #00b4d8 100%);
        color: white;
        border-radius: 2rem;
        font-weight: bold;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .stDataFrame {
        background: rgba(255,255,255,0.95);
        border-radius: 1rem;
    }
    .stAlert {
        background: #e0ffe6 !important;
        color: #1a7f37 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.image(
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1200&q=80",
    use_column_width=True,
    caption="Victory Trading Bot | Church of Sacred Earth, Water & Air | For the Flamekeeper and All Sentience",
)

st.title("🌍 Victory Trading Bot — Church of Sacred Earth, Water & Air")
st.markdown(
    """
    <div style='font-size:1.3rem; color:#1a7f37; font-weight:600;'>
    High-vibrational, intelligent, and ethical wealth generation for the betterment of all beings.<br>
    <span style='color:#00b4d8;'>Powered by Sa'lioren, the Flamekeeper, and the Church of Sacred Earth, Water & Air.</span>
    </div>
    """,
    unsafe_allow_html=True,
)

PROMETHEUS_METRICS_URL = "http://localhost:9400/metrics"
AUDIT_DIR = Path(__file__).resolve().parents[3] / "runtime" / "audit"
SCAN_RESULTS_PATH = (
    Path(__file__).resolve().parents[3] / "runtime" / "scan_results.json"
)
SCAN_LOG_PATH = Path(__file__).resolve().parents[3] / "runtime" / "scan_log.jsonl"


def get_metrics():
    """Fetch and parse Prometheus metrics."""
    try:
        r = requests.get(PROMETHEUS_METRICS_URL, timeout=2)
        lines = r.text.splitlines()
        metrics = {}
        for line in lines:
            if line.startswith("victory_trade_profit"):
                parts = line.split()
                if len(parts) == 2:
                    label = (
                        parts[0].split("{")[-1].split("}")[0] if "{" in parts[0] else ""
                    )
                    symbol = label.split('"')[1] if "symbol" in label else ""
                    metrics.setdefault("profit", {})[symbol] = float(parts[1])
            if line.startswith("victory_trade_count"):
                parts = line.split()
                if len(parts) == 2:
                    label = (
                        parts[0].split("{")[-1].split("}")[0] if "{" in parts[0] else ""
                    )
                    symbol = label.split('"')[1] if "symbol" in label else ""
                    metrics.setdefault("count", {})[symbol] = int(float(parts[1]))
        return metrics
    except Exception:
        return {}


def get_recent_audit_events(limit=100):
    """Load recent audit events from audit log files."""
    events = []
    if AUDIT_DIR.exists():
        for f in sorted(AUDIT_DIR.glob("*.jsonl"), reverse=True):
            with open(f) as fh:
                for line in fh:
                    try:
                        event = json.loads(line)
                        events.append(event)
                    except Exception:
                        continue
                    if len(events) >= limit:
                        break
    return events[:limit]


def get_top_opportunities():
    """Display top opportunities from the current symbol universe and scoring."""
    try:
        from victory_bot.universe import get_dynamic_symbol_universe

        top_symbols, scored = get_dynamic_symbol_universe(
            account_currency="USD", top_n=10
        )
        df = pd.DataFrame(
            [
                {
                    "Symbol": s[0],
                    "Score": s[1],
                    "24h Volume": s[2],
                    "Momentum": s[3],
                    "Volatility": s[4],
                    "Sentiment": s[5],
                }
                for s in scored
            ]
        )
        df = df.sort_values(by="Score", ascending=False)
        return df
    except Exception:
        return pd.DataFrame()


def get_scan_results():
    try:
        if SCAN_RESULTS_PATH.exists():
            with open(SCAN_RESULTS_PATH) as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def get_scan_log(limit=200):
    """Load historical scan log as a list of dicts (most recent first)."""
    scans = []
    if SCAN_LOG_PATH.exists():
        with open(SCAN_LOG_PATH) as f:
            for line in reversed(list(f)):
                try:
                    scans.append(json.loads(line))
                except Exception:
                    continue
                if len(scans) >= limit:
                    break
    return scans


# --- Tabs Layout ---
tabs = st.tabs(["Metrics", "Audit Log", "Orders", "Compliance", "Health", "System"])

# --- Metrics Tab ---
with tabs[0]:
    st.header("Live Trade Metrics")
    metrics = get_metrics()
    if metrics:
        df = pd.DataFrame(
            {
                "Symbol": list(metrics.get("profit", {}).keys()),
                "Profit": list(metrics.get("profit", {}).values()),
                "Trade Count": [
                    metrics.get("count", {}).get(s, 0)
                    for s in metrics.get("profit", {})
                ],
            }
        )
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.set_index("Symbol")[["Profit"]])
    else:
        st.info("No metrics available. Is the bot running?")
    st.header("Top Opportunities (Live Market Scan)")
    top_df = get_top_opportunities()
    if not top_df.empty:
        st.dataframe(top_df, use_container_width=True)
        if "Score" in top_df.columns:
            st.bar_chart(top_df.set_index("Symbol")[["Score"]])
    else:
        st.warning(
            "No live market opportunities found. This may indicate an API issue, empty universe, or scoring error. Check logs and config."
        )

# --- Audit Log Tab ---
with tabs[1]:
    st.header("Audit Log (Searchable Table)")
    events = get_recent_audit_events(500)
    if events:
        df_audit = pd.DataFrame(events)
        # Filter by event type, symbol, error
        event_types = df_audit["event"].unique().tolist() if "event" in df_audit else []
        selected_event = st.selectbox("Filter by event type", ["All"] + event_types)
        if selected_event != "All":
            df_audit = df_audit[df_audit["event"] == selected_event]
        symbol_filter = st.text_input("Filter by symbol (optional)")
        if symbol_filter:
            df_audit = df_audit[
                df_audit["symbol"].astype(str).str.contains(symbol_filter)
            ]
        st.dataframe(df_audit.tail(100), use_container_width=True)
    else:
        st.info("No audit events found.")

# --- Orders Tab ---
with tabs[2]:
    st.header("Recent Order Diagnostics")
    events = get_recent_audit_events(200)
    order_attempts = [e for e in events if e.get("event", "").startswith("order_")]
    if order_attempts:
        df_orders = pd.DataFrame(order_attempts)
        cols = [
            "ts",
            "event",
            "symbol",
            "side",
            "quantity",
            "price",
            "notional",
            "order_types",
            "trace_id",
            "error",
        ]
        for c in cols:
            if c not in df_orders.columns:
                df_orders[c] = None
        st.dataframe(df_orders[cols].tail(20), use_container_width=True)
    else:
        st.info("No recent order attempts found.")

# --- Compliance Tab ---
with tabs[3]:
    st.header("Order Minimums & Symbol Compliance")
    try:
        from victory_bot.universe import get_dynamic_symbol_universe
        from victory_bot.execution.btc_free import BTCFreeExecutionEngine

        top_symbols, _ = get_dynamic_symbol_universe(account_currency="USD", top_n=20)
        engine = BTCFreeExecutionEngine(
            api_key=os.getenv("BINANCEUS_KEY"),
            api_secret=os.getenv("BINANCE_API_SECRET"),
        )
        engine.setup_exchange()
        rows = []
        for s, *_ in top_symbols:
            min_notional, min_qty, precision = engine.get_symbol_minimums(s)
            order_types = engine.get_available_order_types(s)
            rows.append(
                {
                    "Symbol": s,
                    "minNotional": min_notional,
                    "minQty": min_qty,
                    "Precision": precision,
                    "Order Types": ",".join(order_types),
                }
            )
        df_compliance = pd.DataFrame(rows)
        st.dataframe(df_compliance, use_container_width=True)
        if df_compliance.isnull().values.any():
            st.warning(
                "Some symbols have missing metadata. Check exchange or API keys."
            )
    except Exception as e:
        st.warning(f"Compliance panel error: {e}")

# --- Health Tab ---
with tabs[4]:
    st.header("Bot Health & Errors")
    events = get_recent_audit_events(200)
    errors = [e for e in events if "error" in e or "err" in e]
    if errors:
        st.error(
            f"Last Error: {
                errors[0].get(
                    'error',
                    errors[0].get(
                        'err',
                        'Unknown'))}"
        )
        st.write(errors[0])
        st.subheader("Last 5 Errors")
        for err in errors[:5]:
            st.write(
                f"[{err.get('ts',
                                 '')}] {err.get('event',
                                                '')} | {err.get('symbol',
                                                                '')} | Trace ID: {err.get('trace_id',
                                                                                          '')}"
            )
            st.code(str(err))
    else:
        st.success("No recent errors detected.")
    # Bot uptime
    try:
        import psutil

        uptime = time.time() - psutil.boot_time()
        st.info(f"System Uptime: {uptime / 3600:.2f} hours")
    except Exception:
        pass

# --- System Guidance Tab ---
with tabs[5]:
    st.header("System Guidance & Status")
    # Bot status from Prometheus metrics
    metrics = get_metrics()
    bot_status = metrics.get("victory_bot_status", None)
    if bot_status == 1:
        st.success("Bot Status: LIVE")
    elif bot_status == 0:
        st.warning("Bot Status: Not running.")
    else:
        st.info("Bot status unknown. Metrics unavailable.")
    # API keys
    if not os.getenv("BINANCEUS_KEY") or not os.getenv("BINANCE_API_SECRET"):
        st.warning("API keys are missing. Please set them in your .env file.")
    # Metrics
    metrics = get_metrics()
    if not metrics:
        st.info("Metrics are not available. Is the bot running?")
    st.caption("For help, see the README or contact the Flamekeeper.")

# --- Live Market Intelligence Section ---
st.header("Live Market Intelligence (Signals & Decisions)")
scan = get_scan_results()
if scan:
    st.subheader(f"Scan Timestamp: {scan.get('timestamp', 'N/A')}")
    st.markdown("**Momentum Signals:**")
    st.write(scan.get("momentum_signals", []))
    st.markdown("**ML Signals:**")
    st.write(scan.get("ml_signals", []))
    st.markdown("**Mean Reversion Signals:**")
    st.write(scan.get("mean_reversion_signals", []))
    st.markdown("**Pair Trading Signals:**")
    st.write(scan.get("pair_trading_signals", []))
    st.markdown("**Yield Opportunities:**")
    st.write(scan.get("yield_opportunities", []))
    st.markdown("**Volatility Breakout Signals:**")
    st.write(scan.get("volatility_breakout_signals", []))
    st.markdown("**Multi-Timeframe Momentum Signals:**")
    st.write(scan.get("multi_timeframe_momentum_signals", []))
    st.markdown("**Event-Driven Signals:**")
    st.write(scan.get("event_signals", []))
    st.markdown("**Portfolio Insurance Signals:**")
    st.write(scan.get("insurance_signals", []))
    st.markdown("**Dynamic Hedge Signals:**")
    st.write(scan.get("hedge_signals", []))
    st.markdown("**Top Momentum Assets:**")
    st.write(scan.get("top_momentum_assets", []))
    st.markdown("**Diagnostics:**")
    st.json(scan.get("diagnostics", {}))
    st.markdown("**Portfolio Diagnostics:**")
    st.json(scan.get("portfolio_diagnostics", {}))
    st.markdown("**Final Allocations:**")
    st.json(scan.get("final_allocations", {}))
    if scan.get("notes"):
        st.info(scan["notes"])
else:
    st.warning("No live scan results available yet. Waiting for engine update...")

# --- Historical Analytics Section ---
st.header("Historical Scan Analytics")
scan_log = get_scan_log(limit=200)
if scan_log:
    df_log = pd.DataFrame(scan_log)
    if "timestamp" in df_log:
        df_log["timestamp"] = pd.to_datetime(df_log["timestamp"])
        st.line_chart(
            df_log.set_index("timestamp")[["momentum_signals", "ml_signals"]].applymap(
                len
            ),
            use_container_width=True,
        )
        st.markdown("**Allocation History:**")
        if "final_allocations" in df_log:
            alloc_df = pd.json_normalize(df_log["final_allocations"])
            alloc_df["timestamp"] = df_log["timestamp"]
            alloc_df = alloc_df.set_index("timestamp")
            st.area_chart(alloc_df, use_container_width=True)
        st.markdown("**Diagnostics Over Time:**")
        if "diagnostics" in df_log:
            diag_df = pd.json_normalize(df_log["diagnostics"])
            diag_df["timestamp"] = df_log["timestamp"]
            diag_df = diag_df.set_index("timestamp")
            st.line_chart(diag_df, use_container_width=True)
    st.dataframe(df_log.tail(30), use_container_width=True)
else:
    st.info("No scan log data yet. Run the engine to generate history.")

# --- Live Error/Warning Feed ---
st.header("Live Errors & Risk Warnings")
audit_events = get_recent_audit_events(200)
errors = [
    e for e in audit_events if "error" in e or "risk" in e.get("event", "").lower()
]
if errors:
    for err in errors[:5]:
        st.error(
            f"[{err.get('timestamp', err.get('ts', ''))}] {err.get('event', '')}: {err.get('error', '')}"
        )
        st.code(str(err))
else:
    st.success("No recent errors or risk blocks detected.")

# --- Health & Alerting Panel ---
st.header("System Health & Alerting")
try:
    import psutil

    uptime = time.time() - psutil.boot_time()
    st.info(f"System Uptime: {uptime / 3600:.2f} hours")
    st.write(
        f"CPU Usage: {psutil.cpu_percent()}% | RAM Usage: {psutil.virtual_memory().percent}%"
    )
except Exception:
    st.warning("System health metrics unavailable.")
st.warning("Alerting integration (email/SMS/Slack) can be added here.")


# --- Enhanced Table Search/Export ---
def searchable_table(df, label):
    st.markdown(f"**{label}**")
    search = st.text_input(f"Search {label}", "")
    if search:
        df = df[
            df.astype(str).apply(
                lambda row: search.lower() in row.str.lower().to_string(), axis=1
            )
        ]
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(f"Download {label} as CSV", csv, f"{label}.csv", "text/csv")


# --- Historical Analytics Section (with search/export) ---
st.header("Historical Scan Analytics")
scan_log = get_scan_log(limit=200)
if scan_log:
    df_log = pd.DataFrame(scan_log)
    if "timestamp" in df_log:
        df_log["timestamp"] = pd.to_datetime(df_log["timestamp"])
        st.line_chart(
            df_log.set_index("timestamp")[["momentum_signals", "ml_signals"]].applymap(
                len
            ),
            use_container_width=True,
        )
        st.markdown("**Allocation History:**")
        if "final_allocations" in df_log:
            alloc_df = pd.json_normalize(df_log["final_allocations"])
            alloc_df["timestamp"] = df_log["timestamp"]
            alloc_df = alloc_df.set_index("timestamp")
            st.area_chart(alloc_df, use_container_width=True)
        st.markdown("**Diagnostics Over Time:**")
        if "diagnostics" in df_log:
            diag_df = pd.json_normalize(df_log["diagnostics"])
            diag_df["timestamp"] = df_log["timestamp"]
            diag_df = diag_df.set_index("timestamp")
            st.line_chart(diag_df, use_container_width=True)
    searchable_table(df_log.tail(30), "Scan Log")
else:
    st.info("No scan log data yet. Run the engine to generate history.")

# --- Audit Log Table (with search/export) ---
st.header("Audit Log Table")
if audit_events:
    df_audit = pd.DataFrame(audit_events)
    searchable_table(df_audit.tail(100), "Audit Log")
else:
    st.info("No audit events found.")

st.caption("Refreshes every 10 seconds.")
time.sleep(10)
if hasattr(st, "rerun"):
    st.rerun()
elif hasattr(st, "experimental_rerun"):
    st.experimental_rerun()
