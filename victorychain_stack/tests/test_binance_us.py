import pytest
from src.libs.exchange_adapters.binance_us import BinanceUSAdapter, SymbolFilters

@pytest.fixture
def adapter():
    return BinanceUSAdapter()

def test_symbol_validation(adapter):
    assert adapter.filters.validate("BTC/USDT", "buy", 0.001, 50000) is True
    assert adapter.filters.validate("BTCUSDT", "buy", 0.001, 50000) is True
    assert adapter.filters.validate("INVALID/USDT", "buy", 0.001, 50000) is False

def test_snap_and_guard(adapter):
    result, snapped_amount, snapped_price = adapter.client.snap_and_guard(
        adapter.client, "BTC/USDT", "buy", 0.0001, 50000, is_market=False
    )
    assert result is True
    assert snapped_amount > 0

def test_guarded_create_order(adapter):
    response = adapter.guarded_create_order("BTC/USDT", "buy", "market", 0.001)
    assert response is not None
    assert response.get("id") == "paper-buy"

def test_guarded_cancel_order(adapter):
    response = adapter.guarded_cancel_order("some_order_id")
    assert response is not None
    assert response.get("canceled") is True

def test_guarded_withdraw(adapter):
    response = adapter.guarded_withdraw("BTC", 0.01, "some_address")
    assert response is not None
    assert response.get("withdrawal") == "queued"