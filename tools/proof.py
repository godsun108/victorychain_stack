#!/usr/bin/env python3
import os, json, hmac, hashlib, argparse, sys
from typing import Dict, Any

# Canonical fields only (no secrets) for signature
CANONICAL_KEYS = [
    "mode",
    "exchange",
    "symbols",
    "limits",
    "git_commit",
    "prompt_hash",
    "files",
    "markets",
]


def redact_env(env: Dict[str, str]) -> Dict[str, Any]:
    red = {}
    for k, v in env.items():
        if any(s in k for s in ["KEY", "SECRET", "TOKEN", "PASSWORD"]):
            red[k] = "<redacted>"
        else:
            red[k] = v
    return red


def canonical_payload(
    env: Dict[str, str], markets: Dict[str, Any], files: Dict[str, str]
) -> Dict[str, Any]:
    from governance.prompt_version import compute_prompt_hash, get_git_commit

    mode = env.get("MODE", "paper")
    exchange = env.get("EXCHANGE", "binanceus")
    symbols = [
        s.strip()
        for s in env.get("SYMBOLS", "BTC/USDT,ETH/USDT").split(",")
        if s.strip()
    ]
    limits = {
        "MAX_NOTIONAL_PER_ORDER": float(env.get("MAX_NOTIONAL_PER_ORDER", "0") or 0),
        "MAX_OPEN_ORDERS": int(env.get("MAX_OPEN_ORDERS", "0") or 0),
        "SLIPPAGE_BPS": int(env.get("SLIPPAGE_BPS", "0") or 0),
        "MIN_PROFIT_BPS": int(env.get("MIN_PROFIT_BPS", "0") or 0),
    }
    return {
        "mode": mode,
        "exchange": exchange,
        "symbols": symbols,
        "limits": limits,
        "git_commit": get_git_commit(),
        "prompt_hash": compute_prompt_hash(),
        "files": files,
        "markets": {s: markets.get(s) for s in symbols if s in markets},
    }


def file_hash(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return "missing"


def collect_files() -> Dict[str, str]:
    candidates = [
        "libs/exchange_adapters/binance_us.py",
        "libs/common/guards.py",
        "governance/approvals.py",
        "scripts/smoke_live_binanceus.py",
    ]
    return {p: file_hash(p) for p in candidates}


def load_markets_snapshot() -> Dict[str, Any]:
    try:
        from libs.exchange_adapters.binance_us import get_client

        # Always use paper client for snapshot to avoid requiring live keys
        c = get_client("paper")
        return c.load_markets() or {}
    except Exception:
        return {}


def sign(payload: Dict[str, Any], secret: str) -> str:
    # Sign only canonical JSON of allowed keys to avoid secrets being included
    can = {k: payload.get(k) for k in CANONICAL_KEYS if k in payload}
    msg = json.dumps(can, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    env = dict(os.environ)
    markets = load_markets_snapshot()
    files = collect_files()
    payload = canonical_payload(env, markets, files)

    out = {
        "proof": payload,
        "redacted_env": redact_env(env),
        "signature": None,
        "signature_alg": "HMAC-SHA256",
    }

    secret = os.getenv("APPROVAL_SECRET")
    if not secret and os.getenv("MODE", "paper").lower() != "live":
        # In paper mode, allow deterministic fallback
        try:
            from governance.prompt_version import compute_prompt_hash

            secret = f"dev_fallback::{compute_prompt_hash()}"
        except Exception:
            secret = "dev_fallback::victorychain_local"
    if not secret:
        print(
            "ERROR: APPROVAL_SECRET required for signing in live mode", file=sys.stderr
        )
        sys.exit(2)

    out["signature"] = sign(payload, secret)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)

    print(f"WROTE {args.out}")


if __name__ == "__main__":
    main()
