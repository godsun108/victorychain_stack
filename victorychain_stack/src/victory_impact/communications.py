"""Victory Communications Envelope v1.

Transport-neutral canonical envelope for human, service, and agent messages.
Payload confidentiality is a transport/application concern; private plaintext
must not be placed on a public chain merely because this envelope can hash it.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib, json
from typing import Any


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


@dataclass(frozen=True)
class CommunicationEnvelope:
    message_id: str
    sender: str
    recipient: str
    channel: str
    kind: str
    created_at: datetime
    nonce: str
    payload: dict[str, Any]

    def validate(self, *, now: datetime | None = None, max_future_seconds: int = 60) -> None:
        if not all((self.message_id, self.sender, self.recipient, self.channel, self.kind, self.nonce)):
            raise ValueError("communication fields must be non-empty")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        now = now or datetime.now(timezone.utc)
        if self.created_at > now and (self.created_at - now).total_seconds() > max_future_seconds:
            raise ValueError("message timestamp too far in future")

    def canonical_bytes(self) -> bytes:
        self.validate()
        body = {
            "version": 1,
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "channel": self.channel,
            "kind": self.kind,
            "created_at": self.created_at.isoformat(),
            "nonce": self.nonce,
            "payload": self.payload,
        }
        return _canonical(body)

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


class MessageReplayGuard:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def consume(self, envelope: CommunicationEnvelope) -> None:
        digest = envelope.digest()
        if digest in self._seen:
            raise ValueError("message replay")
        self._seen.add(digest)
