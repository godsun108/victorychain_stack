from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..models import WebhookEvent

STATUS_RECEIVED = "received"
STATUS_PROCESSED = "processed"
STATUS_RETRY_QUEUED = "retry_queued"
STATUS_DEAD_LETTER = "dead_letter"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def register_webhook_event(
    db: Session,
    provider: str,
    provider_event_id: str,
    event_type: str | None,
    payload_json: dict,
    max_retries: int = 3,
) -> tuple[WebhookEvent, bool]:
    existing = db.scalar(
        select(WebhookEvent).where(
            WebhookEvent.provider == provider,
            WebhookEvent.provider_event_id == provider_event_id,
        )
    )
    if existing:
        existing.delivery_count += 1
        existing.last_seen_at = _utc_now()
        existing.updated_at = _utc_now()
        db.commit()
        db.refresh(existing)
        return existing, True

    created = WebhookEvent(
        provider=provider,
        provider_event_id=provider_event_id,
        event_type=event_type,
        payload_json=payload_json,
        delivery_count=1,
        processed=False,
        processing_status=STATUS_RECEIVED,
        max_retries=max(1, max_retries),
    )
    db.add(created)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        duplicate = db.scalar(
            select(WebhookEvent).where(
                WebhookEvent.provider == provider,
                WebhookEvent.provider_event_id == provider_event_id,
            )
        )
        if not duplicate:
            raise
        duplicate.delivery_count += 1
        duplicate.last_seen_at = _utc_now()
        duplicate.updated_at = _utc_now()
        db.commit()
        db.refresh(duplicate)
        return duplicate, True

    db.refresh(created)
    return created, False


def mark_processed(db: Session, event: WebhookEvent) -> WebhookEvent:
    now = _utc_now()
    event.processed = True
    event.processing_status = STATUS_PROCESSED
    event.last_error = None
    event.next_retry_at = None
    event.processed_at = now
    if event.remediation_status in {"open", "in_progress"}:
        event.remediation_status = "resolved"
        event.remediated_at = now
    event.updated_at = now
    db.commit()
    db.refresh(event)
    return event


def compute_retry_delay_seconds(
    retry_count: int,
    base_interval_seconds: int,
    max_delay_seconds: int,
    jitter_ratio: float,
) -> int:
    retry_count = max(1, retry_count)
    base_interval_seconds = max(1, base_interval_seconds)
    max_delay_seconds = max(base_interval_seconds, max_delay_seconds)
    jitter_ratio = max(0.0, min(1.0, jitter_ratio))

    exponential = min(base_interval_seconds * (2 ** (retry_count - 1)), max_delay_seconds)
    jitter_min = 1.0 - jitter_ratio
    jitter_max = 1.0 + jitter_ratio
    jitter_multiplier = random.uniform(jitter_min, jitter_max)
    delay = int(exponential * jitter_multiplier)
    return max(1, min(delay, max_delay_seconds))


def mark_retry_or_dead_letter(
    db: Session,
    event: WebhookEvent,
    error_message: str | None,
    retry_interval_seconds: int | None = None,
) -> WebhookEvent:
    now = _utc_now()
    event.retry_count += 1
    event.processed = False
    if error_message:
        event.last_error = error_message[:2000]
    event.updated_at = now

    if event.retry_count >= event.max_retries:
        event.processing_status = STATUS_DEAD_LETTER
        event.dead_lettered_at = now
        if event.remediation_status == "none":
            event.remediation_status = "open"
        event.next_retry_at = None
    else:
        event.processing_status = STATUS_RETRY_QUEUED
        interval = retry_interval_seconds if retry_interval_seconds is not None else settings.webhook_retry_interval_seconds
        delay = compute_retry_delay_seconds(
            retry_count=event.retry_count,
            base_interval_seconds=interval,
            max_delay_seconds=settings.webhook_retry_max_delay_seconds,
            jitter_ratio=settings.webhook_retry_jitter_ratio,
        )
        event.next_retry_at = now + timedelta(seconds=delay)

    db.commit()
    db.refresh(event)
    return event


def list_webhook_events(
    db: Session,
    provider: str | None = None,
    processing_status: str | None = None,
    remediation_status: str | None = None,
    limit: int = 100,
) -> list[WebhookEvent]:
    stmt = select(WebhookEvent)
    if provider:
        stmt = stmt.where(WebhookEvent.provider == provider)
    if processing_status:
        stmt = stmt.where(WebhookEvent.processing_status == processing_status)
    if remediation_status:
        stmt = stmt.where(WebhookEvent.remediation_status == remediation_status)
    stmt = stmt.order_by(WebhookEvent.last_seen_at.desc()).limit(max(1, min(limit, 500)))
    return db.scalars(stmt).all()
