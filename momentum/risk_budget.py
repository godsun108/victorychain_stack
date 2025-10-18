from __future__ import annotations
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from loguru import logger

STATE = Path("runtime/risk_budget/state.json")
STATE.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class RiskCaps:
    quote_alloc_pct: float
    max_notional_per_order: float


def trailing_stats(window_days: int = 7) -> Dict[str, float]:
    # Placeholder: wire to your PnL/trades history
    # Returns dictionary with 'sharpe' and 'drawdown'
    try:
        with open("runtime/metrics/weekly_pnl.json", "r") as f:
            d = json.load(f)
            sharpe = float(d.get("sharpe", 0))
            dd = float(d.get("drawdown", 0))
            return {"sharpe": sharpe, "drawdown": dd}
    except Exception:
        return {"sharpe": 0.0, "drawdown": 0.0}


def compute_caps(
    stats: Dict[str, float], base_quote_alloc_pct: float, base_max_notional: float
) -> RiskCaps:
    sharpe = stats.get("sharpe", 0.0)
    dd = stats.get("drawdown", 0.0)

    scale = 1.0
    if sharpe < 0.5 or dd > 0.15:
        scale = 0.5
    elif sharpe > 1.5 and dd < 0.05:
        scale = 1.2

    return RiskCaps(
        quote_alloc_pct=max(0.0001, base_quote_alloc_pct * scale),
        max_notional_per_order=max(1.0, base_max_notional * scale),
    )


def apply_caps_to_env(caps: RiskCaps) -> Dict[str, str]:
    env = {}
    env["QUOTE_ALLOC_PCT"] = f"{caps.quote_alloc_pct:.6f}"
    env["MAX_NOTIONAL_PER_ORDER"] = f"{caps.max_notional_per_order:.2f}"
    STATE.write_text(json.dumps(caps.__dict__, indent=2))
    logger.info(f"Applied caps: {env}")
    return env


if __name__ == "__main__":
    base_q = float(os.environ.get("QUOTE_ALLOC_PCT", "0.002"))
    base_n = float(os.environ.get("MAX_NOTIONAL_PER_ORDER", "15"))
    s = trailing_stats()
    c = compute_caps(s, base_q, base_n)
    print(json.dumps(c.__dict__, indent=2))
