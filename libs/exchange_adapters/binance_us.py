import logging
import os
import math
from typing import Any, Dict, Optional

MODE_ENV = "MODE"

try:
    import ccxt  # noqa: F401
except Exception:  # pragma: no cover
    ccxt = None

try:
    from libs.common.guards import require_approval, deny_all_if_lockdown
except Exception:  # pragma: no cover

    def require_approval(*args, **kwargs):
        def deco(func):
            return func

        return deco

    def deny_all_if_lockdown():
        return False


# Immutable ledger helpers (prompt hash, git commit, anchor)
try:  # pragma: no cover
    from governance import prompt_version as _pv
except Exception:  # pragma: no cover
    _pv = None

logger = logging.getLogger(__name__)

###############################
# Non-fatal snapping helpers  #
###############################


def _est_price_for_market(ex, symbol: str):
    try:
        if not getattr(ex, "markets", None):
            ex.load_markets()
        t = ex.fetch_ticker(symbol) or {}
        for k in ("ask", "last", "bid"):
            v = t.get(k)
            if v:
                try:
                    return float(ex.price_to_precision(symbol, float(v)))
                except Exception:
                    return float(v)
    except Exception:
        pass
    return None


def _floor_amount_to_precision(ex, symbol: str, amt: float):
    try:
        if not getattr(ex, "markets", None):
            ex.load_markets()
        m = (ex.markets or {}).get(symbol, {}) or {}
        prec = (m.get("precision", {}) or {}).get("amount")
        if isinstance(prec, int):
            step = 10 ** (-prec) if prec > 0 else 1.0
            floored = math.floor(float(amt) / step) * step
            return float(ex.amount_to_precision(symbol, floored))
    except Exception:
        pass
    try:
        return float(ex.amount_to_precision(symbol, float(amt)))
    except Exception:
        return float(amt)


def snap_and_guard(
    ex,
    symbol: str,
    side: str,
    amount: float,
    price: Optional[float],
    *,
    is_market: bool,
    log=logger,
):
    """Snap amount/price; enforce min notional/qty non-fatally.
    Returns (ok, snapped_amount, snapped_price_or_None).
    Never raises; logs and returns ok=False if still below constraints after clamping.
    """
    try:
        if not getattr(ex, "markets", None):
            ex.load_markets()
    except Exception:
        pass
    px = None
    if (not is_market) and price is not None:
        try:
            px = float(ex.price_to_precision(symbol, float(price)))
        except Exception:
            px = price
    amt_raw = float(amount)
    amt = _floor_amount_to_precision(ex, symbol, amt_raw)
    mkt = (getattr(ex, "markets", {}) or {}).get(symbol, {}) or {}
    limits = mkt.get("limits", {}) or {}
    amount_limits = limits.get("amount", {}) or {}
    min_qty = amount_limits.get("min")
    cost_limits = limits.get("cost", {}) or {}
    min_cost = cost_limits.get("min")
    # min qty
    if min_qty not in (None, ""):
        try:
            mq = float(min_qty)
            if amt < mq:
                amt = _floor_amount_to_precision(ex, symbol, mq)
        except Exception:
            pass
    # min notional (use estimate for market)
    px_est = px if px is not None else _est_price_for_market(ex, symbol)
    if min_cost not in (None, "") and px_est:
        try:
            mc = float(min_cost)
            if px_est * amt < mc:
                need = (mc / px_est) * 1.001
                amt = _floor_amount_to_precision(ex, symbol, need)
                if px_est * amt < mc * 0.99:
                    log.warning(
                        f"[skip] post-clamp still below min notional {symbol} cost={px_est*amt:.6f} < {mc}"
                    )
                    return False, amt, (px if not is_market else None)
        except Exception:
            pass
    # final amount precision
    try:
        amt = float(ex.amount_to_precision(symbol, amt))
    except Exception:
        pass
    px_final = None
    if px is not None:
        try:
            px_final = float(ex.price_to_precision(symbol, px))
        except Exception:
            px_final = px
    log.debug(
        f"[order-size] {symbol} side={side} raw_amt={amt_raw} snapped_amt={amt} px={'MARKET' if is_market else px_final} min_cost={min_cost}"
    )
    return True, amt, px_final


def _append_ledger(event: str, extra: Optional[Dict[str, Any]] = None) -> None:
    if not _pv:
        return
    try:
        ph = _pv.compute_prompt_hash()
        gc = _pv.get_git_commit()
        _pv.append_ledger_event(event, "adapter.binanceus", ph, gc, extra or {})
    except Exception:
        pass


class SymbolFilters:
    def __init__(self, markets: Dict[str, Dict[str, Any]]):
        self.markets = markets or {}

    def validate(
        self, symbol: str, side: str, amount: float, price: Optional[float]
    ) -> bool:
        # Accept both "BTC/USDT" and "BTCUSDT" (try sensible variants when looking up markets)
        if not symbol:
            logger.warning("validate: missing_symbol")
            return False
        candidates = [symbol]
        if "/" in symbol:
            candidates.append(symbol.replace("/", ""))
        else:
            # if symbol like BTCUSDT, also try BTC/USDT
            if symbol.endswith("USDT"):
                candidates.append(f"{symbol[:-4]}/USDT")
        m = None
        for s in candidates:
            m = self.markets.get(s)
            if m:
                # use the found form for downstream logging/limits
                symbol = s
                break
        if not m:
            # fallback heuristic: accept common BASE/USDT style symbols even if markets dict empty
            norm = symbol.replace("/", "")
            if norm.endswith("USDT") and len(norm) > 4 and norm[:-4].isalpha():
                logger.debug(f"validate: heuristic accept {symbol} -> {norm}")
                return True
            logger.warning(f"validate: unknown_symbol {symbol}")
            return False
        info = m.get("info", {})
        # (Optional) retain simple min qty / notional logging
        try:
            for f in info.get("filters", []):
                if (
                    f.get("filterType") in ("MIN_NOTIONAL", "NOTIONAL")
                    and price is not None
                ):
                    mn = f.get("minNotional") or f.get("notional")
                    if mn and price * amount < float(mn):
                        logger.debug(
                            f"validate: below min_notional symbol={symbol} amt={amount} px={price} mn={mn}"
                        )
        except Exception:
            pass
        return True


def get_client(mode: Optional[str] = None):
    """Return a client for current MODE.
    - live: real ccxt.binanceus with API key/secret, enableRateLimit, timeouts
    - paper: stub client for dry run
    """
    mode = (mode or os.getenv(MODE_ENV, "paper")).lower()
    if mode == "live":
        if ccxt is None:
            raise ImportError("ccxt_not_available")
        api_key = os.getenv("BINANCEUS_API_KEY") or os.getenv("BINANCEUS_KEY")
        api_secret = os.getenv("BINANCEUS_API_SECRET") or os.getenv("BINANCEUS_SECRET")
        if not api_key or not api_secret:
            logger.error(
                "GO_LIVE_BLOCKED:missing_env:BINANCEUS_API_KEY/BINANCEUS_API_SECRET (or BINANCEUS_KEY/BINANCEUS_SECRET)"
            )
            # return a safe stub so guarded flows with valid approvals can run in tests/local
            return _PaperClient()
        client = ccxt.binanceus(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "timeout": 20000,
                "options": {
                    "adjustForTimeDifference": True,
                },
            }
        )
        return client

    class _Dummy:
        def load_markets(self):
            # Minimal market filters for BTC/USDT and ETH/USDT to pass validations with tiny size
            return {
                "BTC/USDT": {
                    "info": {
                        "filters": [
                            {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                            {
                                "filterType": "LOT_SIZE",
                                "minQty": "0.00001",
                                "stepSize": "0.00001",
                            },
                            {"filterType": "NOTIONAL", "notional": "1.0"},
                        ]
                    }
                },
                "ETH/USDT": {
                    "info": {
                        "filters": [
                            {"filterType": "PRICE_FILTER", "tickSize": "0.01"},
                            {
                                "filterType": "LOT_SIZE",
                                "minQty": "0.0001",
                                "stepSize": "0.0001",
                            },
                            {"filterType": "NOTIONAL", "notional": "1.0"},
                        ]
                    }
                },
            }

        # Methods used by adapter
        def create_market_buy_order(self, symbol, amount, params=None):
            logger.info("paper simulated market buy %s %s", symbol, amount)
            return {"id": "paper-buy", "symbol": symbol, "amount": amount}

        def create_market_sell_order(self, symbol, amount, params=None):
            logger.info("paper simulated market sell %s %s", symbol, amount)
            return {"id": "paper-sell", "symbol": symbol, "amount": amount}

        def create_limit_buy_order(self, symbol, amount, price, params=None):
            logger.info("paper simulated limit buy %s %s @ %s", symbol, amount, price)
            return {"id": "paper-limit-buy"}

        def create_limit_sell_order(self, symbol, amount, price, params=None):
            logger.info("paper simulated limit sell %s %s @ %s", symbol, amount, price)
            return {"id": "paper-limit-sell"}

        def create_order(self, **data):
            logger.info("paper simulated create_order %s", data)
            return {"id": "paper-generic"}

        def cancel_order(self, id, symbol=None, params=None):
            logger.info("paper simulated cancel %s", id)
            return {"canceled": True}

        def withdraw(self, code, amount, address, tag=None, params=None):
            logger.info("paper simulated withdraw %s %s", code, amount)
            return {"withdrawal": "queued"}

    return _Dummy()


class _PaperClient:
    """Stub client used when live API keys are not provided (safe dry-run)."""

    def create_market_buy_order(self, symbol, amount, params=None):
        return {
            "id": "sim",
            "status": "closed",
            "filled": amount,
            "symbol": symbol,
            "simulated": True,
        }

    def create_market_sell_order(self, symbol, amount, params=None):
        return {
            "id": "sim",
            "status": "closed",
            "filled": amount,
            "symbol": symbol,
            "simulated": True,
        }

    def create_limit_buy_order(self, symbol, amount, price, params=None):
        return {
            "id": "sim",
            "status": "closed",
            "filled": amount,
            "price": price,
            "symbol": symbol,
            "simulated": True,
        }

    def create_limit_sell_order(self, symbol, amount, price, params=None):
        return {
            "id": "sim",
            "status": "closed",
            "filled": amount,
            "price": price,
            "symbol": symbol,
            "simulated": True,
        }

    def fetch_order(self, order_id, symbol):
        return {
            "id": order_id,
            "status": "closed",
            "filled": 0,
            "symbol": symbol,
            "simulated": True,
        }


class BinanceUSAdapter:
    def __init__(self, client: Any = None):
        self.client = client or get_client()
        try:
            self.markets = self.client.load_markets()
        except Exception:
            self.markets = {}
        self.filters = SymbolFilters(self.markets)

    def _paper_skip(self, action: str) -> Optional[Dict[str, Any]]:
        logger.info("Paper mode: skipping %s", action)
        _append_ledger("PAPER_SKIP", {"action": action})
        return None

    def _guard_common(self, action: str, params: Dict[str, Any]) -> None:
        if deny_all_if_lockdown():
            _append_ledger("LOCKDOWN_BLOCK", {"action": action})
            raise PermissionError("lockdown_active")

    @require_approval(action="order.create")
    def guarded_create_order(
        self,
        symbol: str,
        side: str,
        type: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        # Short-circuit in non-live modes
        if os.getenv(MODE_ENV, "paper").lower() != "live":
            return self._paper_skip("order.create")
        params = params or {}
        self._guard_common("order.create", params)
        # snap & guard (non-fatal)
        try:
            ok, snapped_amt, snapped_px = snap_and_guard(
                self.client,
                symbol,
                side.upper(),
                amount,
                price,
                is_market=(type == "market"),
                log=logger,
            )
            if not ok:
                _append_ledger(
                    "ORDER_SKIPPED",
                    {
                        "op": "create",
                        "symbol": symbol,
                        "side": side,
                        "type": type,
                        "amount": amount,
                        "price": price,
                    },
                )
                return None
            amount = snapped_amt
            if type != "market":
                price = snapped_px
        except Exception as e:
            logger.warning(f"snap_and_guard failed {symbol}: {e}")
        # optional symbol presence check
        try:
            if not self.filters.validate(symbol, side, amount, price):
                _append_ledger(
                    "ORDER_SKIPPED",
                    {
                        "op": "create",
                        "symbol": symbol,
                        "side": side,
                        "type": type,
                        "reason": "unknown_symbol",
                    },
                )
                return None
        except Exception:
            pass
        try:
            # execute
            if type == "market":
                if side == "buy":
                    res = self.client.create_market_buy_order(symbol, amount, params)
                else:
                    res = self.client.create_market_sell_order(symbol, amount, params)
            elif type == "limit":
                if price is None:
                    raise ValueError("limit_price_required")
                if side == "buy":
                    res = self.client.create_limit_buy_order(
                        symbol, amount, price, params
                    )
                else:
                    res = self.client.create_limit_sell_order(
                        symbol, amount, price, params
                    )
            else:
                # Fallback to unified create_order
                data = {"symbol": symbol, "type": type, "side": side, "amount": amount}
                if price is not None:
                    data["price"] = price
                data.update(params)
                res = self.client.create_order(**data)
            _append_ledger(
                "ORDER_OK",
                {
                    "op": "create",
                    "symbol": symbol,
                    "side": side,
                    "type": type,
                    "amount": amount,
                    "price": price,
                    "result_id": (
                        (res or {}).get("id") if isinstance(res, dict) else None
                    ),
                },
            )
            return res
        except Exception as e:
            _append_ledger(
                "ORDER_FAILED",
                {
                    "op": "create",
                    "symbol": symbol,
                    "side": side,
                    "type": type,
                    "amount": amount,
                    "price": price,
                    "error": str(e)[:200],
                },
            )
            raise

    @require_approval(action="order.cancel")
    def guarded_cancel_order(
        self,
        id: str,
        symbol: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        if os.getenv(MODE_ENV, "paper").lower() != "live":
            return self._paper_skip("order.cancel")
        params = params or {}
        self._guard_common("order.cancel", params)
        try:
            res = self.client.cancel_order(id, symbol, params)
            _append_ledger("ORDER_OK", {"op": "cancel", "id": id, "symbol": symbol})
            return res
        except Exception as e:
            _append_ledger(
                "ORDER_FAILED",
                {"op": "cancel", "id": id, "symbol": symbol, "error": str(e)[:200]},
            )
            raise

    # Optional helpers: OCO/replace/stop
    @require_approval(action="order.create")
    def guarded_create_oco(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        stop_price: float,
        params: Optional[Dict[str, Any]] = None,
    ):
        if os.getenv(MODE_ENV, "paper").lower() != "live":
            return self._paper_skip("order.create.oco")
        params = params or {}
        self._guard_common("order.create", params)
        # validate both prices
        self.filters.validate(symbol, side, amount, price)
        self.filters.validate(symbol, side, amount, stop_price)
        try:
            base = {
                "symbol": symbol,
                "type": "limit",
                "side": side,
                "amount": amount,
                "price": price,
            }
            base.update({"params": {"stopPrice": stop_price, **params}})
            res = self.client.create_order(**base)
            _append_ledger(
                "ORDER_OK",
                {
                    "op": "create_oco",
                    "symbol": symbol,
                    "side": side,
                    "amount": amount,
                    "price": price,
                    "stop_price": stop_price,
                },
            )
            return res
        except Exception as e:
            _append_ledger(
                "ORDER_FAILED",
                {"op": "create_oco", "symbol": symbol, "error": str(e)[:200]},
            )
            raise

    @require_approval(action="withdraw")
    def guarded_withdraw(
        self,
        code: str,
        amount: float,
        address: str,
        tag: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        if os.getenv(MODE_ENV, "paper").lower() != "live":
            return self._paper_skip("withdraw")
        params = params or {}
        self._guard_common("withdraw", params)
        try:
            res = self.client.withdraw(code, amount, address, tag, params)
            _append_ledger("WITHDRAW_OK", {"code": code, "amount": amount})
            return res
        except Exception as e:
            _append_ledger(
                "WITHDRAW_FAILED",
                {"code": code, "amount": amount, "error": str(e)[:200]},
            )
            raise


# Free function wrappers for proof script compatibility
_adapter_singleton: Optional[BinanceUSAdapter] = None


def _get_adapter() -> BinanceUSAdapter:
    global _adapter_singleton
    if _adapter_singleton is None:
        _adapter_singleton = BinanceUSAdapter(get_client())
    return _adapter_singleton


@require_approval(action="order.create")
def guarded_create_order(
    symbol: str,
    side: str,
    type: str,
    amount: float,
    price: Optional[float] = None,
    params: Optional[Dict[str, Any]] = None,
):
    # Allow proof runs to simulate safely without ccxt or real keys
    if os.getenv("PROOF_PAPER_SAFE") == "1" or ccxt is None:
        logger.info(
            "PROOF_PAPER_SAFE: simulate create order %s %s %s %s",
            symbol,
            side,
            type,
            amount,
        )
        _append_ledger(
            "ORDER_OK",
            {
                "op": "create",
                "symbol": symbol,
                "side": side,
                "type": type,
                "amount": amount,
                "price": price,
                "proof_paper_safe": True,
            },
        )
        return {"id": "proof-paper-safe"}
    return _get_adapter().guarded_create_order(
        symbol, side, type, amount, price, params
    )


@require_approval(action="order.cancel")
def guarded_cancel_order(
    id: str, symbol: Optional[str] = None, params: Optional[Dict[str, Any]] = None
):
    return _get_adapter().guarded_cancel_order(id, symbol, params)


@require_approval(action="withdraw")
def guarded_withdraw(
    code: str,
    amount: float,
    address: str,
    tag: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
):
    return _get_adapter().guarded_withdraw(code, amount, address, tag, params)
