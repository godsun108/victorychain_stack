from __future__ import annotations

from datetime import UTC, datetime
from typing import Callable

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import WebhookEvent
from .payment_adapters import VUSDAdapter
from .webhook_events import (
    STATUS_DEAD_LETTER,
    STATUS_RETRY_QUEUED,
    mark_processed,
    mark_retry_or_dead_letter,
)
from .webhook_processing import process_webhook_event


def _utc_now() -> datetime:
    return datetime.now(UTC)


def select_retry_candidates(
    db: Session,
    include_dead_letter: bool,
    limit: int,
    event_ids: list[str] | None = None,
) -> list[WebhookEvent]:
    if event_ids:
        return db.scalars(select(WebhookEvent).where(WebhookEvent.id.in_(event_ids))).all()

    statuses = [STATUS_RETRY_QUEUED]
    if include_dead_letter:
        statuses.append(STATUS_DEAD_LETTER)

    now = _utc_now()
    stmt = select(WebhookEvent).where(WebhookEvent.processing_status.in_(statuses))
    if not include_dead_letter:
        stmt = stmt.where(or_(WebhookEvent.next_retry_at.is_(None), WebhookEvent.next_retry_at <= now))

    stmt = stmt.order_by(WebhookEvent.last_seen_at.asc()).limit(max(1, min(limit, 500)))
    return db.scalars(stmt).all()


def run_retry_batch(
    db: Session,
    vusd_adapter: VUSDAdapter,
    include_dead_letter: bool = False,
    limit: int = 100,
    event_ids: list[str] | None = None,
    processor: Callable[[str, dict, VUSDAdapter], None] = process_webhook_event,
) -> dict:
    rows = select_retry_candidates(db, include_dead_letter=include_dead_letter, limit=limit, event_ids=event_ids)

    processed = 0
    queued = 0
    dead_lettered = 0
    failed_ids: list[str] = []

    for row in rows:
        try:
            processor(row.provider, row.payload_json, vusd_adapter)
            mark_processed(db, row)
            processed += 1
        except Exception as exc:
            row = mark_retry_or_dead_letter(db, row, str(exc), settings.webhook_retry_interval_seconds)
            failed_ids.append(row.id)
            if row.processing_status == STATUS_DEAD_LETTER:
                dead_lettered += 1
            else:
                queued += 1

    return {
        "status": "retry_run_complete",
        "attempted": len(rows),
        "processed": processed,
        "queued": queued,
        "dead_lettered": dead_lettered,
        "failed_ids": failed_ids,
    }


def webhook_queue_metrics(db: Session) -> dict:
    now = _utc_now()
    retry_queue_depth = db.scalar(
        select(func.count())
        .select_from(WebhookEvent)
        .where(
            WebhookEvent.processing_status == STATUS_RETRY_QUEUED,
            or_(WebhookEvent.next_retry_at.is_(None), WebhookEvent.next_retry_at <= now),
        )
    ) or 0

    total_retry_queued = db.scalar(
        select(func.count()).select_from(WebhookEvent).where(WebhookEvent.processing_status == STATUS_RETRY_QUEUED)
    ) or 0

    dead_letter_count = db.scalar(
        select(func.count()).select_from(WebhookEvent).where(WebhookEvent.processing_status == STATUS_DEAD_LETTER)
    ) or 0

    oldest_pending = db.scalar(
        select(WebhookEvent)
        .where(WebhookEvent.processing_status == STATUS_RETRY_QUEUED)
        .order_by(WebhookEvent.first_seen_at.asc())
        .limit(1)
    )

    return {
        "retry_queue_depth": int(retry_queue_depth),
        "total_retry_queued": int(total_retry_queued),
        "dead_letter_count": int(dead_letter_count),
        "oldest_pending_event_id": oldest_pending.id if oldest_pending else None,
        "oldest_pending_first_seen_at": oldest_pending.first_seen_at if oldest_pending else None,
    }
