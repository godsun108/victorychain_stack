"""Victory Identity v0.1: canonical, replay-resistant authorization challenges.

This layer binds authenticated intent to an actor, action and resource. It does
not custody keys or grant funds authority. Signature verification adapters live
outside this policy module.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AuthorizationChallenge:
    version: int
    challenge_id: str
    actor: str
    action: str
    resource: str
    nonce: str
    issued_at: str
    expires_at: str
    suite_id: str = "victory-hybrid-v1"

    def canonical_bytes(self) -> bytes:
        body = {
            "action": self.action,
            "actor": self.actor,
            "challenge_id": self.challenge_id,
            "expires_at": self.expires_at,
            "issued_at": self.issued_at,
            "nonce": self.nonce,
            "resource": self.resource,
            "suite_id": self.suite_id,
            "version": self.version,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def validate(self, *, now: datetime) -> None:
        if self.version != 1:
            raise ValueError("unsupported challenge version")
        for value in (self.challenge_id, self.actor, self.action, self.resource, self.nonce):
            if not value or not value.strip():
                raise ValueError("challenge fields must be non-empty")
        issued = _parse_utc(self.issued_at)
        expires = _parse_utc(self.expires_at)
        current = now.astimezone(timezone.utc)
        if expires <= issued:
            raise ValueError("challenge expiry must follow issuance")
        if current < issued:
            raise ValueError("challenge is not active yet")
        if current >= expires:
            raise ValueError("challenge expired")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


class ReplayGuard:
    """Single-process reference guard; production storage must be atomic/shared."""

    def __init__(self) -> None:
        self._consumed: set[str] = set()

    def consume(self, challenge: AuthorizationChallenge, *, now: datetime) -> None:
        challenge.validate(now=now)
        key = challenge.digest()
        if key in self._consumed:
            raise ValueError("challenge already consumed")
        self._consumed.add(key)


def identity_manifest() -> dict:
    return {
        "version": "0.1",
        "authorization_payload": "actor+action+resource+nonce+issued_at+expires_at+suite",
        "default_suite": "victory-hybrid-v1",
        "replay_policy": "single_use_challenge",
        "server_key_custody": "none",
        "funds_authority": "disabled",
        "soul_key_authority": "none",
    }
