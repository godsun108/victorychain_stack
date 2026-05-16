import hashlib
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..services.payment_adapters import EVMIndexerAdapter, StripeSDKEventParser, StripeWebhookVerifier, VUSDAdapter
from ..services.webhook_processing import process_stripe_payload, process_vusd_payload
from ..services.webhook_events import (
    STATUS_DEAD_LETTER,
    mark_processed,
    mark_retry_or_dead_letter,
    register_webhook_event,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

indexer_adapter = EVMIndexerAdapter(settings.evm_rpc_url, settings.evm_required_confirmations)
stripe_verifier = StripeWebhookVerifier(settings.stripe_webhook_secret)
stripe_sdk_parser = StripeSDKEventParser(settings.stripe_webhook_secret)
vusd_adapter = VUSDAdapter(indexer_adapter, settings.vusd_contract_address)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    if settings.sovereign_mode and not settings.enable_external_stripe_webhooks:
        raise HTTPException(
            status_code=403,
            detail="stripe webhook endpoint is disabled in sovereign in-house mode",
        )

    payload_bytes = await request.body()

    def fallback_event_id(payload: dict | None = None) -> str:
        if payload and payload.get("id"):
            return str(payload["id"])
        return f"sha256:{hashlib.sha256(payload_bytes).hexdigest()}"

    try:
        sdk_event = stripe_sdk_parser.parse_event(payload_bytes, stripe_signature)
        if sdk_event is not None:
            event_type = sdk_event.get("type") if isinstance(sdk_event, dict) else getattr(sdk_event, "type", None)
            event_id = (
                sdk_event.get("id")
                if isinstance(sdk_event, dict)
                else getattr(sdk_event, "id", None)
            ) or fallback_event_id()
            payload_json = sdk_event if isinstance(sdk_event, dict) else {"type": event_type, "id": event_id}
            webhook_event, duplicate = register_webhook_event(
                db,
                provider="stripe",
                provider_event_id=str(event_id),
                event_type=str(event_type) if event_type else None,
                payload_json=payload_json,
                max_retries=settings.webhook_max_retries,
            )
            if duplicate:
                return {
                    "status": "duplicate_ignored",
                    "provider": "stripe",
                    "event": event_type,
                    "event_id": str(event_id),
                    "delivery_count": webhook_event.delivery_count,
                    "processing_status": webhook_event.processing_status,
                }
            try:
                process_stripe_payload(payload_json)
                webhook_event = mark_processed(db, webhook_event)
                status = "accepted"
            except Exception as exc:
                webhook_event = mark_retry_or_dead_letter(
                    db,
                    webhook_event,
                    str(exc),
                    settings.webhook_retry_interval_seconds,
                )
                status = "dead_lettered" if webhook_event.processing_status == STATUS_DEAD_LETTER else "accepted_queued"
            return {
                "status": status,
                "provider": "stripe",
                "event": event_type,
                "event_id": str(event_id),
                "delivery_count": webhook_event.delivery_count,
                "processing_status": webhook_event.processing_status,
            }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    valid = stripe_verifier.verify(payload_bytes, stripe_signature)
    if not valid:
        raise HTTPException(status_code=400, detail="invalid webhook signature")
    payload = json.loads(payload_bytes.decode("utf-8")) if payload_bytes else {}
    event_id = fallback_event_id(payload)
    event_type = payload.get("type")
    webhook_event, duplicate = register_webhook_event(
        db,
        provider="stripe-fallback",
        provider_event_id=str(event_id),
        event_type=str(event_type) if event_type else None,
        payload_json=payload if isinstance(payload, dict) else {"raw": payload},
        max_retries=settings.webhook_max_retries,
    )
    if duplicate:
        return {
            "status": "duplicate_ignored",
            "provider": "stripe-fallback",
            "event": event_type,
            "event_id": str(event_id),
            "delivery_count": webhook_event.delivery_count,
            "processing_status": webhook_event.processing_status,
        }
    try:
        payload_json = payload if isinstance(payload, dict) else {"raw": payload}
        process_stripe_payload(payload_json)
        webhook_event = mark_processed(db, webhook_event)
        status = "accepted"
    except Exception as exc:
        webhook_event = mark_retry_or_dead_letter(
            db,
            webhook_event,
            str(exc),
            settings.webhook_retry_interval_seconds,
        )
        status = "dead_lettered" if webhook_event.processing_status == STATUS_DEAD_LETTER else "accepted_queued"
    return {
        "status": status,
        "provider": "stripe-fallback",
        "event": event_type,
        "event_id": str(event_id),
        "delivery_count": webhook_event.delivery_count,
        "processing_status": webhook_event.processing_status,
    }


@router.post("/vusd")
def vusd_webhook(payload: dict, db: Session = Depends(get_db)):
    verified = vusd_adapter.verify_vusd_transfer_event(payload)
    if verified.get("status") == "rejected":
        raise HTTPException(status_code=400, detail=verified)

    event_id = payload.get("event_id") or payload.get("id") or payload.get("tx_hash")
    if not event_id:
        event_id = f"sha256:{hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()}"
    event_type = payload.get("type") or "vusd.transfer"
    webhook_event, duplicate = register_webhook_event(
        db,
        provider="vusd",
        provider_event_id=str(event_id),
        event_type=str(event_type),
        payload_json=payload,
        max_retries=settings.webhook_max_retries,
    )
    if duplicate:
        return {
            "status": "duplicate_ignored",
            "verification": verified,
            "event_id": str(event_id),
            "delivery_count": webhook_event.delivery_count,
            "processing_status": webhook_event.processing_status,
        }
    try:
        process_vusd_payload(payload, vusd_adapter)
        webhook_event = mark_processed(db, webhook_event)
        status = "accepted"
    except Exception as exc:
        webhook_event = mark_retry_or_dead_letter(
            db,
            webhook_event,
            str(exc),
            settings.webhook_retry_interval_seconds,
        )
        status = "dead_lettered" if webhook_event.processing_status == STATUS_DEAD_LETTER else "accepted_queued"
    return {
        "status": status,
        "verification": verified,
        "event_id": str(event_id),
        "delivery_count": webhook_event.delivery_count,
        "processing_status": webhook_event.processing_status,
    }


@router.post("/crypto/confirm")
def crypto_confirm(payload: dict):
    tx_hash = payload.get("tx_hash")
    if not tx_hash:
        raise HTTPException(status_code=400, detail="tx_hash required")

    result = indexer_adapter.verify_chain_payment(tx_hash, min_confirmations=payload.get("min_confirmations"))
    return {"status": "accepted", "verification": result}
