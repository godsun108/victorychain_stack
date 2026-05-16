from dataclasses import dataclass


@dataclass
class SymbolFilters:
    min_amount: float = 0.000001
    min_price: float = 0.01

    def validate(self, symbol: str, side: str, amount: float, price: float) -> bool:
        normalized = symbol.replace("/", "")
        is_supported = normalized in {"BTCUSDT", "ETHUSDT", "SOLUSDT"}
        if not is_supported:
            return False
        if side not in {"buy", "sell"}:
            return False
        return amount >= self.min_amount and (price is None or price >= self.min_price)


class MockCCXTClient:
    def snap_and_guard(self, _client, symbol: str, side: str, amount: float, price: float, is_market: bool = False):
        safe_amount = max(amount, 0.000001)
        safe_price = None if is_market else max(price, 0.01)
        return True, safe_amount, safe_price


class BinanceUSAdapter:
    def __init__(self):
        self.filters = SymbolFilters()
        self.client = MockCCXTClient()

    def guarded_create_order(self, symbol: str, side: str, order_type: str, amount: float, price: float | None = None):
        if not self.filters.validate(symbol, side, amount, price or 1.0):
            raise ValueError("Invalid order")
        return {
            "id": f"paper-{side}",
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "amount": amount,
            "price": price,
        }

    def guarded_cancel_order(self, order_id: str):
        return {"id": order_id, "canceled": True}

    def guarded_withdraw(self, asset: str, amount: float, address: str):
        return {"asset": asset, "amount": amount, "address": address, "withdrawal": "queued"}
