import os
import time
import asyncio
from typing import Any, Dict, List, Optional

import ccxt
import logging

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3
DEFAULT_POLL_INTERVAL = 1.0  # seconds
DEFAULT_TWAP_SLICE_SECONDS = 10.0


def init_exchange_from_env():
    api_key = os.getenv("BINANCEUS_KEY")
    secret = os.getenv("BINANCEUS_SECRET")
    if not api_key or not secret:
        logger.info("BINANCEUS keys not found; exchange not initialized (dry-run).")
        return None
    try:
        ex = ccxt.binanceus(
            {
                "apiKey": api_key,
                "secret": secret,
                "enableRateLimit": True,
            }
        )

    except Exception as e:
        logger.exception("failed to init ccxt.binanceus: %s", e)
        return None


def _symbol_to_ccxt(symbol: str) -> str:
    """Return symbol in CCXT's expected 'BASE/QUOTE' form, e.g. 'BTC/USDT'."""
    if not symbol:
        return symbol
    if "/" in symbol:
        return symbol
    if symbol.endswith("USDT"):
        base = symbol[:-4]
        return f"{base}/USDT"
    return symbol


def _poll_order(
    exchange,
    symbol_ccxt: str,
    order_id: str,
    timeout: float = 30.0,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> Optional[Dict]:
    if not exchange:
        return None
    start = time.time()
    while True:
        try:
            order = exchange.fetch_order(order_id, symbol_ccxt)
            status = order.get("status")
            if status in ("closed", "canceled", "filled"):
                return order
        except Exception as e:
            logger.debug("poll_order fetch error: %s", e)
        if time.time() - start > timeout:
            logger.warning("order %s poll timeout", order_id)
            return None
        time.sleep(poll_interval)


def _normalize_symbol(symbol: str) -> str:
    """Normalize symbol formats (accept 'BTC/USDT' or 'BTCUSDT')."""
    return symbol.replace("/", "") if symbol and "/" in symbol else symbol


def _normalize_symbol_input(symbol: str) -> str:
    if not symbol:
        return symbol
    return symbol.replace("/", "")


def _normalize_for_exchange(symbol: str) -> str:
    """Accept 'BTC/USDT' or 'BTCUSDT' and return both common forms as needed.
    Default behavior used by tests: keep symbol as passed but ensure a no-slash form
    is available when adapters expect it by removing '/'."""
    if not symbol:
        return symbol
    return symbol.replace("/", "")


# --- add helpers expected by tests ---
def _sym_for_adapter(symbol: str) -> str:
    if not symbol:
        return symbol
    return symbol.replace("/", "")


def safe_market_buy(
    exchange: Optional[Any],
    symbol: str,
    amount: float,
    max_retries: int = DEFAULT_MAX_RETRIES,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> Dict[str, Any]:
    if exchange is None:
        return {
            "id": "sim",
            "status": "closed",
            "average": 0.0,
            "filled": amount,
            "symbol": symbol,
            "simulated": True,
        }
    sym = _sym_for_adapter(symbol)
    order = exchange.create_market_buy_order(sym, amount)
    order_id = order.get("id") if isinstance(order, dict) else order
    last = order
    for _ in range(max_retries + 1):
        try:
            last = exchange.fetch_order(order_id, sym)
        except Exception:
            pass
        status = (last or {}).get("status") or (last or {}).get("state")
        if status in ("closed", "filled", "canceled"):
            return last
        time.sleep(poll_interval)
    return last


def safe_market_sell(
    exchange: Optional[Any],
    symbol: str,
    amount: float,
    max_retries: int = DEFAULT_MAX_RETRIES,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> Dict[str, Any]:
    if exchange is None:
        return {
            "id": "sim",
            "status": "closed",
            "average": 0.0,
            "filled": amount,
            "symbol": symbol,
            "simulated": True,
        }
    sym = _sym_for_adapter(symbol)
    order = exchange.create_market_sell_order(sym, amount)
    order_id = order.get("id") if isinstance(order, dict) else order
    last = order
    for _ in range(max_retries + 1):
        try:
            last = exchange.fetch_order(order_id, sym)
        except Exception:
            pass
        status = (last or {}).get("status") or (last or {}).get("state")
        if status in ("closed", "filled", "canceled"):
            return last
        time.sleep(poll_interval)
    return last


def place_limit_ioc(
    exchange: Optional[Any],
    symbol: str,
    amount: float,
    price: float,
    side: str = "buy",
    max_retries: int = DEFAULT_MAX_RETRIES,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> Dict[str, Any]:
    if exchange is None:
        return {
            "id": "sim",
            "status": "closed",
            "price": price,
            "filled": amount,
            "symbol": symbol,
            "simulated": True,
        }
    sym = _sym_for_adapter(symbol)
    side = (side or "buy").lower()
    if side == "buy":
        order = exchange.create_limit_buy_order(sym, amount, price)
    else:
        order = exchange.create_limit_sell_order(sym, amount, price)
    order_id = order.get("id") if isinstance(order, dict) else order
    last = order
    for _ in range(max_retries + 1):
        try:
            last = exchange.fetch_order(order_id, sym)
        except Exception:
            pass
        status = (last or {}).get("status") or (last or {}).get("state")
        if status in ("closed", "filled"):
            return last
        time.sleep(poll_interval)
    return last


async def place_twap(
    exchange: Optional[Any],
    symbol: str,
    total_amount: float,
    duration_seconds: float = DEFAULT_TWAP_SLICE_SECONDS,
    slices: int = 5,
    side: str = "buy",
    slice_delay: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Async TWAP: split total_amount into `slices` pieces and place them sequentially.
    When exchange is None this returns simulated filled orders (used in tests)."""
    if slices <= 0:
        slices = 1
    per_slice = float(total_amount) / slices
    slice_delay = (
        slice_delay if slice_delay is not None else (duration_seconds / max(slices, 1))
    )
    results: List[Dict[str, Any]] = []
    for i in range(slices):
        if exchange is None:
            results.append(
                {
                    "id": f"sim-{i}",
                    "status": "closed",
                    "filled": per_slice,
                    "symbol": symbol,
                    "price": None,
                    "simulated": True,
                }
            )
        else:
            if side.lower() == "buy":
                res = safe_market_buy(exchange, symbol, per_slice)
            else:
                res = safe_market_sell(exchange, symbol, per_slice)
            results.append(res)
        if i + 1 < slices:
            await asyncio.sleep(slice_delay)
    return results


def validate(
    self, symbol: str, side: str, amount: float, price: Optional[float]
) -> bool:
    # normalize slashed symbols so "BTC/USDT" == "BTCUSDT"
    if symbol:
        symbol = symbol.replace("/", "")
    # ...existing code...
    return True


__all__ = [
    "init_exchange_from_env",
    "safe_market_buy",
    "safe_market_sell",
    "place_limit_ioc",
    "place_twap",
]
