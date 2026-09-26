from __future__ import annotations

import hashlib
import hmac
import os
from typing import Callable

from fastapi import Depends, Header, HTTPException


ALLOWED_ROLES = frozenset({"donor", "admin", "board", "compliance"})
PRIVILEGED_ROLES = frozenset({"admin", "board", "compliance"})


def _configured_tokens() -> dict[str, str]:
    """Load opaque demo/API tokens from process environment only.

    Format: VICTORY_ROLE_TOKENS="tokenA:donor,tokenB:admin"
    No credentials are committed to source. Production should replace this
    adapter with a mature identity/session system or verified wallet challenge.
    """
    raw = os.getenv("VICTORY_ROLE_TOKENS", "")
    tokens: dict[str, str] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        token, sep, role = item.partition(":")
        token, role = token.strip(), role.strip().lower()
        if not sep or not token or role not in ALLOWED_ROLES:
            raise RuntimeError("Invalid VICTORY_ROLE_TOKENS configuration")
        if token in tokens:
            raise RuntimeError("Duplicate Victory role token")
        tokens[token] = role
    return tokens


def _lookup_role(candidate: str, configured: dict[str, str]) -> str | None:
    # Constant-time comparison avoids leaking which configured token matched.
    for token, role in configured.items():
        if hmac.compare_digest(candidate, token):
            return role
    return None


def current_role(x_api_token: str | None = Header(default=None)) -> str:
    """Fail closed: no header, no configured tokens, or bad token => 401."""
    if not x_api_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    configured = _configured_tokens()
    if not configured:
        raise HTTPException(status_code=401, detail="Authentication is not configured")
    role = _lookup_role(x_api_token, configured)
    if not role:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return role


def require_role(*allowed_roles: str) -> Callable[[str], str]:
    unknown = set(allowed_roles) - ALLOWED_ROLES
    if unknown:
        raise ValueError(f"Unknown roles: {sorted(unknown)}")

    def checker(role: str = Depends(current_role)) -> str:  # pragma: no cover
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return role

    return checker


def token_fingerprint(token: str) -> str:
    """Safe identifier for audit logs; never log the credential itself."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
