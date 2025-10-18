import os
import time
import json
import base64
import hmac
import hashlib
import tempfile
from pathlib import Path
import pytest

from governance import approvals, vault, prompt_version


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def make_token(
    secret: str, action: str, expiry: int, params: dict | None = None
) -> str:
    params_json = json.dumps(params or {}, sort_keys=True, separators=(",", ":"))
    msg = f"{action}|{expiry}|{params_json}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    raw = f"{action}|{expiry}|{params_json}|{sig}".encode()
    return _b64url_encode(raw)


def test_approvals_verify_success_and_params(tmp_path, monkeypatch):
    secret = "test_secret_123"
    monkeypatch.setenv(approvals.APPROVAL_SECRET_ENV, secret)
    action = "mode.live"
    params = {"component": "unit"}
    expiry = int(time.time()) + 60

    token = make_token(secret, action, expiry, params)
    res = approvals.verify(token, action, params=params)
    assert res.ok, res.reason
    assert res.payload["action"] == action
    assert res.payload["params"] == params


def test_approvals_verify_expired(monkeypatch):
    secret = "test_secret_123"
    monkeypatch.setenv(approvals.APPROVAL_SECRET_ENV, secret)
    action = "mode.live"
    params = {}
    expiry = int(time.time()) - 1

    token = make_token(secret, action, expiry, params)
    res = approvals.verify(token, action)
    assert not res.ok and res.reason == "expired"


def test_vault_lockdown_and_unlock(monkeypatch):
    secret = "unlock_secret_456"
    monkeypatch.setenv(approvals.APPROVAL_SECRET_ENV, secret)

    # Engage lockdown
    vault.lockdown("unit_test")
    assert vault.is_locked()

    # Unlock requires approved token with action vault.unlock
    expiry = int(time.time()) + 60
    token = make_token(secret, "vault.unlock", expiry, {})
    vault.unlock(token)
    assert not vault.is_locked()


def test_prompt_version_ledger_logging(tmp_path, monkeypatch):
    # Redirect ledger path to a temp file by chdir into temp directory
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        prompt_hash = "deadbeef" * 8
        commit = "cafebabe" * 5
        prompt_version.append_ledger_event(
            "PROMPT_ACTIVATED", "unit", prompt_hash, commit, {"k": 1}
        )
        path = Path("trade_ledger.jsonl")
        assert path.exists()
        lines = path.read_text().strip().splitlines()
        assert len(lines) == 1
        rec = json.loads(lines[0])
        assert rec["event"] == "PROMPT_ACTIVATED"
        assert rec["component"] == "unit"
        assert rec["prompt_hash"] == prompt_hash
        assert rec["git_commit"] == commit
        assert rec["k"] == 1
    finally:
        os.chdir(cwd)


def test_live_requires_real_secret(monkeypatch):
    # Ensure MODE=live and no APPROVAL_SECRET -> block with explicit reason
    monkeypatch.setenv("MODE", "live")
    monkeypatch.delenv(approvals.APPROVAL_SECRET_ENV, raising=False)
    res = approvals.verify("anything", "order.create")
    assert not res.ok
    assert res.reason == "approval_secret_required_in_live"
    with pytest.raises(PermissionError):
        approvals.mint_test_token("order.create", ttl_seconds=60)
