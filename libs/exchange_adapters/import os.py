import os
import types
import pytest
from libs.exchange_adapters.binance_us import get_client

# python

# Absolute import of the function to test (namespace package)
import libs.exchange_adapters.binance_us as binance_module


def test_get_client_default_returns_dummy(monkeypatch):
    # Ensure default MODE is paper by removing MODE env if present
    monkeypatch.delenv(binance_module.MODE_ENV, raising=False)
    client = get_client()  # default should return the internal _Dummy instance
    assert hasattr(client, "create_market_buy_order")
    res = client.create_market_buy_order("BTC/USDT", 0.001)
    assert isinstance(res, dict)
    assert res.get("id") == "paper-buy"


def test_get_client_live_raises_if_no_ccxt(monkeypatch):
    # Force live mode and ensure ccxt is None to trigger ImportError
    monkeypatch.setenv(binance_module.MODE_ENV, "live")
    monkeypatch.setattr(binance_module, "ccxt", None)
    with pytest.raises(ImportError):
        get_client()


def test_get_client_live_without_keys_returns_paperclient(monkeypatch):
    # Force live mode and set ccxt to a non-None sentinel so the api-key path is taken
    monkeypatch.setenv(binance_module.MODE_ENV, "live")
    monkeypatch.setattr(binance_module, "ccxt", object())
    # Ensure API env vars are absent
    monkeypatch.delenv("BINANCEUS_API_KEY", raising=False)
    monkeypatch.delenv("BINANCEUS_KEY", raising=False)
    monkeypatch.delenv("BINANCEUS_API_SECRET", raising=False)
    monkeypatch.delenv("BINANCEUS_SECRET", raising=False)

    client = get_client()
    # _PaperClient create_market_buy_order returns dict with simulated True
    assert hasattr(client, "create_market_buy_order")
    res = client.create_market_buy_order("BTC/USDT", 0.001)
    assert isinstance(res, dict)
    assert res.get("simulated", False) is True


def test_get_client_live_with_keys_uses_ccxt_factory(monkeypatch):
    # Force live mode and provide fake ccxt.binanceus factory
    monkeypatch.setenv(binance_module.MODE_ENV, "live")

    def fake_binanceus(cfg):
        # return an identifiable sentinel object
        return {"_sentinel_client": True, "cfg": cfg}

    fake_ccxt = types.SimpleNamespace(binanceus=fake_binanceus)
    monkeypatch.setattr(binance_module, "ccxt", fake_ccxt)

    # Provide API keys so the code uses the ccxt.binanceus factory
    monkeypatch.setenv("BINANCEUS_API_KEY", "fakekey")
    monkeypatch.setenv("BINANCEUS_API_SECRET", "fakesecret")

    client = get_client()
    assert isinstance(client, dict)
    assert client.get("_sentinel_client") is Trueimport os
import types
import math
import pytest

# python

from libs.exchange_adapters.binance_us import (
    get_client,
    _PaperClient,
    guarded_create_order,
    SymbolFilters,
    snap_and_guard,
)

def test_get_client_paper_and_dummy_methods():
    client = get_client('paper')
    # ensure load_markets exists and returns expected sample market keys
    assert hasattr(client, 'load_markets')
    markets = client.load_markets()
    assert isinstance(markets, dict)
    assert 'BTC/USDT' in markets
    # ensure paper client implements at least one order method
    assert hasattr(client, 'create_market_buy_order')

def test_paper_client_simulated_orders():
    p = _PaperClient()
    r1 = p.create_market_buy_order('BTC/USDT', 0.001)
    assert isinstance(r1, dict)
    assert r1.get('simulated', False) is True
    assert r1.get('status') in ('closed',)
    r2 = p.create_limit_buy_order('BTC/USDT', 0.001, 30000.0)
    assert isinstance(r2, dict)
    assert r2.get('simulated', False) is True
    f = p.fetch_order('anyid', 'BTC/USDT')
    assert isinstance(f, dict)
    assert f.get('status') in ('closed',)

def test_guarded_create_order_proof_paper_safe_env(monkeypatch):
    # Ensure PROOF_PAPER_SAFE is set so guarded_create_order free function short-circuits
    monkeypatch.setenv('PROOF_PAPER_SAFE', '1')
    res = guarded_create_order('BTC/USDT', 'buy', 'market', 0.001)
    assert isinstance(res, dict)
    assert res.get('id') == 'proof-paper-safe'

def test_symbolfilters_validate_known_and_heuristic():
    markets = {
        'BTC/USDT': {
            'info': {
                'filters': [
                    {'filterType': 'PRICE_FILTER', 'tickSize': '0.01'},
                    {'filterType': 'LOT_SIZE', 'minQty': '0.00001', 'stepSize': '0.00001'},
                    {'filterType': 'NOTIONAL', 'notional': '1.0'},
                ]
            }
        }
    }
    f = SymbolFilters(markets)
    # known canonical form
    assert f.validate('BTC/USDT', 'buy', 0.001, 30000.0) is True
    # accept without slash by candidate generation
    assert f.validate('BTCUSDT', 'buy', 0.001, 30000.0) is True

    # empty markets should still accept heuristic style symbol like ABCUSDT
    f2 = SymbolFilters({})
    assert f2.validate('ABCUSDT', 'buy', 0.1, None) is True
    # unknown non-usdt symbol should be rejected
    assert f2.validate('UNKNOWN/XXX', 'buy', 1.0, None) is False

def test_snap_and_guard_respects_min_qty_and_min_cost():
    # Build fake exchange
    class FakeEx:
        def __init__(self):
            self.markets = {
                'BTC/USDT': {
                    'precision': {'amount': 6},
                    'limits': {
                        'amount': {'min': '0.001'},
                        'cost': {'min': '10'}
                    }
                }
            }
        def load_markets(self):
            return self.markets
        def price_to_precision(self, symbol, price):
            # mimic ccxt behaviour: format to 2 decimals for price
            return f"{float(price):.2f}"
        def amount_to_precision(self, symbol, amount):
            # format to 6 decimals
            return f"{float(amount):.6f}"
        def fetch_ticker(self, symbol):
            return {'ask': 5000.0, 'last': 5000.0, 'bid': 4999.0}

    ex = FakeEx()
    # Amount below min_qty and below min_cost given price 5000 -> min cost 10 requires amt >= 0.002
    ok, snapped_amt, snapped_px = snap_and_guard(ex, 'BTC/USDT', 'buy', 0.0001, 5000.0, is_market=False, log=__import__('logging').getLogger())
    assert ok is True
    # snapped amount must be at least the declared minimum (0.001) or satisfy min cost (=>0.002)
    assert isinstance(snapped_amt, float)
    assert snapped_amt >= 0.001
    # price snapped should be float
    assert isinstance(snapped_px, float)