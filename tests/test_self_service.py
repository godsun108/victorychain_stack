from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.victory_impact.models import Base, DonationCategoryCode
from src.victory_impact.config import settings
from src.victory_impact.main import validate_sovereign_runtime_settings
from src.victory_impact.policies import runtime_policies
from src.victory_impact.services.donations import create_donation_and_token, ensure_default_categories, get_or_create_donor
from src.victory_impact.services.payment_adapters import EVMIndexerAdapter, InHouseCardBankAdapter, VUSDAdapter


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
            return {"tx_hash": tx_hash, "status": "confirmed", "confirmations": 3, "receipt": {}}

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
