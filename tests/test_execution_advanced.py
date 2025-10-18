import asyncio
import time
from unittest import mock
import pytest

from src.victory_bot import execution as execution_module


@pytest.mark.asyncio
async def test_place_twap_simulated():
    # simulated mode (exchange=None) should return list of simulated slices
    orders = await execution_module.place_twap(
        None, "BTCUSDT", total_amount=0.006, duration_seconds=1.0, slices=3, side="buy"
    )
    assert isinstance(orders, list)
    assert len(orders) == 3
    assert all(o is not None for o in orders)


def test_place_limit_ioc_simulated():
    res = execution_module.place_limit_ioc(
        None, "BTCUSDT", amount=0.001, price=30000.0, side="buy"
    )
    assert res is not None
    assert res.get("simulated", False) is True


def test_safe_market_buy_and_poll_with_mock_exchange():
    # mock exchange that returns an order id and later a filled order
    exchange = mock.Mock()
    # create_market_buy_order returns an order with id
    exchange.create_market_buy_order.return_value = {"id": "order123"}
    # fetch_order returns 'open' then 'closed'
    states = [{"status": "open"}, {"status": "closed", "average": 40000.0}]

    def fetch_order_side(order_id, symbol):
        return states.pop(0)

    exchange.fetch_order.side_effect = lambda oid, sym: fetch_order_side(oid, sym)
    order = execution_module.safe_market_buy(exchange, "BTCUSDT", 0.001, max_retries=1)
    # order should be a dict from poll (closed)
    assert order is not None
    assert order.get("status") in ("closed", "filled") or "average" in order


def test_place_limit_ioc_with_mock_exchange_polls_closed():
    exchange = mock.Mock()
    # create_limit_buy_order returns order with id
    exchange.create_limit_buy_order.return_value = {"id": "ioc123"}
    # fetch_order returns closed immediately
    exchange.fetch_order.return_value = {
        "id": "ioc123",
        "status": "closed",
        "price": 30000.0,
    }
    res = execution_module.place_limit_ioc(
        exchange, "BTCUSDT", amount=0.001, price=30000.0, side="buy"
    )
    assert res is not None
    assert (
        res.get("status") in ("closed", "filled") or res.get("simulated", False) is True
    )
