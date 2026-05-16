from __future__ import annotations

from ..services.payment_adapters import VUSDAdapter


def process_stripe_payload(payload_json: dict) -> None:
    if payload_json.get("simulate_failure") is True:
        raise RuntimeError("simulated stripe webhook processing failure")


def process_vusd_payload(payload_json: dict, vusd_adapter: VUSDAdapter) -> None:
    if payload_json.get("simulate_failure") is True:
        raise RuntimeError("simulated vUSD webhook processing failure")
    verification = vusd_adapter.verify_vusd_transfer_event(payload_json)
    if verification.get("status") != "verified":
        raise RuntimeError(f"vUSD verification not final: {verification.get('status')}")


def process_webhook_event(provider: str, payload_json: dict, vusd_adapter: VUSDAdapter) -> None:
    if provider in {"stripe", "stripe-fallback"}:
        process_stripe_payload(payload_json)
        return
    if provider == "vusd":
        process_vusd_payload(payload_json, vusd_adapter)
        return
    raise RuntimeError(f"unsupported provider for processing: {provider}")
