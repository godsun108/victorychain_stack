import os
import hmac
import time
import base64
import hashlib
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any

# Centralized approval verification for guards
# Token format (base64url): action|expiry|params_json|signature
# signature = HMAC-SHA256(secret, action|expiry|params_json)

APPROVAL_SECRET_ENV = "APPROVAL_SECRET"


def _is_live() -> bool:
    return os.getenv("MODE", "paper").lower() == "live"


def _get_fallback_secret() -> Optional[str]:
    try:
        # Reuse governance prompt hash deterministic fallback if available
        from governance.prompt_version import compute_prompt_hash

        ph = compute_prompt_hash()
        if ph and ph != "unknown":
            return f"dev_fallback::{ph}"
    except Exception:
        pass
    return "dev_fallback::victorychain_local"


def _get_secret() -> Optional[str]:
    env_secret = os.getenv(APPROVAL_SECRET_ENV)
    if env_secret:
        return env_secret
    if _is_live():
        return None
    return _get_fallback_secret()


def _require_secret_or_fail_live() -> None:
    if _is_live() and not os.getenv(APPROVAL_SECRET_ENV):
        raise PermissionError("approval_secret_required_in_live")


@dataclass
class ApprovalResult:
    ok: bool
    reason: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


def _b64url_decode(s: str) -> bytes:
    s = s.replace("-", "+").replace("_", "/")
    pad = "=" * (-len(s) % 4)
    return base64.b64decode(s + pad)


def _json_dumps_sorted(obj: Any) -> str:
    return json.dumps(obj or {}, sort_keys=True, separators=(",", ":"))


def verify(
    token: str,
    action: str,
    params: Optional[Dict[str, Any]] = None,
    now: Optional[int] = None,
) -> ApprovalResult:
    if _is_live() and not os.getenv(APPROVAL_SECRET_ENV):
        return ApprovalResult(False, "approval_secret_required_in_live")
    if not token:
        return ApprovalResult(False, "missing_token")
    secret = _get_secret()
    if not secret:
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


def mint_test_token(
    action: str, ttl_seconds: int = 120, params: Optional[Dict[str, Any]] = None
) -> str:
    _require_secret_or_fail_live()
    secret = _get_secret()
    if not secret:
        raise PermissionError("approval_secret_required_in_live")
    expiry = int(time.time()) + int(ttl_seconds)
    params_json = _json_dumps_sorted(params or {})
    msg = f"{action}|{expiry}|{params_json}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    raw = f"{action}|{expiry}|{params_json}|{sig}".encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")
