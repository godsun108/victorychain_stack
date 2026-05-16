import hashlib
import hmac
import json
from datetime import UTC, datetime

from src.victory_impact.services import payment_adapters
from src.victory_impact.services.payment_adapters import EVMIndexerAdapter, StripeSDKEventParser, StripeWebhookVerifier, VUSDAdapter


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_stripe_signature_verifier_accepts_valid_signature():
    secret = "whsec_test"
    payload = {"type": "payment_intent.succeeded"}
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ts = int(datetime.now(UTC).timestamp())
    signed = f"{ts}.{payload_bytes.decode('utf-8')}"
    sig = hmac.new(secret.encode("utf-8"), signed.encode("utf-8"), hashlib.sha256).hexdigest()

    verifier = StripeWebhookVerifier(secret)
    header = f"t={ts},v1={sig}"
    assert verifier.verify(payload_bytes, header) is True


def test_stripe_signature_verifier_rejects_bad_signature():
    verifier = StripeWebhookVerifier("whsec_test")
    payload_bytes = b'{"type":"bad"}'
    assert verifier.verify(payload_bytes, "t=123,v1=deadbeef") is False


def test_stripe_sdk_event_parser_with_mocked_sdk(monkeypatch):
    class FakeWebhook:
        @staticmethod
        def construct_event(payload, sig_header, secret):
            assert payload == b'{"type":"payment_intent.succeeded"}'
            assert sig_header == "sig"
            assert secret == "whsec_test"
            return {"id": "evt_1", "type": "payment_intent.succeeded"}

    class FakeStripe:
        Webhook = FakeWebhook

    monkeypatch.setattr(payment_adapters, "stripe", FakeStripe)
    parser = StripeSDKEventParser("whsec_test")
    event = parser.parse_event(b'{"type":"payment_intent.succeeded"}', "sig")
    assert event["type"] == "payment_intent.succeeded"


def test_evm_indexer_and_vusd_verification(monkeypatch):
    def fake_post(url, json, timeout):
        method = json["method"]
        if method == "eth_getTransactionReceipt":
            return DummyResponse(
                {
                    "result": {
                        "transactionHash": "0xabc",
                        "status": "0x1",
                        "blockNumber": hex(100)
                    }
                }
            )
        if method == "eth_blockNumber":
            return DummyResponse({"result": hex(105)})
        return DummyResponse({"result": None})

    monkeypatch.setattr("requests.post", fake_post)

    indexer = EVMIndexerAdapter("http://rpc.local", required_confirmations=3)
    result = indexer.verify_chain_payment("0xabc")
    assert result["status"] == "confirmed"
    assert result["confirmations"] == 5

    vusd = VUSDAdapter(indexer, "0x0000000000000000000000000000000000000000")
    verification = vusd.verify_vusd_transfer_event(
        {
            "tx_hash": "0xabc",
            "contract_address": "0x0000000000000000000000000000000000000000",
            "event_id": "ev-abc"
        }
    )
    assert verification["status"] == "verified"
