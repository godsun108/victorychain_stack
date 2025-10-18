#!/usr/bin/env python3
# Momentum Bot (clean rebuilt version with profitability infrastructure):
# - Audit ledger (hash chained)
# - Prometheus metrics (fallback exporter)
# - Risk limits (daily loss, drawdown, gross exposure, VaR hooks)
# - Treasury banking
# - Claude AI 592 dynamic universe + strategy parameter overrides
# - Loss streak cooldown & approval token freshness gate
# - Adaptive risk multiplier (draws down sizing after clustered losses, recovers slowly)
# - Circuit breaker for repeated exchange errors
# - Expected edge tagging per trade
from __future__ import annotations
import os, json, time, threading, signal, logging, hashlib, subprocess, socket
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# ---------------- Basic Setup ----------------
try:
    import ccxt  # type: ignore
except Exception:  # pragma: no cover
    ccxt = None

try:
    UTC = datetime.UTC
except AttributeError:  # pragma: no cover
    UTC = timezone.utc


def now_utc():
    return datetime.now(UTC)


MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")
BOT_ID = os.getenv("BOT_ID", "default")

# ---------------- Claude Integration ----------------
try:
    from claude_ai_592_token_library import bootstrap_claude_analysis  # type: ignore

    _CLAUDE_ENABLED = True
except Exception:
    bootstrap_claude_analysis = None  # type: ignore
    _CLAUDE_ENABLED = False
_CLAUDE_REF = None
_last_claude_update = 0.0
_CLAUDE_UNIVERSE_REFRESH_SEC = float(os.getenv("CLAUDE_UNIVERSE_REFRESH_SEC", "300"))
_CLAUDE_MIN_CONF = float(os.getenv("CLAUDE_MIN_CONF", "0.60"))
# Strategy specific overrides
_STRATEGY_PROFILES = {
    "momentum_breakout": {
        "LOOKBACK_BREAKOUT": 40,
        "TRAILING_STOP_BPS": 300,
        "MIN_PROFIT_EXIT_BPS": 50,
    },
    "mean_revert": {
        "LOOKBACK_BREAKOUT": 20,
        "TRAILING_STOP_BPS": 180,
        "MIN_PROFIT_EXIT_BPS": 30,
    },
    "volatility_capture": {
        "LOOKBACK_BREAKOUT": 55,
        "TRAILING_STOP_BPS": 450,
        "MIN_PROFIT_EXIT_BPS": 80,
    },
    "range_play": {
        "LOOKBACK_BREAKOUT": 30,
        "TRAILING_STOP_BPS": 250,
        "MIN_PROFIT_EXIT_BPS": 40,
    },
}
_SYMBOL_STRATEGY: Dict[str, str] = {}

# ---------------- Loss Streak / Approval Token ----------------
LOSS_STREAK_THRESHOLD = int(os.getenv("LOSS_STREAK_THRESHOLD", "3") or 3)
LOSS_STREAK_COOLDOWN_SEC = int(os.getenv("LOSS_STREAK_COOLDOWN_SEC", "1800") or 1800)
LOSS_STREAK_COUNT = 0
LOSS_STREAK_PAUSE_UNTIL = 0.0
APPROVAL_TOKEN_PATH = os.getenv("APPROVAL_TOKEN_PATH", "runtime/APPROVAL_TOKEN.txt")
MAX_TOKEN_AGE_SEC = int(os.getenv("MAX_TOKEN_AGE_SEC", "7200") or 7200)
_APPROVAL_STALE = False
_last_token_check = 0.0
_TOKEN_CHECK_INTERVAL = 60.0

# ---------------- Live Addons (optional) ----------------
try:  # pragma: no cover
    from momentum.addons_live import PriceCache, WSClient, RiskManager  # type: ignore

    try:
        from momentum.addons_live import VAR95_SYM_USD, VAR95_CONTRIB_USD  # type: ignore
    except Exception:
        VAR95_SYM_USD = VAR95_CONTRIB_USD = None  # type: ignore
except Exception:
    PriceCache = WSClient = RiskManager = None  # type: ignore
    VAR95_SYM_USD = VAR95_CONTRIB_USD = None  # type: ignore
price_cache = None  # type: ignore
ws_client = None  # type: ignore
risk_mgr = None  # type: ignore

# ---------------- Env / Versioning ----------------
from dotenv import load_dotenv

try:  # pragma: no cover
    from momentum.prompt_versioning import pv  # type: ignore
except Exception:  # minimal fallback

    class _PV:
        LEDGER_PATH = "runtime/ledger/live_ledger.jsonl"

        def compute_prompt_hash(self):
            try:
                with open(__file__, "rb") as f:
                    return hashlib.sha256(f.read()).hexdigest()[:16]
            except Exception:
                return "na"

        def get_git_commit(self):
            try:
                return (
                    subprocess.check_output(
                        ["git", "rev-parse", "--short", "HEAD"],
                        stderr=subprocess.DEVNULL,
                    )
                    .decode()
                    .strip()
                )
            except Exception:
                return "unknown"

    pv = _PV()  # type: ignore

ENV_FILE = os.getenv("ENV", ".env.live")
if os.path.exists(ENV_FILE):
    load_dotenv(ENV_FILE)
else:
    alt = os.path.join(os.path.dirname(__file__), ENV_FILE)
    if os.path.exists(alt):
        load_dotenv(alt)
    else:
        logging.warning("ENV file %s not found", ENV_FILE)

# ---------------- Metrics Setup ----------------
_prom_ok = False
try:
    from prometheus_client import start_http_server, Gauge, Counter, Histogram  # type: ignore

    _prom_ok = True
except Exception:
    Gauge = Counter = Histogram = None  # type: ignore

METRICS_PORT = int(os.getenv("METRICS_PORT", "9108"))
if _prom_ok:
    # start exporter if port unused
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        if s.connect_ex(("127.0.0.1", METRICS_PORT)) != 0:
            start_http_server(METRICS_PORT)
            logging.info("metrics_exporter_started port=%s", METRICS_PORT)
        s.close()
    except Exception:  # pragma: no cover
        pass


class _Dummy:
    def labels(self, *a, **k):
        return self

    def set(self, *_):
        pass

    def inc(self, *_):
        pass

    def observe(self, *_):
        pass


if _prom_ok:
    METRIC_DAILY_REAL = Gauge(
        "momentum_daily_realized_pnl_usd", "Realized PnL today", ["bot_id"]
    )
    METRIC_DD_PCT = Gauge(
        "momentum_intraday_drawdown_pct", "Realized drawdown pct", ["bot_id"]
    )
    METRIC_RISK_BLOCK = Gauge(
        "momentum_risk_blocking", "Risk gate active", ["bot_id", "reason"]
    )
    METRIC_REJECTS = Counter(
        "momentum_order_rejects_total", "Order rejects", ["bot_id", "reason"]
    )
    METRIC_SLIPPAGE = Histogram(
        "momentum_slippage_bps",
        "Slippage bps",
        [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000],
    )
    METRIC_HEARTBEAT = Gauge("momentum_heartbeat_ts", "Heartbeat ts", ["bot_id"])
    METRIC_TREASURY_BUFFER = Gauge(
        "momentum_realized_pnl_buffer_usd", "PnL buffer", ["bot_id"]
    )
    METRIC_TREASURY_RESERVE_VAL = Gauge(
        "momentum_reserve_value_usd", "Reserve USD", ["bot_id", "reserve"]
    )
    METRIC_TREASURY_LAST_TS = Gauge(
        "momentum_treasury_last_bank_ts", "Last bank ts", ["bot_id"]
    )
    METRIC_TREASURY_EVENTS = Counter(
        "momentum_treasury_bank_events_total", "Bank events", ["bot_id"]
    )
    METRIC_GROSS_EXPOSURE = Gauge(
        "momentum_gross_exposure_usd", "Gross exposure", ["bot_id"]
    )
    METRIC_ADAPTIVE_RISK_MULT = Gauge(
        "momentum_adaptive_risk_multiplier", "Adaptive multiplier", ["bot_id"]
    )
else:
    METRIC_DAILY_REAL = METRIC_DD_PCT = METRIC_RISK_BLOCK = METRIC_REJECTS = (
        METRIC_SLIPPAGE
    ) = METRIC_HEARTBEAT = _Dummy()
    METRIC_TREASURY_BUFFER = METRIC_TREASURY_RESERVE_VAL = METRIC_TREASURY_LAST_TS = (
        METRIC_TREASURY_EVENTS
    ) = METRIC_GROSS_EXPOSURE = _Dummy()
    METRIC_ADAPTIVE_RISK_MULT = _Dummy()

# ---------------- Paths & Directories ----------------
LEDGER_PATH = os.getenv("LEDGER_PATH", "runtime/ledger/live_ledger.jsonl")
pv.LEDGER_PATH = LEDGER_PATH  # sync
STATE_PATH = os.getenv("STATE_PATH", "runtime/state/state.json")
AUDIT_LOG_PATH = os.getenv("AUDIT_LOG_PATH", "runtime/audit/audit_log.jsonl")
HEARTBEAT_PATH = os.getenv("HEARTBEAT_PATH", "runtime/heartbeat.json")
PAUSE_FILE = os.getenv("PAUSE_FILE", "runtime/PAUSE")
for d in [
    "runtime",
    "runtime/logs",
    "runtime/ledger",
    "runtime/state",
    "runtime/audit",
]:
    os.makedirs(d, exist_ok=True)

# ---------------- Config ----------------
CFG = {
    "DRY_RUN": os.getenv("DRY_RUN", "true").lower() == "true",
    "MAX_NOTIONAL_PER_ORDER": float(os.getenv("MAX_NOTIONAL_PER_ORDER", "20") or 20),
    "QUOTE_SYMBOL": os.getenv("QUOTE_SYMBOL", "USDT"),
    "SYMBOLS": [
        s.strip().upper()
        for s in os.getenv("ALLOWED_SYMBOLS", "").split(",")
        if s.strip()
    ],
    "LOOKBACK_BREAKOUT": int(os.getenv("LOOKBACK_BREAKOUT", "40") or 40),
    "MIN_PROFIT_EXIT_BPS": int(os.getenv("MIN_PROFIT_EXIT_BPS", "50") or 50),
    "TRAILING_STOP_BPS": int(os.getenv("TRAILING_STOP_BPS", "300") or 300),
    "TAKER_FEE_BPS": float(os.getenv("TAKER_FEE_BPS", "10") or 10),
    "SLIPPAGE_BPS": int(os.getenv("SLIPPAGE_BPS", "10") or 10),
    "DAILY_MAX_LOSS_USD": float(os.getenv("DAILY_MAX_LOSS_USD", "100") or 100),
    "INTRADAY_MAX_DRAWDOWN_PCT": float(
        os.getenv("INTRADAY_MAX_DRAWDOWN_PCT", "10") or 10
    ),
    "HEARTBEAT_SEC": int(os.getenv("HEARTBEAT_SEC", "15") or 15),
    "RISK_BLOCK_COOLDOWN_SEC": int(os.getenv("RISK_BLOCK_COOLDOWN_SEC", "300") or 300),
    "SLEEP_LOOP_SEC": float(os.getenv("SLEEP_LOOP_SEC", "3") or 3),
    "TREASURY_RESERVE_SYMBOLS": [
        s.strip().upper()
        for s in os.getenv("TREASURY_RESERVE_SYMBOLS", "XRP/USDT,HBAR/USDT").split(",")
        if s.strip()
    ],
    "TREASURY_TARGET_WEIGHTS": [
        float(x)
        for x in os.getenv("TREASURY_TARGET_WEIGHTS", "0.6,0.4").split(",")
        if x.strip()
    ],
    "TREASURY_BANK_PCT_REALIZED": float(
        os.getenv("TREASURY_BANK_PCT_REALIZED", "0.25") or 0.25
    ),
    "TREASURY_MIN_BANK_USD": float(os.getenv("TREASURY_MIN_BANK_USD", "15") or 15),
    "REINVEST_ENABLE": os.getenv("REINVEST_ENABLE", "1") == "1",
    "MAX_GROSS_EXPOSURE_USD": float(os.getenv("MAX_GROSS_EXPOSURE_USD", "200") or 200),
    "UNIVERSE_REFRESH_MIN": int(os.getenv("UNIVERSE_REFRESH_MIN", "30") or 30),
    "RISK_PER_TRADE_PCT": float(os.getenv("RISK_PER_TRADE_PCT", "0.02") or 0.02),
}

# Normalize treasury weights
if CFG["TREASURY_TARGET_WEIGHTS"]:
    s_w = sum(CFG["TREASURY_TARGET_WEIGHTS"])
    if s_w > 0:
        CFG["TREASURY_TARGET_WEIGHTS"] = [
            w / s_w for w in CFG["TREASURY_TARGET_WEIGHTS"]
        ]
    if len(CFG["TREASURY_TARGET_WEIGHTS"]) != len(CFG["TREASURY_RESERVE_SYMBOLS"]):
        # resize by simple repeat or trim
        base = CFG["TREASURY_RESERVE_SYMBOLS"]
        w = CFG["TREASURY_TARGET_WEIGHTS"]
        if len(w) < len(base):
            add = [1.0 / len(base)] * (len(base) - len(w))
            w.extend(add)
        CFG["TREASURY_TARGET_WEIGHTS"] = w[: len(base)]

# Minimal fallback symbols
if not CFG["SYMBOLS"]:
    CFG["SYMBOLS"] = ["XRP/USDT", "HBAR/USDT"]

# ---------------- Exchange Adapter ----------------
try:  # pragma: no cover
    from libs.exchange_adapters.binance_us import get_client, guarded_create_order  # type: ignore
except Exception:

    def get_client():
        key = (
            os.getenv("BINANCEUS_API_KEY")
            or os.getenv("BINANCEUS_KEY")
            or os.getenv("BINANCEUS_KEY")
        )
        secret = (
            os.getenv("BINANCEUS_API_SECRET")
            or os.getenv("BINANCE_API_SECRET")
            or os.getenv("BINANCEUS_SECRET")
        )
        if not ccxt:
            raise RuntimeError("ccxt not available")
        ex = ccxt.binanceus(
            {
                "apiKey": key or "DUMMY",
                "secret": secret or "DUMMY",
                "enableRateLimit": True,
            }
        )
        try:
            ex.load_markets()
        except Exception:
            pass
        return ex

    def guarded_create_order(
        client, symbol, type_, side, amount, price=None, params=None
    ):
        if CFG["DRY_RUN"]:
            return {
                "id": "dry-" + str(time.time()),
                "symbol": symbol,
                "side": side,
                "type": type_,
                "amount": amount,
                "price": price,
                "status": "closed",
                "filled": amount,
            }
        return client.create_order(symbol, type_, side, amount, price, params or {})


CLIENT = get_client()
try:
    CLIENT.load_markets()
except Exception:
    pass

# ---------------- Ledger / Audit ----------------
_hash_cache_last: Optional[str] = None


def _read_last_hash() -> Optional[str]:
    global _hash_cache_last
    try:
        with open(LEDGER_PATH, "rb") as f:
            last = None
            for line in f:
                last = line
            if not last:
                return None
            rec = json.loads(last.decode("utf-8", "ignore"))
            _hash_cache_last = rec.get("hash")
            return _hash_cache_last
    except Exception:
        return None


def _write_ledger(event: str, data: Dict[str, Any]):
    prev = _read_last_hash()
    record = {
        "ts": now_utc().isoformat().replace("+00:00", "Z"),
        "event": event,
        "component": "momentum.bot",
        "model_version": MODEL_VERSION,
        "bot_id": BOT_ID,
        "prompt_hash": getattr(pv, "compute_prompt_hash", lambda: "na")(),
        "git_commit": getattr(pv, "get_git_commit", lambda: "unknown")(),
        **data,
    }
    payload = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    h = hashlib.sha256(payload + (prev or "").encode()).hexdigest()
    record["prev_hash"] = prev
    record["hash"] = h
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


_audit_lock = threading.Lock()


def audit(event: str, data: Dict[str, Any]):
    try:
        with _audit_lock:
            with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
                rec = {
                    "ts": now_utc().isoformat().replace("+00:00", "Z"),
                    "event": event,
                    "model_version": MODEL_VERSION,
                    "bot_id": BOT_ID,
                    **data,
                }
                f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


# ---------------- Risk / Treasury State ----------------
@dataclass
class RiskState:
    realized_today: float = 0.0
    peak_realized: float = 0.0
    last_reset_day: str = ""
    risk_block_reason: Optional[str] = None
    last_block_ts: float = 0.0


RISK = RiskState()


@dataclass
class TreasuryState:
    realized_pnl_buffer: float = 0.0
    cumulative_banked_usd: float = 0.0
    last_bank_ts: float = 0.0


TREASURY = TreasuryState()

TODAY = now_utc().date().isoformat()
RISK.last_reset_day = TODAY
if os.path.exists(LEDGER_PATH):
    try:
        for line in open(LEDGER_PATH, "r", encoding="utf-8"):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("event") == "FILL" and rec.get("ts", "")[:10] == TODAY:
                RISK.realized_today += float(rec.get("realized_pnl_delta", 0) or 0)
                RISK.peak_realized = max(RISK.peak_realized, RISK.realized_today)
            if rec.get("event") == "TREASURY_BANK_DONE":
                TREASURY.cumulative_banked_usd = float(
                    rec.get("cumulative_banked_usd", TREASURY.cumulative_banked_usd)
                )
    except Exception:
        pass


@dataclass
class Position:
    symbol: str
    qty: float
    entry_price: float
    last_high: float
    side: str = "LONG"
    expected_edge_bps: float = 0.0


POSITIONS: Dict[str, Position] = {}
STATE_LOCK = threading.Lock()
if os.path.exists(STATE_PATH):
    try:
        raw = json.load(open(STATE_PATH))
        for sym, p in raw.get("positions", {}).items():
            try:
                POSITIONS[sym] = Position(**p)
            except Exception:
                pass
    except Exception:
        pass

# ---------------- Adaptive Risk & Circuit Breaker ----------------
ADAPTIVE_RISK_ENABLE = os.getenv("ADAPTIVE_RISK_ENABLE", "1") == "1"
ADAPTIVE_RISK_MIN_MULT = float(os.getenv("ADAPTIVE_RISK_MIN_MULT", "0.3") or 0.3)
ADAPTIVE_RISK_NEG_FILL_WINDOW = int(
    os.getenv("ADAPTIVE_RISK_NEG_FILL_WINDOW", "10") or 10
)
ADAPTIVE_RISK_RECOVERY_SEC = int(
    os.getenv("ADAPTIVE_RISK_RECOVERY_SEC", "3600") or 3600
)
RISK_MULTIPLIER = 1.0
_last_risk_recovery_check = 0.0
_recent_fills: List[float] = []

ERROR_CIRCUIT_COUNT = int(os.getenv("ERROR_CIRCUIT_COUNT", "5") or 5)
ERROR_CIRCUIT_WINDOW = int(os.getenv("ERROR_CIRCUIT_WINDOW", "60") or 60)
ERROR_CIRCUIT_COOLDOWN = int(os.getenv("ERROR_CIRCUIT_COOLDOWN", "120") or 120)
_ERROR_TIMES: List[float] = []
_CIRCUIT_OPEN_UNTIL = 0.0


def _record_error(err_type: str, detail: str):
    global _CIRCUIT_OPEN_UNTIL
    now = time.time()
    _ERROR_TIMES.append(now)
    while _ERROR_TIMES and now - _ERROR_TIMES[0] > ERROR_CIRCUIT_WINDOW:
        _ERROR_TIMES.pop(0)
    if len(_ERROR_TIMES) >= ERROR_CIRCUIT_COUNT and now >= _CIRCUIT_OPEN_UNTIL:
        _CIRCUIT_OPEN_UNTIL = now + ERROR_CIRCUIT_COOLDOWN
        _write_ledger(
            "EXCHANGE_CIRCUIT_OPEN",
            {
                "errors_in_window": len(_ERROR_TIMES),
                "cooldown_sec": ERROR_CIRCUIT_COOLDOWN,
            },
        )
        audit("EXCHANGE_CIRCUIT_OPEN", {"errors_in_window": len(_ERROR_TIMES)})
    elif _CIRCUIT_OPEN_UNTIL and now >= _CIRCUIT_OPEN_UNTIL:
        _write_ledger("EXCHANGE_CIRCUIT_CLOSED", {})
        audit("EXCHANGE_CIRCUIT_CLOSED", {})


def _update_adaptive_risk(realized_pnl_delta: float):
    global RISK_MULTIPLIER, _last_risk_recovery_check
    if not ADAPTIVE_RISK_ENABLE:
        return
    now = time.time()
    if realized_pnl_delta != 0:
        _recent_fills.append(realized_pnl_delta)
        if len(_recent_fills) > ADAPTIVE_RISK_NEG_FILL_WINDOW:
            _recent_fills.pop(0)
        neg = [x for x in _recent_fills if x < 0]
        if len(_recent_fills) >= max(3, ADAPTIVE_RISK_NEG_FILL_WINDOW // 2):
            loss_ratio = len(neg) / len(_recent_fills)
            if loss_ratio >= 0.6:
                prev = RISK_MULTIPLIER
                RISK_MULTIPLIER = max(ADAPTIVE_RISK_MIN_MULT, RISK_MULTIPLIER * 0.85)
                if RISK_MULTIPLIER != prev:
                    _write_ledger(
                        "ADAPTIVE_RISK_SCALE_DOWN",
                        {"mult": RISK_MULTIPLIER, "loss_ratio": loss_ratio},
                    )
                    audit(
                        "ADAPTIVE_RISK_SCALE_DOWN",
                        {"mult": RISK_MULTIPLIER, "loss_ratio": loss_ratio},
                    )
                    _last_risk_recovery_check = now
    if (
        now - _last_risk_recovery_check >= ADAPTIVE_RISK_RECOVERY_SEC
        and RISK_MULTIPLIER < 1.0
    ):
        prev = RISK_MULTIPLIER
        RISK_MULTIPLIER = min(1.0, RISK_MULTIPLIER * 1.10)
        if RISK_MULTIPLIER != prev:
            _write_ledger("ADAPTIVE_RISK_RECOVER", {"mult": RISK_MULTIPLIER})
            audit("ADAPTIVE_RISK_RECOVER", {"mult": RISK_MULTIPLIER})
            _last_risk_recovery_check = now
    METRIC_ADAPTIVE_RISK_MULT.labels(BOT_ID).set(RISK_MULTIPLIER)


# ---------------- Heartbeat ----------------
_shutdown = threading.Event()


def _heartbeat_loop():
    while not _shutdown.wait(CFG["HEARTBEAT_SEC"]):
        ts = int(time.time())
        try:
            json.dump({"ts": ts, "bot_id": BOT_ID}, open(HEARTBEAT_PATH, "w"))
            METRIC_HEARTBEAT.labels(BOT_ID).set(ts)
        except Exception:
            pass
        try:
            if risk_mgr:
                pos_snapshot = {
                    s: {"qty": p.qty, "avg": p.entry_price}
                    for s, p in POSITIONS.items()
                }
                unreal, expo, per = risk_mgr.compute_unreal_and_exposure(pos_snapshot)
                var_p, var_sym, var_contrib = risk_mgr.compute_var95_contrib(
                    pos_snapshot
                )
                if VAR95_SYM_USD and VAR95_CONTRIB_USD:
                    for _s, _v in var_sym.items():
                        try:
                            VAR95_SYM_USD.labels(symbol=_s).set(float(_v))
                        except Exception:
                            pass
                    for _s, _v in var_contrib.items():
                        try:
                            VAR95_CONTRIB_USD.labels(symbol=_s).set(float(_v))
                        except Exception:
                            pass
                payload = {
                    "unrealized_usd": float(unreal),
                    "exposure_usd": float(expo),
                    "var95_usd": float(var_p),
                    "per_symbol": {
                        k: {"exposure": float(v[0]), "unrealized": float(v[1])}
                        for k, v in per.items()
                    },
                    "per_symbol_var95_usd": {k: float(v) for k, v in var_sym.items()},
                    "per_symbol_var95_contrib_usd": {
                        k: float(v) for k, v in var_contrib.items()
                    },
                }
                _write_ledger("HEARTBEAT", payload)
                audit("HEARTBEAT", payload)
        except Exception:
            pass


hb_thr = threading.Thread(target=_heartbeat_loop, daemon=True, name="heartbeat")

# ---------------- Helpers ----------------


def _risk_update_metrics():
    METRIC_DAILY_REAL.labels(BOT_ID).set(RISK.realized_today)
    drawdown = 0.0
    if RISK.peak_realized > 0:
        drawdown = (
            (RISK.peak_realized - RISK.realized_today) / RISK.peak_realized * 100.0
        )
    METRIC_DD_PCT.labels(BOT_ID).set(drawdown)
    for reason in [
        "daily_loss",
        "drawdown",
        "panic_file",
        "approval_stale",
        "loss_streak_cooldown",
        "exchange_circuit",
    ]:
        METRIC_RISK_BLOCK.labels(BOT_ID, reason).set(
            1 if RISK.risk_block_reason == reason else 0
        )
    METRIC_TREASURY_BUFFER.labels(BOT_ID).set(TREASURY.realized_pnl_buffer)
    METRIC_GROSS_EXPOSURE.labels(BOT_ID).set(_gross_exposure())


def _check_day_rollover():
    global TODAY
    cur_day = now_utc().date().isoformat()
    if cur_day != RISK.last_reset_day:
        _write_ledger("DAILY_RESET", {"prev_day": RISK.last_reset_day})
        audit("DAILY_RESET", {"prev_day": RISK.last_reset_day})
        RISK.realized_today = 0.0
        RISK.peak_realized = 0.0
        RISK.last_reset_day = cur_day
        RISK.risk_block_reason = None
        TODAY = cur_day
        TREASURY.realized_pnl_buffer = 0.0


def _apply_strategy_overrides(symbol: str):
    prof = _STRATEGY_PROFILES.get(_SYMBOL_STRATEGY.get(symbol, ""), {})
    return (
        prof.get("LOOKBACK_BREAKOUT", CFG["LOOKBACK_BREAKOUT"]),
        prof.get("TRAILING_STOP_BPS", CFG["TRAILING_STOP_BPS"]),
        prof.get("MIN_PROFIT_EXIT_BPS", CFG["MIN_PROFIT_EXIT_BPS"]),
    )


def _check_approval_token():
    global _APPROVAL_STALE, _last_token_check
    now = time.time()
    if now - _last_token_check < _TOKEN_CHECK_INTERVAL:
        return
    _last_token_check = now
    try:
        if not os.path.exists(APPROVAL_TOKEN_PATH):
            if not _APPROVAL_STALE:
                _write_ledger("APPROVAL_MISSING", {"path": APPROVAL_TOKEN_PATH})
                audit("APPROVAL_MISSING", {"path": APPROVAL_TOKEN_PATH})
            _APPROVAL_STALE = True
            return
        age = now - os.path.getmtime(APPROVAL_TOKEN_PATH)
        if age > MAX_TOKEN_AGE_SEC:
            if not _APPROVAL_STALE:
                _write_ledger("APPROVAL_STALE", {"age_sec": age})
                audit("APPROVAL_STALE", {"age_sec": age})
            _APPROVAL_STALE = True
        else:
            if _APPROVAL_STALE:
                _write_ledger("APPROVAL_REFRESHED", {"age_sec": age})
                audit("APPROVAL_REFRESHED", {"age_sec": age})
            _APPROVAL_STALE = False
    except Exception:
        pass


def _maybe_end_loss_pause():
    global LOSS_STREAK_PAUSE_UNTIL
    if LOSS_STREAK_PAUSE_UNTIL and time.time() >= LOSS_STREAK_PAUSE_UNTIL:
        LOSS_STREAK_PAUSE_UNTIL = 0.0
        _write_ledger("LOSS_STREAK_PAUSE_END", {})
        audit("LOSS_STREAK_PAUSE_END", {})


def _maybe_update_symbols_from_claude():
    global _CLAUDE_REF, _last_claude_update
    if not _CLAUDE_ENABLED or not bootstrap_claude_analysis:
        return
    if _CLAUDE_REF is None:
        try:
            _CLAUDE_REF = bootstrap_claude_analysis()
            logging.info("Claude refresher started")
        except Exception as e:
            logging.warning("Claude bootstrap fail %s", e)
            return
    now = time.time()
    if now - _last_claude_update < _CLAUDE_UNIVERSE_REFRESH_SEC:
        return
    try:
        recs = _CLAUDE_REF.recommendations(min_conf=_CLAUDE_MIN_CONF)
        if not recs:
            _last_claude_update = now
            return
        _SYMBOL_STRATEGY.clear()
        new_syms = [r["symbol"] for r in recs]
        for r in recs:
            _SYMBOL_STRATEGY[r["symbol"]] = r.get("strategy", "")
        with STATE_LOCK:
            active = list(POSITIONS.keys())
        merged = list(dict.fromkeys(active + new_syms))
        if merged != CFG["SYMBOLS"]:
            CFG["SYMBOLS"] = merged
            _write_ledger(
                "UNIVERSE_REFRESH_CLAUDE", {"symbols": merged, "count": len(merged)}
            )
            audit("UNIVERSE_REFRESH_CLAUDE", {"symbols": merged, "count": len(merged)})
    except Exception as e:
        audit("UNIVERSE_REFRESH_CLAUDE_FAIL", {"err": str(e)})
    finally:
        _last_claude_update = now


# ---------------- Treasury Helpers ----------------


def _fetch_ticker_price(symbol: str) -> Optional[float]:
    try:
        t = CLIENT.fetch_ticker(symbol)
        return t.get("last") or t.get("close") or t.get("info", {}).get("lastPrice")
    except Exception:
        return None


def _reserve_values() -> Dict[str, float]:
    out = {}
    try:
        bal = CLIENT.fetch_balance()
    except Exception:
        bal = {}
    for sym in CFG["TREASURY_RESERVE_SYMBOLS"]:
        if "/" in sym:
            base, quote = sym.split("/")
        else:
            base, quote = sym, "USDT"
            sym = f"{base}/{quote}"
        px = _fetch_ticker_price(sym)
        if px is None:
            continue
        base_free = 0.0
        try:
            base_free = float(((bal or {}).get(base) or {}).get("free") or 0)
        except Exception:
            pass
        out[sym] = base_free * px
    return out


def _gross_exposure() -> float:
    return sum(p.qty * p.entry_price for p in POSITIONS.values())


# ---------------- Risk Gates ----------------


def _risk_gate_new_entry() -> bool:
    _check_approval_token()
    _maybe_end_loss_pause()
    _check_day_rollover()
    # daily loss
    if RISK.realized_today <= -CFG["DAILY_MAX_LOSS_USD"]:
        if RISK.risk_block_reason != "daily_loss":
            RISK.risk_block_reason = "daily_loss"
            RISK.last_block_ts = time.time()
            _write_ledger(
                "RISK_LIMIT_TRIGGER",
                {"reason": "daily_loss", "realized_today": RISK.realized_today},
            )
            audit("RISK_LIMIT_TRIGGER", {"reason": "daily_loss"})
        return False
    # drawdown
    if RISK.peak_realized > 0:
        dd_pct = (RISK.peak_realized - RISK.realized_today) / RISK.peak_realized * 100.0
        if dd_pct >= CFG["INTRADAY_MAX_DRAWDOWN_PCT"]:
            if RISK.risk_block_reason != "drawdown":
                RISK.risk_block_reason = "drawdown"
                RISK.last_block_ts = time.time()
                _write_ledger(
                    "RISK_LIMIT_TRIGGER", {"reason": "drawdown", "drawdown_pct": dd_pct}
                )
                audit("RISK_LIMIT_TRIGGER", {"reason": "drawdown"})
            return False
    if os.path.exists(PAUSE_FILE):
        if RISK.risk_block_reason != "panic_file":
            RISK.risk_block_reason = "panic_file"
            RISK.last_block_ts = time.time()
            audit("RISK_LIMIT_TRIGGER", {"reason": "panic_file"})
        return False
    if _APPROVAL_STALE:
        if RISK.risk_block_reason != "approval_stale":
            RISK.risk_block_reason = "approval_stale"
            RISK.last_block_ts = time.time()
            _write_ledger("RISK_LIMIT_TRIGGER", {"reason": "approval_stale"})
            audit("RISK_LIMIT_TRIGGER", {"reason": "approval_stale"})
        return False
    if LOSS_STREAK_PAUSE_UNTIL and time.time() < LOSS_STREAK_PAUSE_UNTIL:
        if RISK.risk_block_reason != "loss_streak_cooldown":
            RISK.risk_block_reason = "loss_streak_cooldown"
            RISK.last_block_ts = time.time()
            _write_ledger("RISK_LIMIT_TRIGGER", {"reason": "loss_streak_cooldown"})
            audit("RISK_LIMIT_TRIGGER", {"reason": "loss_streak_cooldown"})
        return False
    now = time.time()
    global _CIRCUIT_OPEN_UNTIL
    if _CIRCUIT_OPEN_UNTIL and now < _CIRCUIT_OPEN_UNTIL:
        if RISK.risk_block_reason != "exchange_circuit":
            RISK.risk_block_reason = "exchange_circuit"
            RISK.last_block_ts = now
            _write_ledger("RISK_LIMIT_TRIGGER", {"reason": "exchange_circuit"})
            audit("RISK_LIMIT_TRIGGER", {"reason": "exchange_circuit"})
        return False
    if RISK.risk_block_reason in (
        "panic_file",
        "approval_stale",
        "loss_streak_cooldown",
        "exchange_circuit",
    ):
        # transient: clear if condition gone
        if not (
            _APPROVAL_STALE
            or (LOSS_STREAK_PAUSE_UNTIL and time.time() < LOSS_STREAK_PAUSE_UNTIL)
            or (_CIRCUIT_OPEN_UNTIL and time.time() < _CIRCUIT_OPEN_UNTIL)
            or os.path.exists(PAUSE_FILE)
        ):
            RISK.risk_block_reason = None
    return RISK.risk_block_reason is None


# ---------------- Market Data / Signals ----------------


def _fetch_ohlcv(symbol: str, limit: int):
    try:
        return CLIENT.fetch_ohlcv(symbol, timeframe="5m", limit=limit)
    except Exception:
        return None


def _should_open_long(symbol: str) -> Optional[Dict[str, Any]]:
    lookback, _, _ = _apply_strategy_overrides(symbol)
    candles = _fetch_ohlcv(symbol, lookback)
    if not candles or len(candles) < 5:
        return None
    closes = [c[4] for c in candles]
    highs = [c[2] for c in candles]
    last_close = closes[-1]
    ref = max(highs[-lookback:-1]) if len(highs) >= lookback else max(highs[:-1])
    if last_close > ref:
        edge_bps = (last_close - ref) / max(ref, 1e-12) * 10000.0
        return {"price": last_close, "breakout_ref": ref, "expected_edge_bps": edge_bps}
    return None


def _should_close_long(symbol: str, pos: Position) -> Optional[Dict[str, Any]]:
    _, trail_bps, min_exit_bps = _apply_strategy_overrides(symbol)
    candles = _fetch_ohlcv(symbol, 10)
    px = None
    if candles:
        px = candles[-1][4]
        high = max(c[2] for c in candles[-10:])
        pos.last_high = max(pos.last_high, high)
    else:
        try:
            t = CLIENT.fetch_ticker(symbol)
            px = t.get("last") or t.get("close")
        except Exception:
            pass
    if px is None:
        return None
    gain_bps = (px - pos.entry_price) / pos.entry_price * 10000.0
    if gain_bps >= min_exit_bps:
        trigger = pos.last_high * (1 - trail_bps / 10000.0)
        if px <= trigger:
            return {"price": px, "reason": "trailing_stop", "gain_bps": gain_bps}
    return None


# ---------------- Order / Fills ----------------
REJECT_COUNTS: Dict[str, int] = {}


def _reject(reason: str, detail: Dict[str, Any]):
    REJECT_COUNTS[reason] = REJECT_COUNTS.get(reason, 0) + 1
    METRIC_REJECTS.labels(BOT_ID, reason).inc()
    _write_ledger("ORDER_SKIPPED", {"reason": reason, **detail})
    audit("ORDER_SKIPPED", {"reason": reason, **detail})


def _snap(symbol: str, price: Optional[float], amount: float):
    try:
        if not getattr(CLIENT, "markets", None):
            CLIENT.load_markets()
        m = CLIENT.markets.get(symbol, {})
        if price is not None:
            price = float(CLIENT.price_to_precision(symbol, price))
        amount = float(CLIENT.amount_to_precision(symbol, amount))
        min_cost = (m.get("limits", {}) or {}).get("cost", {}).get("min")
        if min_cost and price is not None and price * amount < float(min_cost):
            need = float(min_cost) / max(price, 1e-12) * 1.001
            amount = float(CLIENT.amount_to_precision(symbol, need))
        return price, amount
    except Exception as e:
        logging.warning("snap_fail %s %s", symbol, e)
        return price, amount


def place_order(
    symbol: str,
    side: str,
    qty: float,
    intended_price: float,
    order_type: str = "market",
) -> Optional[Dict[str, Any]]:
    price_for_create = None if order_type == "market" else intended_price
    price_for_create, qty = _snap(symbol, price_for_create, qty)
    _write_ledger(
        "PRE_ORDER",
        {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price_for_create,
            "type": order_type,
        },
    )
    audit("PRE_ORDER", {"symbol": symbol, "side": side, "qty": qty})
    try:
        resp = guarded_create_order(
            CLIENT, symbol, order_type, side, qty, price_for_create, params=None
        )
        _write_ledger(
            "ORDER_OK",
            {
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "price": price_for_create,
                "resp_id": resp.get("id"),
            },
        )
        audit("ORDER_OK", {"symbol": symbol, "side": side, "qty": qty})
        exec_price = (
            intended_price
            if order_type == "market"
            else (price_for_create or intended_price)
        )
        try:
            sl_bps = (
                abs(exec_price - intended_price) / max(intended_price, 1e-12) * 10000.0
            )
            METRIC_SLIPPAGE.observe(sl_bps)
        except Exception:
            pass
        _record_fill(symbol, side, qty, exec_price, is_close=(side.upper() == "SELL"))
        return resp
    except Exception as e:
        _record_error("create_order", str(e))
        _reject("create_error", {"symbol": symbol, "err": str(e)})
        return None


# ---------------- Position Accounting ----------------


def _record_fill(symbol: str, side: str, qty: float, price: float, is_close: bool):
    global LOSS_STREAK_COUNT, LOSS_STREAK_PAUSE_UNTIL
    realized = 0.0
    if is_close:
        pos = POSITIONS.get(symbol)
        if pos:
            realized = (price - pos.entry_price) * qty - (
                CFG["TAKER_FEE_BPS"] / 10000.0
            ) * price * qty
            RISK.realized_today += realized
            RISK.peak_realized = max(RISK.peak_realized, RISK.realized_today)
            if realized > 0:
                TREASURY.realized_pnl_buffer += realized
    _write_ledger(
        "FILL",
        {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price,
            "realized_pnl_delta": realized,
            "realized_pnl_today": RISK.realized_today,
            "treasury_buffer": TREASURY.realized_pnl_buffer,
        },
    )
    audit(
        "FILL",
        {
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price,
            "realized": realized,
        },
    )
    _risk_update_metrics()
    if is_close:
        if realized > 0:
            _maybe_bank_treasury()
        _update_adaptive_risk(realized)
        if realized < 0:
            LOSS_STREAK_COUNT += 1
            if (
                LOSS_STREAK_COUNT >= LOSS_STREAK_THRESHOLD
                and not LOSS_STREAK_PAUSE_UNTIL
            ):
                LOSS_STREAK_PAUSE_UNTIL = time.time() + LOSS_STREAK_COOLDOWN_SEC
                _write_ledger(
                    "LOSS_STREAK_PAUSE_START",
                    {
                        "count": LOSS_STREAK_COUNT,
                        "cooldown_sec": LOSS_STREAK_COOLDOWN_SEC,
                    },
                )
                audit("LOSS_STREAK_PAUSE_START", {"count": LOSS_STREAK_COUNT})
        else:
            if LOSS_STREAK_COUNT > 0:
                LOSS_STREAK_COUNT = 0


# ---------------- Treasury Banking ----------------
_banking_lock = threading.Lock()


def _maybe_bank_treasury():
    if TREASURY.realized_pnl_buffer < CFG["TREASURY_MIN_BANK_USD"]:
        return
    bank_amount = TREASURY.realized_pnl_buffer * CFG["TREASURY_BANK_PCT_REALIZED"]
    if bank_amount <= 0:
        return
    with _banking_lock:
        if TREASURY.realized_pnl_buffer < CFG["TREASURY_MIN_BANK_USD"]:
            return
        _write_ledger(
            "TREASURY_BANK_START",
            {"buffer": TREASURY.realized_pnl_buffer, "bank_amount": bank_amount},
        )
        audit("TREASURY_BANK_START", {"buffer": TREASURY.realized_pnl_buffer})
        weights = CFG["TREASURY_TARGET_WEIGHTS"] or [
            1.0 / len(CFG["TREASURY_RESERVE_SYMBOLS"])
        ] * len(CFG["TREASURY_RESERVE_SYMBOLS"])
        for sym, w in zip(CFG["TREASURY_RESERVE_SYMBOLS"], weights):
            alloc = bank_amount * w
            if alloc <= 0:
                continue
            px = _fetch_ticker_price(sym)
            if not px:
                continue
            qty = alloc / max(px, 1e-12)
            price_for_create = None
            price_for_create, qty = _snap(sym, price_for_create, qty)
            try:
                if CFG["DRY_RUN"]:
                    resp = {"id": "dry-bank-" + str(time.time())}
                else:
                    resp = guarded_create_order(
                        CLIENT, sym, "market", "BUY", qty, price_for_create, params=None
                    )
                _write_ledger(
                    "TREASURY_TRADE",
                    {
                        "symbol": sym,
                        "qty": qty,
                        "notional": qty * px,
                        "resp_id": resp.get("id"),
                    },
                )
                audit("TREASURY_TRADE", {"symbol": sym, "qty": qty})
            except Exception as e:
                _write_ledger("TREASURY_TRADE_FAIL", {"symbol": sym, "err": str(e)})
                audit("TREASURY_TRADE_FAIL", {"symbol": sym, "err": str(e)})
        TREASURY.realized_pnl_buffer -= bank_amount
        if TREASURY.realized_pnl_buffer < 0:
            TREASURY.realized_pnl_buffer = 0
        TREASURY.cumulative_banked_usd += bank_amount
        TREASURY.last_bank_ts = time.time()
        METRIC_TREASURY_LAST_TS.labels(BOT_ID).set(TREASURY.last_bank_ts)
        METRIC_TREASURY_EVENTS.labels(BOT_ID).inc()
        for rsym, v in _reserve_values().items():
            METRIC_TREASURY_RESERVE_VAL.labels(BOT_ID, rsym).set(v)
        _write_ledger(
            "TREASURY_BANK_DONE",
            {
                "banked_usd": bank_amount,
                "cumulative_banked_usd": TREASURY.cumulative_banked_usd,
                "buffer_remaining": TREASURY.realized_pnl_buffer,
            },
        )
        audit("TREASURY_BANK_DONE", {"banked_usd": bank_amount})


# ---------------- Sizing ----------------


def _compute_qty(symbol: str, price: float) -> float:
    gross = _gross_exposure()
    cap = CFG["MAX_GROSS_EXPOSURE_USD"]
    headroom = max(0.0, cap - gross)
    if headroom <= 0:
        return 0.0
    per_order_cap = min(CFG["MAX_NOTIONAL_PER_ORDER"], headroom)
    risk_notional = cap * CFG["RISK_PER_TRADE_PCT"] * RISK_MULTIPLIER
    notional = min(per_order_cap, risk_notional)
    return notional / max(price, 1e-12)


# ---------------- Live Addons Init ----------------
_def_live_added = globals().get("_def_live_added")
if not _def_live_added:

    def _init_live_addons():  # pragma: no cover
        global price_cache, ws_client, risk_mgr
        if RiskManager is None or PriceCache is None:
            return
        if risk_mgr is not None:
            return
        try:
            price_cache = PriceCache()
            risk_mgr = RiskManager(price_cache)
            if CFG.get("SYMBOLS"):
                ws_client = WSClient(price_cache, CFG["SYMBOLS"])
                ws_client.start()
            logging.info("live_addons_initialized symbols=%s", CFG["SYMBOLS"])
        except Exception as e:
            logging.warning("live_addons_init_fail %s", e)

    _def_live_added = True

# ---------------- Main Loop ----------------
STOP_REQUESTED = False


def _signal_handler(sig, frame):
    global STOP_REQUESTED
    STOP_REQUESTED = True


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
try:
    signal.signal(
        signal.SIGUSR1,
        lambda s, f: json.dump(
            {
                "positions": {s: vars(p) for s, p in POSITIONS.items()},
                "ts": time.time(),
                "symbols": CFG["SYMBOLS"],
            },
            open("runtime/debug_snapshot.json", "w"),
        )
        or _write_ledger("DEBUG_SNAPSHOT", {"path": "runtime/debug_snapshot.json"}),
    )
except Exception:
    pass

# ---------------- Core run_once ----------------


def run_once():
    _maybe_update_symbols_from_claude()
    _risk_update_metrics()
    if STOP_REQUESTED:
        return False
    if not CFG["SYMBOLS"]:
        time.sleep(1)
        return True
    # record prices for VaR
    if risk_mgr and price_cache:
        for sym in CFG["SYMBOLS"]:
            try:
                risk_mgr.record_price(sym)
            except Exception:
                pass
    for symbol in CFG["SYMBOLS"]:
        if STOP_REQUESTED:
            break
        if _gross_exposure() >= CFG["MAX_GROSS_EXPOSURE_USD"]:
            _reject("gross_exposure_cap", {"symbol": symbol})
            break
        if risk_mgr and symbol == CFG["SYMBOLS"][0]:
            try:
                pos_snapshot = {
                    s: {"qty": p.qty, "avg": p.entry_price}
                    for s, p in POSITIONS.items()
                }
                equity_proxy = RISK.realized_today + _gross_exposure()
                ok, reason = risk_mgr.set_metrics_and_gate(pos_snapshot, equity_proxy)
                if not ok:
                    _reject(reason, {"symbol": symbol, "var_gate": True})
            except Exception:
                pass
        pos = POSITIONS.get(symbol)
        if pos:
            decision = _should_close_long(symbol, pos)
            if decision:
                qty = pos.qty
                resp = place_order(symbol, "SELL", qty, decision["price"])
                if resp:
                    with STATE_LOCK:
                        POSITIONS.pop(symbol, None)
                        persist_state()
                continue
        if pos:
            continue
        if not _risk_gate_new_entry():
            _reject(
                "risk_limit",
                {"symbol": symbol, "active_reason": RISK.risk_block_reason},
            )
            continue
        if os.path.exists(PAUSE_FILE):
            _reject("panic_file", {"symbol": symbol})
            continue
        sig = _should_open_long(symbol)
        if not sig:
            continue
        qty = _compute_qty(symbol, sig["price"])
        if qty <= 0:
            _reject("zero_or_exposure_qty", {"symbol": symbol})
            continue
        notional = qty * sig["price"]
        max_risk_notional = CFG["MAX_GROSS_EXPOSURE_USD"] * CFG["RISK_PER_TRADE_PCT"]
        if notional > max_risk_notional * 1.10:
            _reject(
                "risk_notional_cap",
                {"symbol": symbol, "notional": notional, "cap": max_risk_notional},
            )
            continue
        resp = place_order(symbol, "BUY", qty, sig["price"])
        if resp:
            with STATE_LOCK:
                POSITIONS[symbol] = Position(
                    symbol=symbol,
                    qty=qty,
                    entry_price=sig["price"],
                    last_high=sig["price"],
                    expected_edge_bps=sig.get("expected_edge_bps", 0.0),
                )
                persist_state()
    return True


# ---------------- Persistence ----------------


def persist_state():
    try:
        json.dump(
            {"positions": {s: vars(p) for s, p in POSITIONS.items()}},
            open(STATE_PATH, "w"),
        )
    except Exception:
        pass


# ---------------- Main ----------------


def ensure_dirs():
    pass  # kept for backward compatibility


def main():
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
        )
    _init_live_addons()
    hb_thr.start()
    logging.info(
        "Bot start model_version=%s bot_id=%s dry_run=%s symbols=%s",
        MODEL_VERSION,
        BOT_ID,
        CFG["DRY_RUN"],
        CFG["SYMBOLS"],
    )
    _write_ledger(
        "BOT_START",
        {
            "model_version": MODEL_VERSION,
            "symbols": CFG["SYMBOLS"],
            "dry_run": CFG["DRY_RUN"],
        },
    )
    try:
        while not STOP_REQUESTED:
            if not run_once():
                break
            time.sleep(CFG["SLEEP_LOOP_SEC"])
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt")
    finally:
        _shutdown.set()
        try:
            hb_thr.join(timeout=2)
        except Exception:
            pass
        persist_state()
        _write_ledger("BOT_STOP", {"reason": "shutdown"})
        logging.info("Bot stopped")


if __name__ == "__main__":
    main()
