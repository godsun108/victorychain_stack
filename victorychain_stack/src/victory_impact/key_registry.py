"""Victory Key Registry v0.1.

Reference policy for actor-bound public keys. Private keys are never accepted or
stored. The in-memory registry is for tests/research; production requires durable,
transactional storage and authenticated administrative ceremonies.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class PublicKeyRecord:
    key_id: str
    actor: str
    purpose: str
    algorithm: str
    public_key: bytes
    created_at: str
    status: str = "active"
    replaced_by: str | None = None
    revoked_at: str | None = None

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.public_key).hexdigest()


class KeyRegistry:
    def __init__(self) -> None:
        self._keys: dict[str, PublicKeyRecord] = {}

    def register(self, record: PublicKeyRecord) -> None:
        if record.key_id in self._keys:
            raise ValueError("key_id already registered")
        if not record.actor or not record.public_key:
            raise ValueError("actor and public key are required")
        if record.status != "active" or record.replaced_by or record.revoked_at:
            raise ValueError("new key must be active and unreplaced")
        if any(
            k.actor == record.actor and k.purpose == record.purpose and k.status == "active"
            for k in self._keys.values()
        ):
            raise ValueError("actor already has an active key for this purpose")
        self._keys[record.key_id] = record

    def get(self, key_id: str) -> PublicKeyRecord:
        try:
            return self._keys[key_id]
        except KeyError as exc:
            raise ValueError("unknown key") from exc

    def require_active(self, key_id: str, *, actor: str, purpose: str) -> PublicKeyRecord:
        record = self.get(key_id)
        if record.actor != actor:
            raise ValueError("key is not bound to actor")
        if record.purpose != purpose:
            raise ValueError("key purpose mismatch")
        if record.status != "active":
            raise ValueError("key is not active")
        return record

    def rotate(self, old_key_id: str, new_record: PublicKeyRecord, *, at: datetime) -> None:
        old = self.require_active(
            old_key_id, actor=new_record.actor, purpose=new_record.purpose
        )
        if new_record.key_id == old_key_id:
            raise ValueError("rotation requires a new key_id")
        # Retire old first only after all validation that can fail cheaply.
        if new_record.key_id in self._keys:
            raise ValueError("key_id already registered")
        timestamp = _utc(at)
        self._keys[old_key_id] = PublicKeyRecord(
            **{**old.__dict__, "status": "rotated", "replaced_by": new_record.key_id,
               "revoked_at": timestamp}
        )
        self._keys[new_record.key_id] = new_record

    def revoke(self, key_id: str, *, at: datetime) -> None:
        old = self.get(key_id)
        if old.status != "active":
            raise ValueError("only active keys may be revoked")
        self._keys[key_id] = PublicKeyRecord(
            **{**old.__dict__, "status": "revoked", "revoked_at": _utc(at)}
        )


def _utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
