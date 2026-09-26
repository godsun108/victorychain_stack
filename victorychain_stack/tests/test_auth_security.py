import pytest
from fastapi import HTTPException

from src.victory_impact.security import current_role, require_role, token_fingerprint


def test_auth_fails_closed_without_header(monkeypatch):
    monkeypatch.delenv("VICTORY_ROLE_TOKENS", raising=False)
    with pytest.raises(HTTPException) as exc:
        current_role(None)
    assert exc.value.status_code == 401


def test_auth_fails_closed_without_server_configuration(monkeypatch):
    monkeypatch.delenv("VICTORY_ROLE_TOKENS", raising=False)
    with pytest.raises(HTTPException) as exc:
        current_role("anything")
    assert exc.value.status_code == 401


def test_role_tokens_are_runtime_only(monkeypatch):
    monkeypatch.setenv("VICTORY_ROLE_TOKENS", "alpha:donor,bravo:admin")
    assert current_role("alpha") == "donor"
    assert current_role("bravo") == "admin"
    with pytest.raises(HTTPException):
        current_role("donor-token")


def test_invalid_role_configuration_is_rejected(monkeypatch):
    monkeypatch.setenv("VICTORY_ROLE_TOKENS", "alpha:superuser")
    with pytest.raises(RuntimeError):
        current_role("alpha")


def test_unknown_required_role_is_rejected():
    with pytest.raises(ValueError):
        require_role("root")


def test_token_fingerprint_does_not_expose_token():
    token = "very-secret-value"
    fingerprint = token_fingerprint(token)
    assert token not in fingerprint
    assert len(fingerprint) == 16
