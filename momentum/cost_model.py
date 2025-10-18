from __future__ import annotations
import math
from typing import Optional


def bps_to_frac(bps: float) -> float:
    return (bps or 0.0) / 10000.0


def compute_net_edge_ok(
    symbol: str,
    side: str,
    price: float,
    amount: float,
    expected_alpha_bps: float,
    taker_fee_bps: float = 10.0,
    maker_fee_bps: float = 0.0,
    slippage_bps: float = 5.0,
    gas_usd: float = 0.0,
    buffer_bps: float = 3.0,
    maker: bool = False,
) -> bool:
    """
    Returns True if expected alpha (bps) covers fees + slippage + gas + buffer.
    Fees modeled as taker by default; set maker=True to use maker_fee_bps.
    gas_usd is converted to bps of notional using price*amount.
    """
    notional = max(1e-12, price * amount)
    fee_bps = maker_fee_bps if maker else taker_fee_bps

    # Convert gas in USD to bps on notional
    gas_bps = (gas_usd / notional) * 10000.0 if gas_usd > 0 else 0.0

    total_cost_bps = fee_bps + slippage_bps + gas_bps + (buffer_bps or 0.0)

    return (expected_alpha_bps or 0.0) >= total_cost_bps
