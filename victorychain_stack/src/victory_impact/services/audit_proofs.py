from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Disbursement, Receipt, WebhookEvent


def _iso(value):
    if value is None:
        return None
    return value.astimezone(UTC).isoformat()


def _canonical_json(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _sign(secret: str, canonical_payload: str) -> str:
    return hmac.new(secret.encode("utf-8"), canonical_payload.encode("utf-8"), hashlib.sha256).hexdigest()


def build_audit_proof(db: Session, entity_type: str, entity_id: str, secret: str) -> dict:
    generated_at = datetime.now(UTC).isoformat()
    if entity_type == "webhook_event":
        row = db.scalar(select(WebhookEvent).where(WebhookEvent.id == entity_id))
        if not row:
            raise ValueError("webhook event not found")
        payload = {
            "entity_type": "webhook_event",
            "entity_id": row.id,
            "provider": row.provider,
            "provider_event_id": row.provider_event_id,
            "event_type": row.event_type,
            "delivery_count": row.delivery_count,
            "processing_status": row.processing_status,
            "retry_count": row.retry_count,
            "max_retries": row.max_retries,
            "first_seen_at": _iso(row.first_seen_at),
            "last_seen_at": _iso(row.last_seen_at),
            "processed_at": _iso(row.processed_at),
            "dead_lettered_at": _iso(row.dead_lettered_at),
        }
    elif entity_type == "disbursement":
        row = db.scalar(select(Disbursement).where(Disbursement.id == entity_id))
        if not row:
            raise ValueError("disbursement not found")
        receipt = db.scalar(select(Receipt).where(Receipt.disbursement_id == row.id))
        payload = {
            "entity_type": "disbursement",
            "entity_id": row.id,
            "beneficiary_request_id": row.beneficiary_request_id,
            "category_id": row.category_id,
            "amount": str(row.amount),
            "currency": row.currency,
            "treasury_wallet": row.treasury_wallet,
            "destination_reference": row.destination_reference,
            "disbursement_status": row.disbursement_status.value,
            "tx_hash": row.tx_hash,
            "created_at": _iso(row.created_at),
            "receipt_number": receipt.receipt_number if receipt else None,
        }
    else:
        raise ValueError("unsupported entity_type")

    canonical_payload = _canonical_json(payload)
    return {
        "proof_version": "hmac-sha256-v1",
        "entity_type": payload["entity_type"],
        "entity_id": payload["entity_id"],
        "generated_at": generated_at,
        "canonical_payload": canonical_payload,
        "signature_hex": _sign(secret, canonical_payload),
    }
