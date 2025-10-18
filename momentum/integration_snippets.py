from __future__ import annotations
import os
from typing import Optional

from .cost_model import compute_net_edge_ok


def check_before_order(
    symbol: str,
    side: str,
    price: float,
    amount: float,
    expected_alpha_bps: float,
    taker_fee_bps: Optional[float] = None,
    maker_fee_bps: Optional[float] = None,
    slippage_bps: Optional[float] = None,
    gas_usd: Optional[float] = None,
    buffer_bps: Optional[float] = None,
) -> bool:
    """
    Drop-in helper to gate orders by net edge.
    Returns True if expected alpha clears costs+buffer, else False.
    Reads defaults from env if args are None.
    """

    # Read defaults from environment
    def _get_env_bps(name: str, default: float) -> float:
        try:
            return float(os.environ.get(name, default))
        except Exception:
            return default

    taker_fee_bps = (
        taker_fee_bps
        if taker_fee_bps is not None
        else _get_env_bps("TAKER_FEE_BPS", 10.0)
    )
    maker_fee_bps = (
        maker_fee_bps
        if maker_fee_bps is not None
        else _get_env_bps("MAKER_FEE_BPS", 0.0)
    )
    slippage_bps = (
        slippage_bps if slippage_bps is not None else _get_env_bps("SLIPPAGE_BPS", 5.0)
    )
    gas_usd = gas_usd if gas_usd is not None else float(os.environ.get("GAS_USD", "0"))
    buffer_bps = (
        buffer_bps if buffer_bps is not None else _get_env_bps("EDGE_BUFFER_BPS", 3.0)
    )

    return compute_net_edge_ok(
        symbol=symbol,
        side=side,
        price=price,
        amount=amount,
        expected_alpha_bps=expected_alpha_bps,
        taker_fee_bps=taker_fee_bps,
        maker_fee_bps=maker_fee_bps,
        slippage_bps=slippage_bps,
        gas_usd=gas_usd,
        buffer_bps=buffer_bps,
    )
