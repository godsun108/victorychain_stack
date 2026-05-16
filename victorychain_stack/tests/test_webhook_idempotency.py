from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from src.victory_impact.models import Base, WebhookEvent
from src.victory_impact.routers import webhooks


class DummyRequest:
    def __init__(self, payload: dict):
        self._payload = payload

    async def body(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def _build_db(db_file: Path) -> Session:
    engine = create_engine(
        f"sqlite+pysqlite:///{db_file}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def test_stripe_webhook_duplicate_is_ignored(tmp_path, monkeypatch):
    db = _build_db(tmp_path / "stripe-idempotency.db")
    monkeypatch.setattr(
        webhooks.stripe_sdk_parser,
        "parse_event",
        lambda payload_bytes, stripe_signature: {"id": "evt_duplicate_1", "type": "payment_intent.succeeded"},
    )

    request = DummyRequest({"id": "evt_duplicate_1", "type": "payment_intent.succeeded"})
    first = asyncio.run(webhooks.stripe_webhook(request, "testsig", db))
    second = asyncio.run(webhooks.stripe_webhook(request, "testsig", db))

    assert first["status"] == "accepted"
    assert first["event_id"] == "evt_duplicate_1"
    assert second["status"] == "duplicate_ignored"
    assert second["delivery_count"] == 2

    event = db.scalar(
        select(WebhookEvent).where(
            WebhookEvent.provider == "stripe",
            WebhookEvent.provider_event_id == "evt_duplicate_1",
        )
    )
    assert event is not None
    assert event.delivery_count == 2
    db.close()


def test_vusd_webhook_duplicate_is_ignored(tmp_path, monkeypatch):
    db = _build_db(tmp_path / "vusd-idempotency.db")
    monkeypatch.setattr(
        webhooks.vusd_adapter,
        "verify_vusd_transfer_event",
        lambda payload: {"status": "verified", "event_id": payload.get("event_id"), "verification": {"ok": True}},
    )

    payload = {"event_id": "vusd-evt-1", "tx_hash": "0xabc", "contract_address": "0x123"}
    first = webhooks.vusd_webhook(payload, db)
    second = webhooks.vusd_webhook(payload, db)

    assert first["status"] == "accepted"
    assert second["status"] == "duplicate_ignored"
    assert second["delivery_count"] == 2

    event = db.scalar(
        select(WebhookEvent).where(
            WebhookEvent.provider == "vusd",
            WebhookEvent.provider_event_id == "vusd-evt-1",
        )
    )
    assert event is not None
    assert event.delivery_count == 2
    db.close()
