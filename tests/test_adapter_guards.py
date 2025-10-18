import os
import time
import pytest

from governance import approvals as gov_approvals, vault
from libs.common import approvals as central
from libs.exchange_adapters.binance_us import guarded_create_order


def setup_module(module):
    # Ensure a secret for token minting
    os.environ["APPROVAL_SECRET"] = "test_secret_guard_123"
    # Ensure not locked
    try:
        vault.unlock(gov_approvals.mint_test_token("vault.unlock", ttl_seconds=120))
    except Exception:
        pass


def test_lockdown_blocks_live_order(monkeypatch):
    vault.lockdown("unit_lock")
    os.environ["MODE"] = "live"
    os.environ["APPROVAL_TOKEN"] = gov_approvals.mint_test_token(
        "order.create", ttl_seconds=60
    )
    with pytest.raises(PermissionError):
        guarded_create_order("BTC/USDT", "buy", "market", 0.0001)
    # clear
    token = gov_approvals.mint_test_token("vault.unlock", ttl_seconds=60)
    vault.unlock(token)


def test_approval_required_for_live(monkeypatch):
    os.environ["MODE"] = "live"
    if "APPROVAL_TOKEN" in os.environ:
        del os.environ["APPROVAL_TOKEN"]
    with pytest.raises(PermissionError):
        guarded_create_order("BTC/USDT", "buy", "market", 0.0001)


def test_valid_token_allows_paper_safe(monkeypatch):
    os.environ["MODE"] = "live"
    os.environ["APPROVAL_TOKEN"] = central.mint_test_token(
        "order.create", ttl_seconds=60
    )
    res = guarded_create_order("BTC/USDT", "buy", "market", 0.0001)
    assert res is not None
