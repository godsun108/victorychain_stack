from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Disbursement, DisbursementStatus, WebhookEvent
from .webhook_events import STATUS_DEAD_LETTER, STATUS_RETRY_QUEUED
from .webhook_retry import webhook_queue_metrics


def build_prometheus_metrics(db: Session) -> str:
    queue = webhook_queue_metrics(db)
    webhook_total = db.scalar(select(func.count()).select_from(WebhookEvent)) or 0
    webhook_processed = db.scalar(
        select(func.count()).select_from(WebhookEvent).where(WebhookEvent.processing_status == "processed")
    ) or 0

    disbursements_total = db.scalar(select(func.count()).select_from(Disbursement)) or 0
    disbursements_sent = db.scalar(
        select(func.count()).select_from(Disbursement).where(Disbursement.disbursement_status == DisbursementStatus.SENT)
    ) or 0
    disbursements_queued = db.scalar(
        select(func.count()).select_from(Disbursement).where(Disbursement.disbursement_status == DisbursementStatus.QUEUED)
    ) or 0
    disbursements_canceled = db.scalar(
        select(func.count()).select_from(Disbursement).where(Disbursement.disbursement_status == DisbursementStatus.CANCELED)
    ) or 0
    disbursement_amount_total = db.scalar(select(func.coalesce(func.sum(Disbursement.amount), 0)).select_from(Disbursement)) or 0

    lines = [
        "# HELP webhook_events_total Total webhook events received.",
        "# TYPE webhook_events_total gauge",
        f"webhook_events_total {int(webhook_total)}",
        "# HELP webhook_events_processed_total Total webhook events successfully processed.",
        "# TYPE webhook_events_processed_total gauge",
        f"webhook_events_processed_total {int(webhook_processed)}",
        "# HELP webhook_retry_queue_depth Retry-eligible webhook events ready now.",
        "# TYPE webhook_retry_queue_depth gauge",
        f"webhook_retry_queue_depth {queue['retry_queue_depth']}",
        "# HELP webhook_retry_queued_total Webhook events currently queued for retry.",
        "# TYPE webhook_retry_queued_total gauge",
        f"webhook_retry_queued_total {queue['total_retry_queued']}",
        "# HELP webhook_dead_letter_total Webhook events in dead-letter state.",
        "# TYPE webhook_dead_letter_total gauge",
        f"webhook_dead_letter_total {queue['dead_letter_count']}",
        "# HELP disbursements_total Total disbursements created.",
        "# TYPE disbursements_total gauge",
        f"disbursements_total {int(disbursements_total)}",
        "# HELP disbursements_sent_total Total disbursements with SENT status.",
        "# TYPE disbursements_sent_total gauge",
        f"disbursements_sent_total {int(disbursements_sent)}",
        "# HELP disbursements_queued_total Total disbursements with QUEUED status.",
        "# TYPE disbursements_queued_total gauge",
        f"disbursements_queued_total {int(disbursements_queued)}",
        "# HELP disbursements_canceled_total Total disbursements with CANCELED status.",
        "# TYPE disbursements_canceled_total gauge",
        f"disbursements_canceled_total {int(disbursements_canceled)}",
        "# HELP disbursement_amount_total Total disbursement amount across all currencies.",
        "# TYPE disbursement_amount_total gauge",
        f"disbursement_amount_total {float(disbursement_amount_total)}",
        "# HELP webhook_status_count_count Webhook count by processing status.",
        "# TYPE webhook_status_count_count gauge",
    ]

    for status in ["received", STATUS_RETRY_QUEUED, STATUS_DEAD_LETTER, "processed"]:
        count = db.scalar(
            select(func.count()).select_from(WebhookEvent).where(WebhookEvent.processing_status == status)
        ) or 0
        lines.append(f'webhook_status_count_count{{status="{status}"}} {int(count)}')

    return "\n".join(lines) + "\n"
