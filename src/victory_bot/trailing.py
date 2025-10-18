import os
import logging
from datetime import datetime
from typing import List

logger = logging.getLogger(__name__)


def _load_config():
    return {
        "activation_pct": float(os.getenv("TRAILING_STOP_ACTIVATION_PCT", 0.50)),
        "trail_pct": float(os.getenv("TRAILING_STOP_PCT", 0.10)),
        "min_profit_pct": float(os.getenv("MIN_PROFIT_EXIT_PCT", 0.05)),
        "initial_stop_pct": float(os.getenv("VICTORYBOT_STOP_LOSS_PCT", 0.02)),
    }


def compute_trailing_candidate(
    entry_price: float, current_price: float, cfg: dict, allow_wider: bool = False
) -> float:
    """
    Return a candidate stop price (absolute price) for a long position.
    """
    trail = cfg["trail_pct"]
    candidate = current_price * (1 - trail)
    if allow_wider:
        candidate = current_price * (1 - (trail * 1.5))
    return candidate


def update_trailing_stops(positions: List[object]) -> List[object]:
    """
    Update stop_loss on each PortfolioPosition in-place and return positions.
    Uses env-configured thresholds. Never lowers an existing stop; only tightens.
    """
    cfg = _load_config()
    activation = cfg["activation_pct"]
    trail = cfg["trail_pct"]
    min_profit = cfg["min_profit_pct"]
    initial_stop_pct = cfg["initial_stop_pct"]

    for pos in positions:
        try:
            entry = getattr(pos, "entry_price", 0) or 0
            current = getattr(pos, "current_price", 0) or 0
            if entry <= 0 or current <= 0:
                continue

            pnl_pct = (current - entry) / entry
            existing = getattr(pos, "stop_loss", None)
            if existing is None or existing == 0:
                existing = entry * (1 - initial_stop_pct)

            new_stop = existing

            # Full trailing activation
            if pnl_pct >= activation:
                # determine if we should widen trail
                allow_wider = False
                try:
                    recent = getattr(pos, "recent_ohlcv", None)
                    if recent:
                        closes = [c[4] for c in recent]
                        volumes = [c[5] for c in recent]
                        if len(closes) >= 2 and closes[0] > 0:
                            momentum_short = (closes[-1] - closes[0]) / closes[0]
                            volume_trend = volumes[-1] - volumes[0]
                            if momentum_short > 0.02 and volume_trend > 0:
                                allow_wider = True
                except Exception:
                    pass

                candidate = compute_trailing_candidate(
                    entry, current, cfg, allow_wider=allow_wider
                )
                if candidate > new_stop:
                    new_stop = candidate

            # Protect small profits
            elif pnl_pct >= min_profit:
                candidate = current * (1 - (trail * 0.5))
                if candidate > new_stop:
                    new_stop = candidate

            pos.stop_loss = new_stop
            pos.last_updated = datetime.utcnow()
        except Exception as e:
            logger.debug("trailing.update_trailing_stops error: %s", e)
    return positions
