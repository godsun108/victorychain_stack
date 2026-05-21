import asyncio
import time as pytime
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from starlette.requests import Request

from src.victory_impact.models import (
    AuditLog,
    AdminAPISession,
    Base,
    DonationCategoryCode,
    OpsRateLimitCooldown,
    VUSDTransferVerification,
    WebhookEvent,
)
from src.victory_impact.config import settings
from src.victory_impact.main import (
    _client_ip,
    _is_internal_url,
    _is_private_or_loopback_ip,
    _parse_trusted_proxy_networks,
    validate_inhouse_only_settings,
    validate_public_runtime_settings,
    validate_sovereign_runtime_settings,
)
from src.victory_impact.policies import runtime_policies
from src.victory_impact.routers import admin, payments, public
from src.victory_impact.schemas import (
    AdminPaymentIntentBulkActionRequest,
    AdminOpsActionRequest,
    AdminOpsSupportBundleArchiveRequest,
    PegasusEventIngestRequest,
    PegasusTrustedSignalUpsertRequest,
    PaymentCapturePayload,
    SLOControlLoopRequest,
    PegasusBalanceResponse,
    PaymentIntentCreate,
    RuntimePolicyUpdate,
    PublicAiChatRequest,
    PublicAuthRevokeRequest,
    PublicDiagnosticsReportCreate,
    ProductAnalyticsEventCreate,
    VUSDAutoRetryRequest,
    VUSDRetryRequest,
    VUSDRetryRangeRequest,
    VUSDVerifyRequest,
    WalletPhotoCreate,
)
from src.victory_impact.security import current_role
from src.victory_impact.services.admin_auth import (
    issue_admin_api_session,
    revoke_admin_api_session_token,
    validate_admin_api_session_token,
)
from src.victory_impact.services.donations import (
    create_donation_and_token,
    ensure_default_categories,
    get_or_create_donor,
    get_wallet_summary,
)
from src.victory_impact.services.payment_adapters import EVMIndexerAdapter, InHouseCardBankAdapter, VUSDAdapter
from src.victory_impact.services.subscriptions import (
    check_entitlement,
    ensure_default_billing_plans,
    grant_entitlement,
    subscribe_user,
)
from src.victory_impact.services.public_auth import (
    issue_wallet_challenge,
    revoke_wallet_session_token,
    validate_wallet_session_token,
    verify_wallet_signature,
)


def build_db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, future=True)
    return factory()


def test_idempotent_capture_by_payment_reference():
    db = build_db()
    ensure_default_categories(db)
    donor = get_or_create_donor(db, "idem@example.org")

    first = create_donation_and_token(
        db,
        donor,
        DonationCategoryCode.MERCY,
        Decimal("42.00"),
        "USD",
        "card_or_bank",
        "capture-ref-001",
        None,
        "idem test",
        "M-1",
    )
    second = create_donation_and_token(
        db,
        donor,
        DonationCategoryCode.MERCY,
        Decimal("42.00"),
        "USD",
        "card_or_bank",
        "capture-ref-001",
        None,
        "idem test",
        "M-1",
    )

    assert first[0].id == second[0].id
    assert first[1].id == second[1].id
    assert first[2].id == second[2].id


def test_payment_adapters_local():
    old_base = settings.inhouse_payment_gateway_base_url
    settings.inhouse_payment_gateway_base_url = "https://checkout.internal"
    try:
        card = InHouseCardBankAdapter().create_intent("card", Decimal("10.00"), "USD", "d@example.org")
    finally:
        settings.inhouse_payment_gateway_base_url = old_base
    assert card.intent_id.startswith("inhouse-card-")
    assert card.status == "pending"
    assert card.checkout_url is not None and card.checkout_url.startswith("https://checkout.internal/checkout/")

    class FakeIndexer(EVMIndexerAdapter):
        def __init__(self):
            super().__init__("http://rpc.local", 1)

        def verify_chain_payment(self, tx_hash: str, min_confirmations=None) -> dict:  # type: ignore[override]
            return {
                "tx_hash": tx_hash,
                "status": "confirmed",
                "confirmations": 3,
                "required_confirmations": 1,
                "tx_block": 100,
                "head_block": 103,
                "tx_status": "success",
                "receipt": {
                    "logs": [
                        {
                            "address": "0x0000000000000000000000000000000000000000",
                            "topics": [
                                "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55aeb3d4f6b3f",
                                "0x0000000000000000000000001111111111111111111111111111111111111111",
                                "0x0000000000000000000000002222222222222222222222222222222222222222",
                            ],
                            "data": hex(10**18),
                            "logIndex": hex(0),
                        }
                    ]
                },
            }

    assert FakeIndexer().verify_chain_payment("0xabc")["status"] == "confirmed"
    assert (
        VUSDAdapter(FakeIndexer(), "0x0000000000000000000000000000000000000000")
        .verify_vusd_transfer_event({"event_id": "ev-1", "tx_hash": "0xabc"})
        ["status"]
        == "verified"
    )


def test_runtime_policy_toggle_is_mutable():
    original = runtime_policies.tax_receipts_enabled
    runtime_policies.tax_receipts_enabled = not original
    assert runtime_policies.tax_receipts_enabled is (not original)
    runtime_policies.tax_receipts_enabled = original


def test_sovereign_runtime_validation_blocks_external_endpoints():
    old_rpc = settings.evm_rpc_url
    old_checkout = settings.inhouse_payment_gateway_base_url
    old_sovereign = settings.sovereign_mode
    old_enforce = settings.enforce_internal_endpoints_in_sovereign_mode
    settings.sovereign_mode = True
    settings.enforce_internal_endpoints_in_sovereign_mode = True
    settings.evm_rpc_url = "https://mainnet.infura.io/v3/example"
    settings.inhouse_payment_gateway_base_url = "https://payments.example.com"
    try:
        try:
            validate_sovereign_runtime_settings()
            assert False, "expected RuntimeError for sovereign misconfiguration"
        except RuntimeError as exc:
            message = str(exc)
            assert "evm_rpc_url must be internal/private" in message
            assert "inhouse_payment_gateway_base_url must be internal/private" in message
    finally:
        settings.evm_rpc_url = old_rpc
        settings.inhouse_payment_gateway_base_url = old_checkout
        settings.sovereign_mode = old_sovereign
        settings.enforce_internal_endpoints_in_sovereign_mode = old_enforce


def test_donor_wallet_is_normalized_and_summary_is_available():
    db = build_db()
    ensure_default_categories(db)
    donor = get_or_create_donor(db, "wallet@example.org", wallet_address=" 0xAbC123 ")

    create_donation_and_token(
        db,
        donor,
        DonationCategoryCode.WIDOW,
        Decimal("50.00"),
        "USD",
        "wallet",
        "wallet-ref-1",
        "0xdeadbeef",
        "wallet-path donation",
        "W-1",
    )

    summary = get_wallet_summary(db, "0xabc123")
    assert summary is not None
    assert summary["wallet_address"] == "0xabc123"
    assert summary["donation_count"] == 1
    assert str(summary["total_donated"]) == "50.00"
    assert summary["donations"][0]["category"] == "WIDOW"
    assert summary["donations"][0]["receipt_id"] is not None


def test_public_services_catalog_includes_launch_endpoints():
    catalog = public.public_services_catalog()
    paths = {item.path for item in catalog.services}
    assert catalog.launch_surface == "public_web"
    assert "/public/services" in paths
    assert "/public/wallet/{wallet_address}" in paths
    assert "/public/vusd/verify" in paths
    assert "/public/diagnostics/ingest" in paths
    assert "/public/diagnostics/reports" in paths


def test_public_vusd_verify_persists_verification_record():
    db = build_db()
    original = public.public_vusd_adapter.verify_vusd_transfer_event
    public.public_vusd_adapter.verify_vusd_transfer_event = lambda payload: {
        "status": "verified",
        "event_id": payload.get("event_id"),
        "verification": {"status": "confirmed", "confirmations": 5, "required_confirmations": 3, "tx_block": 101},
        "matched_transfer": {
            "log_index": 0,
            "from_address": "0x1111111111111111111111111111111111111111",
            "to_address": "0x2222222222222222222222222222222222222222",
            "amount_raw": str(10**18),
            "amount_decimal": "1",
        },
    }
    try:
        response = public.public_vusd_verify(
            VUSDVerifyRequest(
                user_email="public-vusd@example.org",
                tx_hash="0xabc",
                contract_address="0x0000000000000000000000000000000000000000",
                event_id="public-verify-1",
            ),
            db=db,
        )
        assert response["status"] == "verified"
    finally:
        public.public_vusd_adapter.verify_vusd_transfer_event = original

    rows = db.query(VUSDTransferVerification).all()
    assert len(rows) == 1
    assert rows[0].source == "public_api"
    assert rows[0].tx_hash == "0xabc"
    assert rows[0].status == "verified"

    listed = admin.list_vusd_verifications(tx_hash="0xabc", status="verified", source="public_api", db=db, role="admin")
    assert len(listed) == 1
    assert listed[0]["tx_hash"] == "0xabc"
    assert listed[0]["status"] == "verified"


def test_public_ai_chat_entitlement_limit_enforced():
    db = build_db()
    email = "ai-limit@example.org"
    grant_entitlement(
        db,
        user_email=email,
        entitlement_key="ai_chat_messages",
        limit_per_window=1,
        window_unit="month",
        metadata={"test": "ai_limit"},
    )

    first = public.public_ai_chat(PublicAiChatRequest(user_email=email, message="Hello"), db=db)
    assert first.reply

    try:
        public.public_ai_chat(PublicAiChatRequest(user_email=email, message="Second"), db=db)
        assert False, "expected entitlement rejection"
    except HTTPException as exc:
        assert exc.status_code == 403
        assert isinstance(exc.detail, dict)
        assert exc.detail["error"] == "entitlement_denied"
        assert exc.detail["entitlement_key"] == "ai_chat_messages"


def test_public_calendar_event_entitlement_limit_enforced():
    db = build_db()
    email = "calendar-limit@example.org"
    grant_entitlement(
        db,
        user_email=email,
        entitlement_key="calendar_events",
        limit_per_window=1,
        window_unit="month",
        metadata={"test": "calendar_limit"},
    )

    accepted = public.public_analytics_event(
        ProductAnalyticsEventCreate(
            user_email=email,
            event_name="calendar_event_created",
            route="/calendar",
        ),
        db=db,
    )
    assert accepted.status == "accepted"

    try:
        public.public_analytics_event(
            ProductAnalyticsEventCreate(
                user_email=email,
                event_name="calendar_event_created",
                route="/calendar",
            ),
            db=db,
        )
        assert False, "expected entitlement rejection"
    except HTTPException as exc:
        assert exc.status_code == 403
        assert isinstance(exc.detail, dict)
        assert exc.detail["error"] == "entitlement_denied"
        assert exc.detail["entitlement_key"] == "calendar_events"


def test_public_ai_chat_can_resolve_entitlement_identity_from_bearer_wallet_session():
    db = build_db()
    account = Account.create()
    wallet = account.address.lower()
    get_or_create_donor(db, "wallet-session@example.org", wallet_address=wallet)

    challenge = issue_wallet_challenge(db, wallet)
    signature = Account.sign_message(
        encode_defunct(text=challenge["message"]),
        private_key=account.key,
    ).signature.hex()
    verified = verify_wallet_signature(
        db,
        wallet_address=wallet,
        nonce=challenge["nonce"],
        signature=signature,
    )

    response = public.public_ai_chat(
        PublicAiChatRequest(message="help me navigate services"),
        authorization=f"Bearer {verified['token']}",
        db=db,
    )
    assert response.reply


def test_admin_entitlement_usage_and_summary_reports_breaches():
    db = build_db()
    ensure_default_billing_plans(db)
    email = "entitlement-report@example.org"
    subscribe_user(
        db,
        user_email=email,
        plan_code="FREE",
        billing_cycle="monthly",
        trial_days=0,
    )
    consumed = check_entitlement(
        db,
        user_email=email,
        entitlement_key="ai_chat_messages",
        requested=10,
        consume=True,
    )
    assert consumed["allowed"] is True
    grant_entitlement(
        db,
        user_email=email,
        entitlement_key="ai_chat_messages",
        limit_per_window=5,
        window_unit="month",
        metadata={"source": "test-breach"},
    )

    usage_rows = admin.list_entitlement_usage(
        entitlement_key="ai_chat_messages",
        user_email=email,
        active_window_only=True,
        breached_only=True,
        limit=100,
        db=db,
        role="admin",
    )
    assert len(usage_rows) >= 1
    assert usage_rows[0].breached is True
    assert usage_rows[0].overage >= 5
    assert usage_rows[0].entitlement_key == "ai_chat_messages"

    summary = admin.entitlement_usage_summary(
        entitlement_key="ai_chat_messages",
        user_email=email,
        active_window_only=True,
        breached_only=False,
        limit=100,
        top_breaches_limit=5,
        db=db,
        role="admin",
    )
    assert summary.breach_count >= 1
    assert summary.total_rows >= 1
    assert "ai_chat_messages" in summary.by_entitlement
    assert summary.by_entitlement["ai_chat_messages"]["breaches"] >= 1
    assert len(summary.top_breaches) >= 1


def test_admin_vusd_verification_filters_pagination_and_summary():
    db = build_db()
    db.add_all(
        [
            VUSDTransferVerification(
                source="webhook_vusd",
                event_id="ev-1",
                tx_hash="0xaaa",
                status="pending",
                created_at=datetime(2026, 5, 18, 10, 0, 0),
            ),
            VUSDTransferVerification(
                source="webhook_vusd",
                event_id="ev-2",
                tx_hash="0xbbb",
                status="rejected",
                created_at=datetime(2026, 5, 19, 11, 0, 0),
            ),
            VUSDTransferVerification(
                source="public_api",
                event_id="ev-3",
                tx_hash="0xccc",
                status="verified",
                created_at=datetime(2026, 5, 19, 12, 0, 0),
            ),
        ]
    )
    db.commit()

    first_page = admin.list_vusd_verifications(
        source="webhook_vusd",
        created_from=date(2026, 5, 18),
        created_to=date(2026, 5, 19),
        limit=1,
        offset=0,
        db=db,
        role="admin",
    )
    second_page = admin.list_vusd_verifications(
        source="webhook_vusd",
        created_from=date(2026, 5, 18),
        created_to=date(2026, 5, 19),
        limit=1,
        offset=1,
        db=db,
        role="admin",
    )
    assert len(first_page) == 1
    assert first_page[0]["event_id"] == "ev-2"
    assert len(second_page) == 1
    assert second_page[0]["event_id"] == "ev-1"

    summary = admin.vusd_verification_summary(
        created_from=date(2026, 5, 18),
        created_to=date(2026, 5, 19),
        db=db,
        role="admin",
    )
    assert summary["total"] == 3
    assert summary["by_status"]["pending"] == 1
    assert summary["by_status"]["rejected"] == 1
    assert summary["by_status"]["verified"] == 1
    assert summary["by_source"]["webhook_vusd"] == 2
    assert summary["by_source"]["public_api"] == 1

    try:
        admin.list_vusd_verifications(
            created_from=date(2026, 5, 20),
            created_to=date(2026, 5, 19),
            db=db,
            role="admin",
        )
        assert False, "expected HTTPException for invalid created date range"
    except HTTPException as exc:
        assert exc.status_code == 400


def test_admin_vusd_retry_by_tx_hash_maps_provider_events():
    db = build_db()
    webhook_event = WebhookEvent(
        provider="vusd",
        provider_event_id="provider-ev-1",
        event_type="vusd.transfer",
        payload_json={"tx_hash": "0xabc"},
        processing_status="retry_queued",
    )
    db.add(webhook_event)
    db.add(
        VUSDTransferVerification(
            source="webhook",
            event_id="provider-ev-1",
            tx_hash="0xabc",
            status="pending",
            created_at=datetime(2026, 5, 19, 10, 0, 0),
        )
    )
    db.commit()

    original_run_retry_batch = admin.run_retry_batch
    admin.run_retry_batch = lambda **kwargs: {  # type: ignore[assignment]
        "status": "retry_run_complete",
        "attempted": len(kwargs.get("event_ids") or []),
        "processed": len(kwargs.get("event_ids") or []),
        "queued": 0,
        "dead_lettered": 0,
        "failed_ids": [],
    }
    try:
        result = admin.retry_vusd_by_tx_hash(
            payload=VUSDRetryRequest(tx_hash="0xabc", include_dead_letter=True, limit=50),
            db=db,
            role="admin",
        )
    finally:
        admin.run_retry_batch = original_run_retry_batch  # type: ignore[assignment]

    assert result["status"] == "retry_run_complete"
    assert result["matched_provider_event_count"] == 1
    assert result["matched_event_count"] == 1
    assert result["attempted"] == 1

    no_result = admin.retry_vusd_by_tx_hash(
        payload=VUSDRetryRequest(tx_hash="0xmissing"),
        db=db,
        role="admin",
    )
    assert no_result["status"] == "no_events_found"
    assert no_result["matched_event_count"] == 0


def test_admin_vusd_retry_failed_range_and_audit_log():
    db = build_db()
    db.add_all(
        [
            WebhookEvent(
                provider="vusd",
                provider_event_id="provider-ev-9",
                event_type="vusd.transfer",
                payload_json={"tx_hash": "0xrange"},
                processing_status="retry_queued",
            ),
            VUSDTransferVerification(
                source="webhook",
                event_id="provider-ev-9",
                tx_hash="0xrange",
                status="failed",
                created_at=datetime(2026, 5, 19, 9, 0, 0),
            ),
        ]
    )
    db.commit()

    original_run_retry_batch = admin.run_retry_batch
    admin.run_retry_batch = lambda **kwargs: {  # type: ignore[assignment]
        "status": "retry_run_complete",
        "attempted": len(kwargs.get("event_ids") or []),
        "processed": len(kwargs.get("event_ids") or []),
        "queued": 0,
        "dead_lettered": 0,
        "failed_ids": [],
    }
    try:
        result = admin.retry_vusd_failed_in_range(
            payload=VUSDRetryRangeRequest(
                created_from=date(2026, 5, 19),
                created_to=date(2026, 5, 19),
                statuses=["failed"],
                include_dead_letter=True,
                limit=100,
            ),
            db=db,
            role="admin",
        )
    finally:
        admin.run_retry_batch = original_run_retry_batch  # type: ignore[assignment]

    assert result["status"] == "retry_run_complete"
    assert result["matched_event_count"] == 1
    assert result["attempted"] == 1

    log = db.query(AuditLog).filter(AuditLog.action == "VUSD_RETRY_FAILED_RANGE").first()
    assert log is not None
    assert log.metadata_json.get("actor_role") == "admin"


def test_admin_vusd_retry_last_hours_and_retry_audit_csv_export():
    db = build_db()
    db.add_all(
        [
            WebhookEvent(
                provider="vusd",
                provider_event_id="provider-ev-12",
                event_type="vusd.transfer",
                payload_json={"tx_hash": "0xlasthours"},
                processing_status="retry_queued",
            ),
            VUSDTransferVerification(
                source="webhook",
                event_id="provider-ev-12",
                tx_hash="0xlasthours",
                status="failed",
                created_at=datetime.now(),
            ),
        ]
    )
    db.commit()

    original_run_retry_batch = admin.run_retry_batch
    admin.run_retry_batch = lambda **kwargs: {  # type: ignore[assignment]
        "status": "retry_run_complete",
        "attempted": len(kwargs.get("event_ids") or []),
        "processed": len(kwargs.get("event_ids") or []),
        "queued": 0,
        "dead_lettered": 0,
        "failed_ids": [],
    }
    try:
        result = admin.retry_vusd_last_hours(
            payload=VUSDAutoRetryRequest(hours_back=24, statuses=["failed"], include_dead_letter=True, limit=100),
            db=db,
            role="admin",
        )
    finally:
        admin.run_retry_batch = original_run_retry_batch  # type: ignore[assignment]

    assert result["status"] == "retry_run_complete"
    assert result["matched_event_count"] == 1
    assert result["attempted"] == 1

    export = admin.export_vusd_retry_audit_csv(limit=100, db=db, role="admin")
    body = asyncio.run(export.body_iterator.__anext__())
    text = body.decode() if isinstance(body, bytes) else str(body)
    assert "VUSD_RETRY_LAST_HOURS" in text


def test_admin_vusd_retry_audit_list_filters_action():
    db = build_db()
    db.add_all(
        [
            AuditLog(
                action="VUSD_RETRY_BY_TX_HASH",
                entity_type="vusd_admin",
                entity_id="a1",
                metadata_json={"actor_role": "admin"},
            ),
            AuditLog(
                action="VUSD_RETRY_FAILED_RANGE",
                entity_type="vusd_admin",
                entity_id="a2",
                metadata_json={"actor_role": "admin"},
            ),
        ]
    )
    db.commit()

    all_rows = admin.list_vusd_retry_audit(db=db, role="admin", limit=100)
    assert len(all_rows) >= 2
    filtered = admin.list_vusd_retry_audit(action="retry_by_tx_hash", db=db, role="admin", limit=100)
    assert len(filtered) == 1
    assert filtered[0]["action"] == "VUSD_RETRY_BY_TX_HASH"


def test_admin_vusd_retry_last_hours_dry_run_does_not_execute_retry_batch():
    db = build_db()
    db.add_all(
        [
            WebhookEvent(
                provider="vusd",
                provider_event_id="provider-ev-dry-1",
                event_type="vusd.transfer",
                payload_json={"tx_hash": "0xdry"},
                processing_status="retry_queued",
            ),
            VUSDTransferVerification(
                source="webhook",
                event_id="provider-ev-dry-1",
                tx_hash="0xdry",
                status="failed",
                created_at=datetime.now(),
            ),
        ]
    )
    db.commit()

    original_run_retry_batch = admin.run_retry_batch

    def _should_not_run(**kwargs):
        raise AssertionError("run_retry_batch should not execute in dry-run mode")

    admin.run_retry_batch = _should_not_run  # type: ignore[assignment]
    try:
        result = admin.retry_vusd_last_hours(
            payload=VUSDAutoRetryRequest(hours_back=24, statuses=["failed"], dry_run=True, limit=100),
            db=db,
            role="admin",
        )
    finally:
        admin.run_retry_batch = original_run_retry_batch  # type: ignore[assignment]

    assert result["status"] == "dry_run_complete"
    assert result["attempted"] == 1
    assert result["processed"] == 0
    assert result["matched_event_count"] == 1
    assert result["preview_event_ids"]

    dry_log = db.query(AuditLog).filter(AuditLog.action == "VUSD_RETRY_LAST_HOURS_DRY_RUN").first()
    assert dry_log is not None


def test_admin_slo_status_reports_breaches():
    db = build_db()
    db.add_all(
        [
            VUSDTransferVerification(
                source="webhook",
                event_id="slo-ev-1",
                tx_hash="0xslo1",
                status="failed",
                created_at=datetime.now(),
            ),
            VUSDTransferVerification(
                source="webhook",
                event_id="slo-ev-2",
                tx_hash="0xslo2",
                status="pending",
                created_at=datetime.now(),
            ),
            VUSDTransferVerification(
                source="webhook",
                event_id="slo-ev-3",
                tx_hash="0xslo3",
                status="verified",
                created_at=datetime.now(),
            ),
            AuditLog(
                action="VUSD_RETRY_LAST_HOURS",
                entity_type="vusd_admin",
                entity_id="slo-audit-1",
                metadata_json={"retry_result": {"attempted": 10, "processed": 2}},
            ),
        ]
    )
    db.commit()

    status = admin.admin_slo_status(db=db, role="admin")
    assert status["overall_healthy"] is False
    assert status["slos"]["failed_rejected_ratio"]["met"] is False
    assert status["slos"]["pending_ratio"]["met"] is False
    assert status["slos"]["retry_success_rate"]["met"] is False


def test_admin_slo_control_loop_executes_and_audits():
    db = build_db()
    db.add_all(
        [
            WebhookEvent(
                provider="vusd",
                provider_event_id="slo-control-provider-1",
                event_type="vusd.transfer",
                payload_json={"tx_hash": "0xsloctl"},
                processing_status="retry_queued",
            ),
            VUSDTransferVerification(
                source="webhook",
                event_id="slo-control-provider-1",
                tx_hash="0xsloctl",
                status="failed",
                created_at=datetime.now(),
            ),
        ]
    )
    db.commit()

    original_run_retry_batch = admin.run_retry_batch
    admin.run_retry_batch = lambda **kwargs: {  # type: ignore[assignment]
        "status": "retry_run_complete",
        "attempted": len(kwargs.get("event_ids") or []),
        "processed": len(kwargs.get("event_ids") or []),
        "queued": 0,
        "dead_lettered": 0,
        "failed_ids": [],
    }
    try:
        dry_run = admin.admin_slo_control_loop(
            payload=SLOControlLoopRequest(dry_run=True, max_actions=2, retry_hours_back=24, retry_limit=100),
            db=db,
            role="admin",
        )
        assert dry_run["dry_run"] is True
        assert dry_run["actions_count"] >= 1
        assert dry_run["actions_taken"][0]["details"]["status"] == "dry_run_complete"

        execute = admin.admin_slo_control_loop(
            payload=SLOControlLoopRequest(dry_run=False, max_actions=2, retry_hours_back=24, retry_limit=100),
            db=db,
            role="admin",
        )
    finally:
        admin.run_retry_batch = original_run_retry_batch  # type: ignore[assignment]

    assert execute["dry_run"] is False
    assert execute["actions_count"] >= 1
    assert execute["actions_taken"][0]["details"]["status"] == "retry_run_complete"
    assert execute["failed_slos"]

    logs = db.query(AuditLog).filter(AuditLog.action == "VUSD_SLO_CONTROL_LOOP").all()
    assert len(logs) >= 2


def test_admin_slo_history_includes_control_loop_ops_alerts_and_recoveries():
    db = build_db()
    now = datetime.now(UTC)
    alert_id = "ops-alert-1"
    db.add_all(
        [
            AuditLog(
                action="VUSD_SLO_CONTROL_LOOP",
                entity_type="vusd_admin",
                entity_id="slo-history-1",
                created_at=now,
                metadata_json={
                    "dry_run": True,
                    "max_actions": 3,
                    "retry_hours_back": 24,
                    "retry_limit": 300,
                    "failed_slos": ["failed_rejected_ratio"],
                    "actions_count": 1,
                    "actions": [{"action": "retry_vusd_last_hours"}],
                    "pre_overall_healthy": False,
                    "post_overall_healthy": False,
                },
            ),
            AuditLog(
                action="OPS_SLO_ALERT",
                entity_type="ops_console",
                id=alert_id,
                entity_id=alert_id,
                created_at=now,
                metadata_json={"actor_role": "admin", "session_id": "cron-slo"},
            ),
            AuditLog(
                action="OPS_SLO_RECOVERED",
                entity_type="ops_console",
                entity_id="ops-recovered-1",
                created_at=now,
                metadata_json={"actor_role": "admin", "session_id": "cron-slo"},
            ),
            AuditLog(
                action="OPS_ARCHIVE_SUPPORT_BUNDLE",
                entity_type="ops_console",
                entity_id="ops-ack-1",
                created_at=now + timedelta(minutes=1),
                metadata_json={
                    "actor_role": "admin",
                    "session_id": "admin-review-dashboard",
                    "metadata": {
                        "acknowledged": True,
                        "incident_audit_id": alert_id,
                    },
                },
            ),
            AuditLog(
                action="VUSD_SLO_CONTROL_LOOP",
                entity_type="vusd_admin",
                entity_id="slo-history-old",
                created_at=now - timedelta(hours=200),
                metadata_json={
                    "dry_run": False,
                    "failed_slos": [],
                    "actions_count": 0,
                    "pre_overall_healthy": True,
                    "post_overall_healthy": True,
                },
            ),
        ]
    )
    db.commit()

    result = admin.admin_slo_history(limit=10, hours_back=72, include_ops_alerts=True, db=db, role="admin")
    assert result["total"] == 1
    assert len(result["items"]) == 1
    first = result["items"][0]
    assert first["dry_run"] is True
    assert first["actions_count"] == 1
    assert first["failed_slos"] == ["failed_rejected_ratio"]
    assert first["post_overall_healthy"] is False
    assert "alerts" in result
    assert len(result["alerts"]) == 1
    assert result["alerts"][0]["audit_id"] == alert_id
    assert result["alerts"][0]["acknowledged"] is True
    assert "recoveries" in result
    assert len(result["recoveries"]) == 1
    assert result["recoveries"][0]["acknowledged"] is False

    filtered = admin.admin_slo_history(
        limit=10,
        hours_back=72,
        include_ops_alerts=True,
        hide_acknowledged_ops=True,
        db=db,
        role="admin",
    )
    assert filtered["hide_acknowledged_ops"] is True
    assert "alerts" in filtered
    assert len(filtered["alerts"]) == 0
    assert "recoveries" in filtered
    assert len(filtered["recoveries"]) == 1


def test_public_diagnostics_ingest_and_query():
    db = build_db()

    ingested = public.public_diagnostics_ingest(
        payload=PublicDiagnosticsReportCreate(
            session_id="session-alpha",
            route="/diagnostics",
            platform="ios",
            online=True,
            runtime_issue_count=2,
            checks=[{"id": "api", "status": "pass"}],
            runtime_issues=[{"source": "api", "message": "timeout"}],
        ),
        db=db,
    )
    assert ingested.status == "accepted"
    assert ingested.report_id

    listed = public.public_diagnostics_reports(limit=10, session_id="session-alpha", db=db)
    assert listed.total >= 1
    assert listed.reports
    first = listed.reports[0]
    assert first.session_id == "session-alpha"
    assert first.route == "/diagnostics"
    assert first.runtime_issue_count == 2


def test_public_wallet_auth_challenge_and_signature_verification():
    db = build_db()
    account = Account.create()
    wallet = account.address.lower()

    challenge = issue_wallet_challenge(db, wallet)
    assert challenge["wallet_address"] == wallet
    assert challenge["nonce"]
    assert "wants you to sign in with your Ethereum account" in challenge["message"]
    assert "Chain ID:" in challenge["message"]
    assert challenge["chain_id"] >= 1
    assert challenge["domain"]
    assert challenge["uri"].startswith(("http://", "https://"))

    signature = Account.sign_message(
        encode_defunct(text=challenge["message"]),
        private_key=account.key,
    ).signature.hex()

    verified = verify_wallet_signature(
        db,
        wallet_address=wallet,
        nonce=challenge["nonce"],
        signature=signature,
    )
    assert verified["wallet_address"] == wallet
    assert verified["token"]
    assert validate_wallet_session_token(db, wallet, verified["token"]) is True
    assert validate_wallet_session_token(db, wallet, "bad-token") is False


def test_public_wallet_auth_revoke_token():
    db = build_db()
    account = Account.create()
    wallet = account.address.lower()

    challenge = issue_wallet_challenge(db, wallet)
    signature = Account.sign_message(
        encode_defunct(text=challenge["message"]),
        private_key=account.key,
    ).signature.hex()
    verified = verify_wallet_signature(
        db,
        wallet_address=wallet,
        nonce=challenge["nonce"],
        signature=signature,
    )
    token = verified["token"]

    assert validate_wallet_session_token(db, wallet, token) is True
    assert revoke_wallet_session_token(db, wallet, token) is True
    assert validate_wallet_session_token(db, wallet, token) is False

    response = public.public_auth_revoke(
        payload=PublicAuthRevokeRequest(wallet_address=wallet),
        authorization=f"Bearer {token}",
        db=db,
    )
    assert response.status == "not_found"


def test_public_wallet_auth_rejects_disallowed_chain():
    db = build_db()
    account = Account.create()
    wallet = account.address.lower()
    old_allowed = settings.public_auth_allowed_chain_ids
    settings.public_auth_allowed_chain_ids = "1"
    try:
        try:
            issue_wallet_challenge(db, wallet, chain_id=8453)
            assert False, "expected ValueError for disallowed chain"
        except ValueError as exc:
            assert "not allowed" in str(exc)
    finally:
        settings.public_auth_allowed_chain_ids = old_allowed


def test_public_wallet_photo_library_upload_list_and_delete():
    db = build_db()
    account = Account.create()
    wallet = account.address.lower()

    challenge = issue_wallet_challenge(db, wallet)
    signature = Account.sign_message(
        encode_defunct(text=challenge["message"]),
        private_key=account.key,
    ).signature.hex()
    verified = verify_wallet_signature(
        db,
        wallet_address=wallet,
        nonce=challenge["nonce"],
        signature=signature,
    )
    auth_header = f"Bearer {verified['token']}"

    uploaded = public.public_wallet_photo_upload(
        wallet_address=wallet,
        payload=WalletPhotoCreate(
            mime_type="image/png",
            image_base64=(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5x2ioAAAAASUVORK5CYII="
            ),
            caption="receipt proof",
        ),
        authorization=auth_header,
        db=db,
    )
    assert uploaded.photo_count == 1
    assert uploaded.photos[0].caption == "receipt proof"

    listed = public.public_wallet_photo_library(wallet_address=wallet, authorization=auth_header, db=db)
    assert listed.photo_count == 1
    photo_id = listed.photos[0].photo_id

    deleted = public.public_wallet_photo_delete(
        wallet_address=wallet,
        photo_id=photo_id,
        authorization=auth_header,
        db=db,
    )
    assert deleted["status"] == "deleted"
    assert deleted["photo_id"] == photo_id

    listed_after_delete = public.public_wallet_photo_library(wallet_address=wallet, authorization=auth_header, db=db)
    assert listed_after_delete.photo_count == 0


def test_public_pegasus_ingest_and_balance_with_wallet_bearer_session():
    db = build_db()
    original_require_trusted = runtime_policies.pegasus_require_trusted_signal
    runtime_policies.pegasus_require_trusted_signal = False
    account = Account.create()
    wallet = account.address.lower()
    get_or_create_donor(db, "pegasus-wallet@example.org", wallet_address=wallet)

    challenge = issue_wallet_challenge(db, wallet)
    signature = Account.sign_message(
        encode_defunct(text=challenge["message"]),
        private_key=account.key,
    ).signature.hex()
    verified = verify_wallet_signature(
        db,
        wallet_address=wallet,
        nonce=challenge["nonce"],
        signature=signature,
    )
    auth_header = f"Bearer {verified['token']}"

    try:
        ingested = public.public_pegasus_event_ingest(
            payload=PegasusEventIngestRequest(
                event_key="wallet.vcn_domain_setup",
                source_ref="vcn-domain-setup-1",
                metadata={
                    "domain_binding_tx": "0xabc123",
                    "ownership_verification": True,
                },
            ),
            authorization=auth_header,
            db=db,
        )
        assert ingested.status == "awarded"
        assert ingested.actor_type == "wallet"
        assert ingested.actor_id == wallet
        assert ingested.points_awarded > 0
        assert ingested.balance_total >= ingested.points_awarded

        balance = public.public_pegasus_balance(
            authorization=auth_header,
            user_email=None,
            limit=25,
            db=db,
        )
        assert isinstance(balance, PegasusBalanceResponse)
        assert balance.actor_type == "wallet"
        assert balance.actor_id == wallet
        assert balance.total_points >= ingested.points_awarded
        assert len(balance.recent_events) >= 1
        assert balance.recent_events[0].event_key == "wallet.vcn_domain_setup"
    finally:
        runtime_policies.pegasus_require_trusted_signal = original_require_trusted


def test_public_pegasus_duplicate_source_ref_is_idempotent():
    db = build_db()
    original_require_trusted = runtime_policies.pegasus_require_trusted_signal
    runtime_policies.pegasus_require_trusted_signal = False
    account = Account.create()
    wallet = account.address.lower()
    get_or_create_donor(db, "pegasus-idem@example.org", wallet_address=wallet)

    challenge = issue_wallet_challenge(db, wallet)
    signature = Account.sign_message(
        encode_defunct(text=challenge["message"]),
        private_key=account.key,
    ).signature.hex()
    verified = verify_wallet_signature(
        db,
        wallet_address=wallet,
        nonce=challenge["nonce"],
        signature=signature,
    )
    auth_header = f"Bearer {verified['token']}"
    payload = PegasusEventIngestRequest(
        event_key="wallet.vcn_domain_setup",
        source_ref="same-ref-1",
        metadata={
            "domain_binding_tx": "0x777",
            "ownership_verification": True,
        },
    )

    try:
        first = public.public_pegasus_event_ingest(payload=payload, authorization=auth_header, db=db)
        second = public.public_pegasus_event_ingest(payload=payload, authorization=auth_header, db=db)

        assert first.status == "awarded"
        assert second.status == "awarded"
        assert first.event_id == second.event_id
        assert first.balance_total == second.balance_total
    finally:
        runtime_policies.pegasus_require_trusted_signal = original_require_trusted


def test_public_pegasus_email_actor_ingest_and_balance():
    db = build_db()
    original_require_trusted = runtime_policies.pegasus_require_trusted_signal
    runtime_policies.pegasus_require_trusted_signal = False
    email = "pegasus-email@example.org"

    try:
        ingested = public.public_pegasus_event_ingest(
            payload=PegasusEventIngestRequest(
                user_email=email,
                event_key="chat.friend_message_sent",
                source_ref="chat-msg-1",
                metadata={
                    "recipient_exists": True,
                    "content_quality_gate": True,
                },
            ),
            authorization=None,
            db=db,
        )
        assert ingested.status == "awarded"
        assert ingested.actor_type == "email"
        assert ingested.actor_id == email
        assert ingested.points_awarded > 0

        balance = public.public_pegasus_balance(user_email=email, authorization=None, limit=10, db=db)
        assert balance.actor_type == "email"
        assert balance.actor_id == email
        assert balance.total_points >= ingested.points_awarded
    finally:
        runtime_policies.pegasus_require_trusted_signal = original_require_trusted


def test_public_vusd_verify_upserts_wallet_trusted_signal():
    db = build_db()
    account = Account.create()
    wallet = account.address.lower()
    get_or_create_donor(db, "pegasus-vusd@example.org", wallet_address=wallet)

    challenge = issue_wallet_challenge(db, wallet)
    signature = Account.sign_message(
        encode_defunct(text=challenge["message"]),
        private_key=account.key,
    ).signature.hex()
    verified = verify_wallet_signature(
        db,
        wallet_address=wallet,
        nonce=challenge["nonce"],
        signature=signature,
    )
    auth_header = f"Bearer {verified['token']}"

    class _FakePublicVUSDAdapter:
        def verify_vusd_transfer_event(self, payload: dict) -> dict:
            return {
                "status": "verified",
                "expected": {},
                "matched_transfer": {},
                "verification": {"required_confirmations": 1, "confirmations": 2},
            }

    old_adapter = public.public_vusd_adapter
    public.public_vusd_adapter = _FakePublicVUSDAdapter()
    try:
        result = public.public_vusd_verify(
            payload=VUSDVerifyRequest(tx_hash="0xabc123"),
            authorization=auth_header,
            db=db,
        )
        assert result["status"] == "verified"

        signals = admin.admin_list_pegasus_trusted_signals(
            actor_type="wallet",
            actor_id=wallet,
            event_key="wallet.vusd_p2p_transfer_verified",
            status="verified",
            limit=10,
            db=db,
            role="admin",
        )
        assert len(signals) == 1
        assert signals[0].source_ref == "0xabc123"
        assert signals[0].verifier == "public_vusd_verify"
    finally:
        public.public_vusd_adapter = old_adapter


def test_admin_pegasus_policy_and_signal_controls():
    db = build_db()
    original_values = {
        "pegasus_enabled": runtime_policies.pegasus_enabled,
        "pegasus_kill_switch": runtime_policies.pegasus_kill_switch,
        "pegasus_require_trusted_signal": runtime_policies.pegasus_require_trusted_signal,
        "pegasus_enabled_event_keys": runtime_policies.pegasus_enabled_event_keys,
        "incident_scan_capped_rate_alert_threshold": runtime_policies.incident_scan_capped_rate_alert_threshold,
    }
    try:
        updated = admin.update_runtime_policies(
            payload=RuntimePolicyUpdate(
                pegasus_enabled=False,
                pegasus_kill_switch=True,
                pegasus_require_trusted_signal=True,
                pegasus_enabled_event_keys="wallet.vusd_p2p_transfer_verified",
                incident_scan_capped_rate_alert_threshold=0.2,
            ),
            db=db,
            role="admin",
        )
        policies = updated["policies"]
        assert policies["pegasus_enabled"] is False
        assert policies["pegasus_kill_switch"] is True
        assert policies["pegasus_require_trusted_signal"] is True
        assert policies["pegasus_enabled_event_keys"] == "wallet.vusd_p2p_transfer_verified"
        assert abs(float(policies["incident_scan_capped_rate_alert_threshold"]) - 0.2) < 1e-9
    finally:
        runtime_policies.pegasus_enabled = original_values["pegasus_enabled"]
        runtime_policies.pegasus_kill_switch = original_values["pegasus_kill_switch"]
        runtime_policies.pegasus_require_trusted_signal = original_values["pegasus_require_trusted_signal"]
        runtime_policies.pegasus_enabled_event_keys = original_values["pegasus_enabled_event_keys"]
        runtime_policies.incident_scan_capped_rate_alert_threshold = original_values["incident_scan_capped_rate_alert_threshold"]

    signal = admin.admin_upsert_pegasus_trusted_signal(
        payload=PegasusTrustedSignalUpsertRequest(
            actor_type="email",
            actor_id="pegasus-admin@example.org",
            event_key="social.post_published",
            source_ref="social:manual:1",
            status="verified",
            verifier="test_suite",
            evidence={"source": "unit_test"},
        ),
        db=db,
        role="admin",
    )
    assert signal.actor_type == "email"
    assert signal.actor_id == "pegasus-admin@example.org"
    assert signal.event_key == "social.post_published"
    assert signal.status == "verified"

    trusted = admin.admin_list_pegasus_trusted_signals(
        actor_type="email",
        actor_id="pegasus-admin@example.org",
        event_key="social.post_published",
        status="verified",
        limit=10,
        db=db,
        role="admin",
    )
    assert len(trusted) == 1
    assert trusted[0].signal_id == signal.signal_id

    summary = admin.admin_pegasus_summary(db=db, role="admin")
    assert summary.trusted_signals.get("verified", 0) >= 1

def test_admin_api_session_issue_validate_and_revoke():
    db = build_db()
    issued = issue_admin_api_session(db, "admin-token")
    assert issued["role"] == "admin"
    assert issued["token"]
    assert validate_admin_api_session_token(db, issued["token"]) == "admin"

    assert revoke_admin_api_session_token(db, issued["token"]) is True
    assert validate_admin_api_session_token(db, issued["token"]) is None


def test_admin_api_session_requires_admin_bootstrap_token():
    db = build_db()
    try:
        issue_admin_api_session(db, "donor-token")
        assert False, "expected ValueError for non-admin bootstrap token"
    except ValueError as exc:
        assert "invalid bootstrap token" in str(exc)


def test_current_role_supports_bearer_and_legacy_tokens():
    db = build_db()
    old_allow_legacy = settings.admin_allow_legacy_api_tokens
    settings.admin_allow_legacy_api_tokens = True
    try:
        issued = issue_admin_api_session(db, "board-token")
        assert current_role(authorization=f"Bearer {issued['token']}", x_api_token=None, db=db) == "board"
        assert current_role(authorization=None, x_api_token="compliance-token", db=db) == "compliance"
    finally:
        settings.admin_allow_legacy_api_tokens = old_allow_legacy


def test_current_role_rejects_legacy_token_when_disabled():
    db = build_db()
    old_allow_legacy = settings.admin_allow_legacy_api_tokens
    settings.admin_allow_legacy_api_tokens = False
    try:
        try:
            current_role(authorization=None, x_api_token="admin-token", db=db)
            assert False, "expected HTTPException when legacy tokens are disabled"
        except HTTPException as exc:
            assert exc.status_code == 401
            assert "disabled" in str(exc.detail).lower()
    finally:
        settings.admin_allow_legacy_api_tokens = old_allow_legacy


def test_admin_auth_session_endpoints_issue_and_revoke():
    db = build_db()
    request = _build_request("10.1.2.3")
    issued = admin.create_admin_session(request=request, x_api_token="admin-token", x_device_id="ios-dev-1", db=db)
    assert issued.role == "admin"
    assert issued.token

    rotated = admin.rotate_admin_session(
        request=request,
        authorization=f"Bearer {issued.token}",
        x_device_id="ios-dev-1",
        db=db,
        role="admin",
    )
    assert rotated.role == "admin"
    assert rotated.token != issued.token

    result = admin.revoke_admin_session(authorization=f"Bearer {issued.token}", db=db, role="admin")
    assert result["status"] == "revoked"

    second = admin.revoke_admin_session(authorization=f"Bearer {rotated.token}", db=db, role="admin")
    assert second["status"] == "revoked"


def test_admin_session_limit_auto_revokes_oldest():
    db = build_db()
    old_max = settings.admin_session_max_active_per_role
    settings.admin_session_max_active_per_role = 2
    try:
        first = admin.create_admin_session(request=_build_request("10.1.1.1"), x_api_token="admin-token", db=db)
        second = admin.create_admin_session(request=_build_request("10.1.1.2"), x_api_token="admin-token", db=db)
        third = admin.create_admin_session(request=_build_request("10.1.1.3"), x_api_token="admin-token", db=db)

        assert first.token and second.token and third.token
        # Oldest token should be invalid after limit enforcement.
        assert validate_admin_api_session_token(db, first.token) is None
        assert validate_admin_api_session_token(db, second.token) == "admin"
        assert validate_admin_api_session_token(db, third.token) == "admin"

        active_sessions = db.query(AdminAPISession).filter(AdminAPISession.revoked_at.is_(None)).all()
        assert len(active_sessions) == 2
    finally:
        settings.admin_session_max_active_per_role = old_max


def test_admin_bootstrap_can_be_disabled():
    db = build_db()
    old_enabled = settings.admin_bootstrap_enabled
    settings.admin_bootstrap_enabled = False
    try:
        try:
            admin.create_admin_session(request=_build_request("10.1.9.9"), x_api_token="admin-token", db=db)
            assert False, "expected HTTPException when bootstrap issuance is disabled"
        except HTTPException as exc:
            assert exc.status_code == 401
            assert "disabled" in str(exc.detail).lower()
    finally:
        settings.admin_bootstrap_enabled = old_enabled


def test_admin_ops_action_and_audit_endpoints():
    db = build_db()
    logged = admin.admin_ops_action(
        payload=AdminOpsActionRequest(
            action="run_all_checks",
            source_route="/ops-console",
            session_id="session-ops-1",
            metadata={"trigger": "manual"},
        ),
        db=db,
        role="admin",
    )
    assert logged.status == "logged"
    assert logged.action == "run_all_checks"
    assert logged.action_id

    audit = admin.admin_ops_audit(limit=20, action="run_all_checks", db=db, role="admin")
    assert audit.total >= 1
    assert audit.entries
    assert audit.entries[0].action == "OPS_RUN_ALL_CHECKS"
    assert audit.entries[0].metadata.get("source_route") == "/ops-console"

    slo_logged = admin.admin_ops_action(
        payload=AdminOpsActionRequest(
            action="slo_alert",
            source_route="/ops/slo-control-loop",
            session_id="cron-slo-control-loop",
            metadata={"failed_slos": ["failed_rejected_ratio"]},
        ),
        db=db,
        role="admin",
    )
    assert slo_logged.status == "logged"
    assert slo_logged.action == "slo_alert"

    recovered_logged = admin.admin_ops_action(
        payload=AdminOpsActionRequest(
            action="slo_recovered",
            source_route="/ops/slo-control-loop",
            session_id="cron-slo-control-loop",
            metadata={"recovered": True},
        ),
        db=db,
        role="admin",
    )
    assert recovered_logged.status == "logged"
    assert recovered_logged.action == "slo_recovered"

    slo_audit = admin.admin_ops_audit(limit=20, action="slo_alert", db=db, role="admin")
    assert slo_audit.total >= 1
    assert slo_audit.entries[0].action == "OPS_SLO_ALERT"

    api_health_alert_logged = admin.admin_ops_action(
        payload=AdminOpsActionRequest(
            action="api_health_alert",
            source_route="/ops/api-health-sentinel",
            session_id="api-health-sentinel",
            metadata={"port": 9100, "restarted": True},
        ),
        db=db,
        role="admin",
    )
    assert api_health_alert_logged.status == "logged"
    assert api_health_alert_logged.action == "api_health_alert"

    api_health_recovered_logged = admin.admin_ops_action(
        payload=AdminOpsActionRequest(
            action="api_health_recovered",
            source_route="/ops/api-health-sentinel",
            session_id="api-health-sentinel",
            metadata={"port": 9100, "restarted": True},
        ),
        db=db,
        role="admin",
    )
    assert api_health_recovered_logged.status == "logged"
    assert api_health_recovered_logged.action == "api_health_recovered"

    incidents = admin.admin_ops_incidents(
        limit=20,
        hours_back=48,
        include_slo=True,
        include_api_health=True,
        hide_acknowledged=False,
        db=db,
        role="admin",
    )
    assert incidents.total >= 4
    assert any(entry.category == "slo" for entry in incidents.entries)
    assert any(entry.category == "api_health" for entry in incidents.entries)
    assert any(entry.kind == "alert" for entry in incidents.entries)
    assert any(entry.kind == "recovery" for entry in incidents.entries)
    assert any(entry.severity == "critical" for entry in incidents.entries)
    assert any(entry.severity == "warning" for entry in incidents.entries)
    assert any(entry.remediation_status == "open" for entry in incidents.entries)
    assert any(entry.remediation_status == "resolved" for entry in incidents.entries)

    _ = admin.admin_ops_action(
        payload=AdminOpsActionRequest(
            action="archive_support_bundle",
            source_route="/admin/reviews",
            session_id="admin-review-dashboard",
            metadata={"incident_audit_id": api_health_alert_logged.action_id, "acknowledged": True},
        ),
        db=db,
        role="admin",
    )

    api_only_visible = admin.admin_ops_incidents(
        limit=20,
        hours_back=48,
        include_slo=False,
        include_api_health=True,
        hide_acknowledged=False,
        db=db,
        role="admin",
    )
    target_incident = next((entry for entry in api_only_visible.entries if entry.incident_id == api_health_alert_logged.action_id), None)
    assert target_incident is not None
    assert target_incident.acknowledged is True
    assert target_incident.acknowledged_at is not None
    assert target_incident.remediation_status == "acknowledged"
    assert target_incident.severity == "warning"

    api_only_hidden = admin.admin_ops_incidents(
        limit=20,
        hours_back=48,
        include_slo=False,
        include_api_health=True,
        hide_acknowledged=True,
        db=db,
        role="admin",
    )
    assert all(entry.incident_id != api_health_alert_logged.action_id for entry in api_only_hidden.entries)

    critical_only = admin.admin_ops_incidents(
        limit=20,
        hours_back=48,
        include_slo=True,
        include_api_health=True,
        severity="critical",
        db=db,
        role="admin",
    )
    assert critical_only.entries
    assert all(entry.severity == "critical" for entry in critical_only.entries)

    first_page = admin.admin_ops_incidents(
        limit=1,
        hours_back=48,
        include_slo=True,
        include_api_health=True,
        db=db,
        role="admin",
    )
    assert first_page.entries
    assert first_page.next_cursor is not None
    second_page = admin.admin_ops_incidents(
        limit=1,
        hours_back=48,
        cursor=first_page.next_cursor,
        include_slo=True,
        include_api_health=True,
        db=db,
        role="admin",
    )
    assert second_page.entries
    assert second_page.entries[0].incident_id != first_page.entries[0].incident_id


def test_admin_ops_incidents_filtered_cursor_scans_beyond_initial_window():
    db = build_db()
    now = datetime.now(UTC)

    for i in range(650):
        db.add(
            AuditLog(
                action="OPS_API_HEALTH_ALERT",
                entity_type="ops_console",
                entity_id=f"warning-{i}",
                metadata_json={
                    "source_route": "/ops/api-health-sentinel",
                    "session_id": "api-health-sentinel",
                    "metadata": {"restarted": True},
                },
                created_at=now - timedelta(seconds=i),
            )
        )

    critical_one = AuditLog(
        action="OPS_API_HEALTH_ALERT",
        entity_type="ops_console",
        entity_id="critical-1",
        metadata_json={
            "source_route": "/ops/api-health-sentinel",
            "session_id": "api-health-sentinel",
            "metadata": {"restarted": False},
        },
        created_at=now - timedelta(seconds=700),
    )
    critical_two = AuditLog(
        action="OPS_API_HEALTH_ALERT",
        entity_type="ops_console",
        entity_id="critical-2",
        metadata_json={
            "source_route": "/ops/api-health-sentinel",
            "session_id": "api-health-sentinel",
            "metadata": {"restarted": False},
        },
        created_at=now - timedelta(seconds=710),
    )
    db.add(critical_one)
    db.add(critical_two)
    db.commit()

    first_page = admin.admin_ops_incidents(
        limit=1,
        hours_back=48,
        include_slo=False,
        include_api_health=True,
        severity="critical",
        db=db,
        role="admin",
    )
    assert first_page.entries
    assert first_page.entries[0].incident_id == critical_one.id
    assert first_page.next_cursor is not None
    assert first_page.scan_rows >= 650
    assert first_page.scan_capped is False
    assert first_page.warning is None

    second_page = admin.admin_ops_incidents(
        limit=1,
        hours_back=48,
        cursor=first_page.next_cursor,
        include_slo=False,
        include_api_health=True,
        severity="critical",
        db=db,
        role="admin",
    )
    assert second_page.entries
    assert second_page.entries[0].incident_id == critical_two.id


def test_admin_ops_incidents_scan_cap_sets_warning_and_cursor_for_continuation():
    db = build_db()
    now = datetime.now(UTC)

    for i in range(5100):
        db.add(
            AuditLog(
                action="OPS_API_HEALTH_ALERT",
                entity_type="ops_console",
                entity_id=f"warning-cap-{i}",
                metadata_json={
                    "source_route": "/ops/api-health-sentinel",
                    "session_id": "api-health-sentinel",
                    "metadata": {"restarted": True},
                },
                created_at=now - timedelta(seconds=i),
            )
        )

    critical_after_cap = AuditLog(
        action="OPS_API_HEALTH_ALERT",
        entity_type="ops_console",
        entity_id="critical-after-cap",
        metadata_json={
            "source_route": "/ops/api-health-sentinel",
            "session_id": "api-health-sentinel",
            "metadata": {"restarted": False},
        },
        created_at=now - timedelta(seconds=5200),
    )
    db.add(critical_after_cap)
    db.commit()

    first_page = admin.admin_ops_incidents(
        limit=10,
        hours_back=48,
        include_slo=False,
        include_api_health=True,
        severity="critical",
        db=db,
        role="admin",
    )
    assert first_page.entries == []
    assert first_page.scan_rows >= 5000
    assert first_page.scan_capped is True
    assert first_page.warning is not None
    assert first_page.next_cursor is not None

    second_page = admin.admin_ops_incidents(
        limit=10,
        hours_back=48,
        cursor=first_page.next_cursor,
        include_slo=False,
        include_api_health=True,
        severity="critical",
        db=db,
        role="admin",
    )
    assert second_page.entries
    assert second_page.entries[0].incident_id == critical_after_cap.id
    assert second_page.scan_capped is False


def test_admin_ops_incidents_rejects_invalid_cursor():
    db = build_db()
    try:
        _ = admin.admin_ops_incidents(
            limit=5,
            hours_back=48,
            cursor="not-a-valid-cursor",
            include_slo=True,
            include_api_health=True,
            db=db,
            role="admin",
        )
        assert False, "expected HTTPException for invalid cursor"
    except HTTPException as exc:
        assert exc.status_code == 400
        assert str(exc.detail) == "invalid cursor"


def test_admin_ops_incidents_records_scan_observation_and_metrics():
    db = build_db()

    _ = admin.admin_ops_incidents(
        limit=5,
        hours_back=48,
        include_slo=True,
        include_api_health=True,
        db=db,
        role="admin",
    )
    recorded = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "ops_console",
            AuditLog.action == "OPS_INCIDENTS_SCAN_OBSERVATION",
        )
    ).all()
    assert recorded

    now = datetime.now(UTC)
    synthetic = [
        {"scan_rows": 50, "scan_capped": False, "severity": "all", "remediation_status": "all"},
        {"scan_rows": 75, "scan_capped": False, "severity": "all", "remediation_status": "all"},
        {"scan_rows": 100, "scan_capped": False, "severity": "critical", "remediation_status": "all"},
        {"scan_rows": 150, "scan_capped": True, "severity": "critical", "remediation_status": "all"},
        {"scan_rows": 5000, "scan_capped": True, "severity": "critical", "remediation_status": "acknowledged"},
    ]
    for idx, item in enumerate(synthetic):
        db.add(
            AuditLog(
                action="OPS_INCIDENTS_SCAN_OBSERVATION",
                entity_type="ops_console",
                entity_id=f"scan-observation-{idx}",
                metadata_json={
                    "actor_role": "admin",
                    "limit": 40,
                    "hours_back": 48,
                    "include_slo": True,
                    "include_api_health": True,
                    "hide_acknowledged": False,
                    "severity": item["severity"],
                    "remediation_status": item["remediation_status"],
                    "cursor_used": False,
                    "returned_entries": 10,
                    "scan_rows": item["scan_rows"],
                    "scan_capped": item["scan_capped"],
                },
                created_at=now - timedelta(minutes=idx),
            )
        )
    db.commit()

    metrics = admin.admin_ops_incident_metrics(hours_back=48, top_filters=6, db=db, role="admin")
    assert metrics.window_hours == 48
    assert abs(float(metrics.capped_rate_alert_threshold) - float(runtime_policies.incident_scan_capped_rate_alert_threshold)) < 1e-9
    assert metrics.total_scans >= 6
    assert metrics.capped_scans >= 2
    assert metrics.capped_rate > 0
    assert metrics.max_scan_rows >= 5000
    assert metrics.p95_scan_rows >= 150
    assert metrics.cooldown_rows_total == 0
    assert metrics.cooldown_oldest_updated_at is None
    assert metrics.filters
    assert any(item.filter_key.startswith("severity=critical|") for item in metrics.filters)


def test_runtime_policy_threshold_update_logs_audit_and_is_rate_limited():
    db = build_db()
    runtime_policies.incident_scan_capped_rate_alert_threshold = 0.10

    updated = admin.update_runtime_policies(
        payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.15),
        db=db,
        role="admin",
    )
    assert updated["status"] == "updated"
    threshold_logs = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "ops_console",
            AuditLog.action == "OPS_UPDATE_INCIDENT_SCAN_CAPPED_RATE_THRESHOLD",
        )
    ).all()
    assert threshold_logs
    assert threshold_logs[0].metadata_json["actor_role"] == "admin"

    try:
        _ = admin.update_runtime_policies(
            payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.2),
            db=db,
            role="admin",
        )
        assert False, "expected HTTPException for rate-limited threshold update"
    except HTTPException as exc:
        assert exc.status_code == 429
        assert "rate-limited" in str(exc.detail).lower()
        assert exc.headers is not None
        assert int(exc.headers.get("Retry-After", "0")) >= 1


def test_runtime_policy_threshold_update_noop_does_not_log_audit_row():
    db = build_db()
    runtime_policies.incident_scan_capped_rate_alert_threshold = 0.10

    first = admin.update_runtime_policies(
        payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.15),
        db=db,
        role="admin",
    )
    assert first["status"] == "updated"
    first_logs = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "ops_console",
            AuditLog.action == "OPS_UPDATE_INCIDENT_SCAN_CAPPED_RATE_THRESHOLD",
        )
    ).all()
    assert len(first_logs) == 1

    second = admin.update_runtime_policies(
        payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.15),
        db=db,
        role="admin",
    )
    assert second["status"] == "updated"
    second_logs = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "ops_console",
            AuditLog.action == "OPS_UPDATE_INCIDENT_SCAN_CAPPED_RATE_THRESHOLD",
        )
    ).all()
    assert len(second_logs) == 1


def test_runtime_policy_threshold_rate_limit_is_role_scoped():
    db = build_db()
    runtime_policies.incident_scan_capped_rate_alert_threshold = 0.10

    _ = admin.update_runtime_policies(
        payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.15),
        db=db,
        role="admin",
    )

    board_update = admin.update_runtime_policies(
        payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.20),
        db=db,
        role="board",
    )
    assert board_update["status"] == "updated"
    threshold_logs = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "ops_console",
            AuditLog.action == "OPS_UPDATE_INCIDENT_SCAN_CAPPED_RATE_THRESHOLD",
        )
    ).all()
    assert len(threshold_logs) == 2
    actor_roles = {
        str((row.metadata_json or {}).get("actor_role"))
        for row in threshold_logs
        if isinstance(row.metadata_json, dict)
    }
    assert "admin" in actor_roles
    assert "board" in actor_roles


def test_runtime_policy_threshold_rate_limit_retry_after_decreases_over_time():
    db = build_db()
    runtime_policies.incident_scan_capped_rate_alert_threshold = 0.10

    _ = admin.update_runtime_policies(
        payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.15),
        db=db,
        role="admin",
    )

    first_retry_after = None
    try:
        _ = admin.update_runtime_policies(
            payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.20),
            db=db,
            role="admin",
        )
        assert False, "expected HTTPException for first blocked update"
    except HTTPException as exc:
        assert exc.status_code == 429
        assert exc.headers is not None
        first_retry_after = int(exc.headers.get("Retry-After", "0"))
        assert first_retry_after >= 1

    pytime.sleep(1.2)

    try:
        _ = admin.update_runtime_policies(
            payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.25),
            db=db,
            role="admin",
        )
        assert False, "expected HTTPException for second blocked update"
    except HTTPException as exc:
        assert exc.status_code == 429
        assert exc.headers is not None
        second_retry_after = int(exc.headers.get("Retry-After", "0"))
        assert second_retry_after >= 1
        assert first_retry_after is not None
        assert second_retry_after <= first_retry_after


def test_runtime_policy_threshold_cooldown_is_driven_by_cooldown_table_not_audit_logs():
    db = build_db()
    runtime_policies.incident_scan_capped_rate_alert_threshold = 0.10

    db.add(
        AuditLog(
            action="OPS_UPDATE_INCIDENT_SCAN_CAPPED_RATE_THRESHOLD",
            entity_type="ops_console",
            entity_id="legacy-audit-only",
            metadata_json={"actor_role": "admin"},
            created_at=datetime.now(UTC),
        )
    )
    db.commit()

    updated = admin.update_runtime_policies(
        payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.15),
        db=db,
        role="admin",
    )
    assert updated["status"] == "updated"
    cooldown_rows = db.scalars(
        select(OpsRateLimitCooldown).where(
            OpsRateLimitCooldown.cooldown_key == "incident_scan_capped_rate_alert_threshold",
            OpsRateLimitCooldown.actor_role == "admin",
        )
    ).all()
    assert len(cooldown_rows) == 1


def test_runtime_policy_threshold_update_prunes_stale_cooldown_rows():
    db = build_db()
    runtime_policies.incident_scan_capped_rate_alert_threshold = 0.10
    stale_time = datetime.now(UTC) - timedelta(days=90)
    db.add(
        OpsRateLimitCooldown(
            cooldown_key="stale-key",
            actor_role="admin",
            last_triggered_at=stale_time,
            created_at=stale_time,
            updated_at=stale_time,
        )
    )
    db.commit()

    _ = admin.update_runtime_policies(
        payload=RuntimePolicyUpdate(incident_scan_capped_rate_alert_threshold=0.15),
        db=db,
        role="admin",
    )
    stale_rows = db.scalars(
        select(OpsRateLimitCooldown).where(OpsRateLimitCooldown.cooldown_key == "stale-key")
    ).all()
    assert stale_rows == []


def test_admin_ops_incident_metrics_includes_cooldown_health_signals():
    db = build_db()
    now = datetime.now(UTC)
    older = now - timedelta(hours=5)
    newer = now - timedelta(hours=1)
    db.add(
        OpsRateLimitCooldown(
            cooldown_key="incident_scan_capped_rate_alert_threshold",
            actor_role="admin",
            last_triggered_at=older,
            created_at=older,
            updated_at=older,
        )
    )
    db.add(
        OpsRateLimitCooldown(
            cooldown_key="another-key",
            actor_role="board",
            last_triggered_at=newer,
            created_at=newer,
            updated_at=newer,
        )
    )
    db.commit()

    metrics = admin.admin_ops_incident_metrics(hours_back=24, top_filters=6, db=db, role="admin")
    assert metrics.cooldown_rows_total == 2
    assert metrics.cooldown_oldest_updated_at is not None
    assert abs((metrics.cooldown_oldest_updated_at - older).total_seconds()) < 1.0


def test_admin_ops_support_bundle_archive_and_list():
    db = build_db()
    archived = admin.admin_archive_ops_support_bundle(
        payload=AdminOpsSupportBundleArchiveRequest(
            source_route="/ops-console",
            session_id="session-ops-2",
            diagnostics_report_id="diag-rpt-1",
            bundle={"api_health": {"status": "ok"}, "checks": [{"key": "api", "status": "pass"}]},
        ),
        db=db,
        role="admin",
    )
    assert archived.status == "archived"
    assert archived.bundle_id

    listed = admin.admin_list_ops_support_bundles(limit=10, session_id="session-ops-2", db=db, role="admin")
    assert listed.total >= 1
    assert listed.bundles
    first = listed.bundles[0]
    assert first.session_id == "session-ops-2"
    assert first.source_route == "/ops-console"


def test_public_runtime_validation_requires_walletconnect_and_https_origins():
    old_env = settings.app_env
    old_public_web_mode = settings.public_web_mode
    old_walletconnect = settings.enable_external_walletconnect
    old_inhouse = settings.inhouse_only_mode
    old_admin_legacy = settings.admin_allow_legacy_api_tokens
    old_origins = settings.cors_origins
    settings.app_env = "prod"
    settings.public_web_mode = True
    settings.enable_external_walletconnect = False
    settings.inhouse_only_mode = False
    settings.admin_allow_legacy_api_tokens = True
    settings.cors_origins = "http://localhost:5173"
    try:
        try:
            validate_public_runtime_settings()
            assert False, "expected RuntimeError for public mode misconfiguration"
        except RuntimeError as exc:
            message = str(exc)
            assert "enable_external_walletconnect must be true" in message
            assert "admin_allow_legacy_api_tokens must be false" in message
            assert "admin_bootstrap_enabled must be false" in message
            assert "localhost/127.0.0.1" in message
            assert "must use https" in message
    finally:
        settings.app_env = old_env
        settings.public_web_mode = old_public_web_mode
        settings.enable_external_walletconnect = old_walletconnect
        settings.inhouse_only_mode = old_inhouse
        settings.admin_allow_legacy_api_tokens = old_admin_legacy
        settings.cors_origins = old_origins


def _build_request(client_host: str, forwarded_for: str | None = None) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if forwarded_for:
        headers.append((b"x-forwarded-for", forwarded_for.encode("utf-8")))

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/public/services",
        "raw_path": b"/public/services",
        "query_string": b"",
        "headers": headers,
        "client": (client_host, 44321),
        "server": ("api.example.org", 443),
    }
    return Request(scope)


def test_client_ip_trusts_forwarded_header_only_for_trusted_proxy_networks():
    old_trust = settings.trust_proxy_headers
    old_cidrs = settings.trusted_proxy_cidrs
    settings.trust_proxy_headers = True
    settings.trusted_proxy_cidrs = "10.0.0.0/8"
    try:
        trusted_request = _build_request("10.1.2.3", forwarded_for="198.51.100.24")
        untrusted_request = _build_request("203.0.113.9", forwarded_for="198.51.100.24")
        invalid_forwarded_request = _build_request("10.2.3.4", forwarded_for="not-an-ip")

        assert _client_ip(trusted_request) == "198.51.100.24"
        assert _client_ip(untrusted_request) == "203.0.113.9"
        assert _client_ip(invalid_forwarded_request) == "10.2.3.4"
    finally:
        settings.trust_proxy_headers = old_trust
        settings.trusted_proxy_cidrs = old_cidrs


def test_parse_trusted_proxy_networks_rejects_invalid_cidr():
    old_cidrs = settings.trusted_proxy_cidrs
    settings.trusted_proxy_cidrs = "10.0.0.0/8,bad-cidr"
    try:
        try:
            _parse_trusted_proxy_networks()
            assert False, "expected RuntimeError for invalid CIDR"
        except RuntimeError as exc:
            assert "invalid trusted proxy CIDR 'bad-cidr'" in str(exc)
    finally:
        settings.trusted_proxy_cidrs = old_cidrs


def test_internal_url_accepts_single_label_service_hostnames():
    assert _is_internal_url("http://evm-node:8545")
    assert _is_internal_url("https://db:5432")


def test_inhouse_only_runtime_validation_blocks_external_dependencies():
    old_inhouse = settings.inhouse_only_mode
    old_sovereign = settings.sovereign_mode
    old_stripe = settings.enable_external_stripe_webhooks
    old_walletconnect = settings.enable_external_walletconnect
    old_admin_legacy = settings.admin_allow_legacy_api_tokens
    old_public_web_mode = settings.public_web_mode
    old_rpc = settings.evm_rpc_url
    settings.inhouse_only_mode = True
    settings.sovereign_mode = False
    settings.enable_external_stripe_webhooks = True
    settings.enable_external_walletconnect = True
    settings.admin_allow_legacy_api_tokens = True
    settings.public_web_mode = True
    settings.evm_rpc_url = "https://mainnet.infura.io/v3/example"
    try:
        try:
            validate_inhouse_only_settings()
            assert False, "expected RuntimeError for inhouse-only misconfiguration"
        except RuntimeError as exc:
            message = str(exc)
            assert "sovereign_mode must be true" in message
            assert "enable_external_stripe_webhooks must be false" in message
            assert "enable_external_walletconnect must be false" in message
            assert "admin_allow_legacy_api_tokens must be false" in message
            assert "public_web_mode must be false" in message
            assert "evm_rpc_url must be internal/private" in message
    finally:
        settings.inhouse_only_mode = old_inhouse
        settings.sovereign_mode = old_sovereign
        settings.enable_external_stripe_webhooks = old_stripe
        settings.enable_external_walletconnect = old_walletconnect
        settings.admin_allow_legacy_api_tokens = old_admin_legacy
        settings.public_web_mode = old_public_web_mode
        settings.evm_rpc_url = old_rpc


def test_private_or_loopback_ip_helper():
    assert _is_private_or_loopback_ip("10.1.2.3")
    assert _is_private_or_loopback_ip("192.168.1.25")
    assert _is_private_or_loopback_ip("127.0.0.1")
    assert not _is_private_or_loopback_ip("8.8.8.8")
    assert not _is_private_or_loopback_ip("not-an-ip")


def test_public_runtime_validation_allows_no_walletconnect_in_inhouse_only_mode():
    old_env = settings.app_env
    old_public_web_mode = settings.public_web_mode
    old_walletconnect = settings.enable_external_walletconnect
    old_inhouse = settings.inhouse_only_mode
    old_admin_legacy = settings.admin_allow_legacy_api_tokens
    old_admin_bootstrap = settings.admin_bootstrap_enabled
    old_origins = settings.cors_origins
    settings.app_env = "prod"
    settings.public_web_mode = True
    settings.enable_external_walletconnect = False
    settings.inhouse_only_mode = True
    settings.admin_allow_legacy_api_tokens = False
    settings.admin_bootstrap_enabled = False
    settings.cors_origins = "https://app.victoryimpact.local"
    try:
        validate_public_runtime_settings()
    finally:
        settings.app_env = old_env
        settings.public_web_mode = old_public_web_mode
        settings.enable_external_walletconnect = old_walletconnect
        settings.inhouse_only_mode = old_inhouse
        settings.admin_allow_legacy_api_tokens = old_admin_legacy
        settings.admin_bootstrap_enabled = old_admin_bootstrap
        settings.cors_origins = old_origins


def test_inhouse_payment_intent_checkout_and_one_time_capture():
    db = build_db()
    ensure_default_categories(db)
    old_checkout_base = settings.inhouse_checkout_app_base_url
    settings.inhouse_checkout_app_base_url = "https://app.victory.local"
    try:
        intent = payments.create_payment_intent(
            PaymentIntentCreate(
                donor_email="checkout@example.org",
                category=DonationCategoryCode.MERCY,
                payment_method="card",
                amount=Decimal("25.00"),
                currency="USD",
            ),
            db,
        )
        assert intent.checkout_url is not None
        assert intent.checkout_url.startswith("https://app.victory.local/checkout?intent_id=")

        details = payments.get_payment_intent(intent.intent_id, db)
        assert details.status == "pending"

        capture_payload = PaymentCapturePayload(
            donor_email="checkout@example.org",
            category=DonationCategoryCode.MERCY,
            amount=Decimal("25.00"),
            currency="USD",
            payment_reference=intent.intent_id,
        )
        captured = payments.capture_payment(capture_payload, db)
        assert captured.receipt_id

        try:
            payments.capture_payment(capture_payload, db)
            assert False, "expected second capture to fail"
        except HTTPException as exc:
            assert exc.status_code == 409
            assert "already captured" in str(exc.detail)
    finally:
        settings.inhouse_checkout_app_base_url = old_checkout_base


def test_admin_payment_intent_listing_includes_pending_and_captured():
    db = build_db()
    ensure_default_categories(db)
    old_checkout_base = settings.inhouse_checkout_app_base_url
    settings.inhouse_checkout_app_base_url = "https://app.victory.local"
    try:
        pending_intent = payments.create_payment_intent(
            PaymentIntentCreate(
                donor_email="ops@example.org",
                category=DonationCategoryCode.MERCY,
                payment_method="card",
                amount=Decimal("10.00"),
                currency="USD",
            ),
            db,
        )
        captured_intent = payments.create_payment_intent(
            PaymentIntentCreate(
                donor_email="ops@example.org",
                category=DonationCategoryCode.WIDOW,
                payment_method="bank",
                amount=Decimal("15.00"),
                currency="USD",
            ),
            db,
        )
        payments.capture_payment(
            PaymentCapturePayload(
                donor_email="ops@example.org",
                category=DonationCategoryCode.WIDOW,
                amount=Decimal("15.00"),
                currency="USD",
                payment_reference=captured_intent.intent_id,
            ),
            db,
        )

        rows = admin.list_payment_intents(donor_email="ops@example.org", db=db, role="admin")
        assert len(rows) >= 2
        statuses = {row.intent_id: row.status for row in rows}
        assert statuses[pending_intent.intent_id] == "pending"
        assert statuses[captured_intent.intent_id] == "captured"

        captured_rows = admin.list_payment_intents(status="captured", donor_email="ops@example.org", db=db, role="admin")
        assert any(row.intent_id == captured_intent.intent_id for row in captured_rows)
        assert all(row.status == "captured" for row in captured_rows)
    finally:
        settings.inhouse_checkout_app_base_url = old_checkout_base


def test_admin_payment_intent_listing_requires_admin_or_board_role():
    db = build_db()
    try:
        try:
            admin.list_payment_intents(db=db, role="donor")
            assert False, "expected HTTPException for donor role"
        except HTTPException as exc:
            assert exc.status_code == 403
    finally:
        db.close()


def test_admin_payment_intent_bulk_actions_expire_and_replay():
    db = build_db()
    ensure_default_categories(db)
    old_checkout_base = settings.inhouse_checkout_app_base_url
    settings.inhouse_checkout_app_base_url = "https://app.victory.local"
    try:
        first = payments.create_payment_intent(
            PaymentIntentCreate(
                donor_email="bulk@example.org",
                category=DonationCategoryCode.MERCY,
                payment_method="card",
                amount=Decimal("12.00"),
                currency="USD",
            ),
            db,
        )
        second = payments.create_payment_intent(
            PaymentIntentCreate(
                donor_email="bulk@example.org",
                category=DonationCategoryCode.ELDER,
                payment_method="bank",
                amount=Decimal("18.00"),
                currency="USD",
            ),
            db,
        )

        expire_result = admin.bulk_action_payment_intents(
            payload=AdminPaymentIntentBulkActionRequest(
                action="expire",
                intent_ids=[first.intent_id, second.intent_id],
            ),
            db=db,
            role="admin",
        )
        assert expire_result["updated"] == 2

        replay_result = admin.bulk_action_payment_intents(
            payload=AdminPaymentIntentBulkActionRequest(
                action="replay",
                intent_ids=[first.intent_id],
            ),
            db=db,
            role="admin",
        )
        assert replay_result["updated"] == 1
        assert len(replay_result["replayed"]) == 1
        assert replay_result["replayed"][0]["source_intent_id"] == first.intent_id
    finally:
        settings.inhouse_checkout_app_base_url = old_checkout_base
