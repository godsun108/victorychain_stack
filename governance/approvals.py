import os
import hmac
import time
import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Simple HMAC-based approval token validation
# Token format (base64url): action|expiry|params_json|signature
# signature = HMAC-SHA256(secret, action|expiry|params_json)

APPROVAL_SECRET_ENV = "APPROVAL_SECRET"


def _is_live() -> bool:
    return os.getenv("MODE", "paper").lower() == "live"


def _get_fallback_secret() -> Optional[str]:
    """Provide a stable, local-only fallback secret if env var is missing.
    Derived from the current prompt hash to remain consistent across processes.
    Used ONLY when not in live mode.
    """
    try:
        from . import prompt_version as _pv

        ph = _pv.compute_prompt_hash()
        if ph and ph != "unknown":
            return f"dev_fallback::{ph}"
    except Exception:
        pass
    # Last resort constant; acceptable for local paper-mode only
    return "dev_fallback::victorychain_local"


def _require_secret_or_fail_live() -> None:
    if _is_live() and not os.getenv(APPROVAL_SECRET_ENV):
        raise PermissionError("approval_secret_required_in_live")


def _get_secret() -> Optional[str]:
    env_secret = os.getenv(APPROVAL_SECRET_ENV)
    if env_secret:
        return env_secret
    # No env secret: only allow fallback when not live
    if _is_live():
        return None
    return _get_fallback_secret()


@dataclass
class ApprovalResult:
    ok: bool
    reason: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


def _b64url_decode(s: str) -> bytes:
    s = s.replace("-", "+").replace("_", "/")
    pad = "=" * (-len(s) % 4)
    return base64.b64decode(s + pad)


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _json_dumps_sorted(obj: Any) -> str:
    """Stable, compact JSON used for signing/verification."""
    return json.dumps(obj or {}, sort_keys=True, separators=(",", ":"))


def verify(
    token: str,
    action: str,
    params: Optional[Dict[str, Any]] = None,
    now: Optional[int] = None,
) -> ApprovalResult:
    """Verify an approval token for a given action.
    Live mode: requires APPROVAL_SECRET in environment (no fallback allowed).
    Paper/CI: allows deterministic fallback secret derived from prompt hash.
    If params is provided, it must match the params embedded in the token.
    """
    # Enforce live rule first
    if _is_live() and not os.getenv(APPROVAL_SECRET_ENV):
        return ApprovalResult(False, "approval_secret_required_in_live")
    if not token:
        return ApprovalResult(False, "missing_token")
    secret = _get_secret()
    if not secret:
        # In live, this indicates missing secret; in paper, should not happen
        return ApprovalResult(False, "approval_secret_required_in_live")
    try:
        raw = _b64url_decode(token).decode()
        parts = raw.split("|", 3)
        if len(parts) != 4:
            return ApprovalResult(False, "malformed_token")
        tok_action, tok_expiry, tok_params_json, tok_sig = parts
        if tok_action != action:
            return ApprovalResult(False, "action_mismatch")
        expiry = int(tok_expiry)
        now_i = int(now if now is not None else time.time())
        if now_i > expiry:
            return ApprovalResult(False, "expired")
        msg = f"{tok_action}|{expiry}|{tok_params_json}".encode()
        calc_sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc_sig, tok_sig):
            return ApprovalResult(False, "invalid_signature")
        # Validate params if provided
        embedded_params = json.loads(tok_params_json or "{}")
        if params is not None:
            if _json_dumps_sorted(embedded_params) != _json_dumps_sorted(params):
                return ApprovalResult(False, "params_mismatch")
        return ApprovalResult(
            True,
            payload={
                "action": tok_action,
                "expiry": expiry,
                "params": embedded_params,
            },
        )
    except Exception as e:
        return ApprovalResult(False, f"error:{e}")


def require(token: str, action: str, params: Optional[Dict[str, Any]] = None) -> None:
    res = verify(token, action, params=params)
    if not res.ok:
        raise PermissionError(f"approval_failed:{res.reason}")


def mint_test_token(
    action: str, ttl_seconds: int = 120, params: Optional[Dict[str, Any]] = None
) -> str:
    """Mint a short-lived approval token for tests and paper-mode proofs.
    Live mode requires a real env secret; paper/CI may use deterministic fallback.
    """
    # Enforce no fallback in live
    _require_secret_or_fail_live()
    secret = _get_secret()
    if not secret:
        # In paper/CI this should not occur; be explicit
        raise PermissionError("approval_secret_required_in_live")
    expiry = int(time.time()) + int(ttl_seconds)
    params_json = _json_dumps_sorted(params or {})
    msg = f"{action}|{expiry}|{params_json}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    raw = f"{action}|{expiry}|{params_json}|{sig}".encode()
    return _b64url_encode(raw)
