from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import requests
try:
    import stripe  # type: ignore
except ImportError:  # pragma: no cover
    stripe = None


@dataclass
class PaymentIntent:
    intent_id: str
    provider: str
    payment_method: str
    amount: Decimal
    currency: str
    status: str
    checkout_url: str | None = None


class StripeWebhookVerifier:
    """Verifies Stripe-style webhook signatures using signing secret."""

    def __init__(self, signing_secret: str, tolerance_seconds: int = 300):
        self.signing_secret = signing_secret
        self.tolerance_seconds = tolerance_seconds

    def verify(self, payload_bytes: bytes, stripe_signature: str | None) -> bool:
        if not stripe_signature or not self.signing_secret:
            return False

        parts = {}
        for item in stripe_signature.split(","):
            if "=" in item:
                key, value = item.split("=", 1)
                parts.setdefault(key.strip(), []).append(value.strip())

        ts_values = parts.get("t", [])
        sig_values = parts.get("v1", [])
        if not ts_values or not sig_values:
            return False

        try:
            ts = int(ts_values[0])
        except ValueError:
            return False

        now = int(datetime.now(UTC).timestamp())
        if abs(now - ts) > self.tolerance_seconds:
            return False

        signed_payload = f"{ts}.{payload_bytes.decode('utf-8')}"
        expected = hmac.new(
            self.signing_secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return any(hmac.compare_digest(expected, sig) for sig in sig_values)


class StripeSDKEventParser:
    """Parses and verifies Stripe webhook events using Stripe's official SDK."""

    def __init__(self, signing_secret: str):
        self.signing_secret = signing_secret

    def parse_event(self, payload_bytes: bytes, stripe_signature: str | None):
        if stripe is None:
            return None
        if not stripe_signature:
            raise ValueError("missing stripe signature")
        if not self.signing_secret:
            raise ValueError("missing stripe webhook secret")
        try:
            return stripe.Webhook.construct_event(
                payload=payload_bytes,
                sig_header=stripe_signature,
                secret=self.signing_secret,
            )
        except Exception as exc:
            raise ValueError(f"stripe verification failed: {exc}") from exc


class InHouseCardBankAdapter:
    """Provider-neutral interface for card and bank payments."""

    def create_intent(self, payment_method: str, amount: Decimal, currency: str, donor_email: str) -> PaymentIntent:
        ts = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        intent_id = f"inhouse-{payment_method}-{ts}"
        return PaymentIntent(
            intent_id=intent_id,
            provider="inhouse_gateway",
            payment_method=payment_method,
            amount=amount,
            currency=currency,
            status="pending",
            checkout_url=f"https://payments.local/checkout/{intent_id}?donor={donor_email}",
        )


class EVMIndexerAdapter:
    """Simple EVM RPC/indexer verifier for in-house operation."""

    def __init__(self, rpc_url: str, required_confirmations: int = 1):
        self.rpc_url = rpc_url
        self.required_confirmations = required_confirmations

    def _rpc(self, method: str, params: list) -> dict:
        response = requests.post(
            self.rpc_url,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise RuntimeError(payload["error"])
        return payload.get("result")

    def verify_chain_payment(self, tx_hash: str, min_confirmations: int | None = None) -> dict:
        receipt = self._rpc("eth_getTransactionReceipt", [tx_hash])
        if not receipt:
            return {"tx_hash": tx_hash, "status": "pending", "confirmations": 0}

        block_hex = receipt.get("blockNumber")
        if not block_hex:
            return {"tx_hash": tx_hash, "status": "pending", "confirmations": 0}

        tx_block = int(block_hex, 16)
        head_hex = self._rpc("eth_blockNumber", [])
        head_block = int(head_hex, 16)
        confirmations = max(head_block - tx_block, 0)

        required = min_confirmations if min_confirmations is not None else self.required_confirmations
        status_ok = receipt.get("status") in {"0x1", 1, "1"}
        confirmed = status_ok and confirmations >= required

        return {
            "tx_hash": tx_hash,
            "confirmations": confirmations,
            "required_confirmations": required,
            "status": "confirmed" if confirmed else "pending",
            "receipt": receipt,
        }


class VUSDAdapter:
    def __init__(self, indexer: EVMIndexerAdapter, contract_address: str):
        self.indexer = indexer
        self.contract_address = contract_address.lower()

    def verify_vusd_transfer_event(self, event_payload: dict) -> dict:
        tx_hash = event_payload.get("tx_hash")
        contract_address = (event_payload.get("contract_address") or "").lower()
        if not tx_hash:
            return {"status": "rejected", "reason": "missing tx_hash", "raw": event_payload}
        if contract_address and contract_address != self.contract_address:
            return {"status": "rejected", "reason": "contract mismatch", "raw": event_payload}

        chain_verification = self.indexer.verify_chain_payment(tx_hash)
        if chain_verification["status"] != "confirmed":
            return {"status": "pending", "verification": chain_verification, "raw": event_payload}

        return {
            "event_id": event_payload.get("event_id", f"vusd-{tx_hash}"),
            "status": "verified",
            "verification": chain_verification,
            "raw": event_payload,
        }
