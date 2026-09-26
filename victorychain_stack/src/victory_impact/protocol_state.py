"""Deterministic Victory protocol-state research model.

This is not a blockchain or consensus engine. It provides a small canonical
state-transition kernel so protocol invariants can be attacked before choosing
an L1 framework.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


@dataclass(frozen=True)
class Transaction:
    version: int
    tx_id: str
    actor: str
    domain: str
    operation: str
    payload: dict[str, Any]

    def digest(self) -> str:
        return hashlib.sha256(canonical_json(self.__dict__)).hexdigest()


@dataclass
class ProtocolState:
    protocol_version: int = 1
    height: int = 0
    domains: dict[str, dict[str, Any]] = field(default_factory=dict)
    applied_transactions: set[str] = field(default_factory=set)

    def commitment(self) -> str:
        body = {
            "protocol_version": self.protocol_version,
            "height": self.height,
            "domains": self.domains,
            "applied_transactions": sorted(self.applied_transactions),
        }
        return hashlib.sha256(canonical_json(body)).hexdigest()

    def apply(self, tx: Transaction) -> None:
        if tx.version != self.protocol_version:
            raise ValueError("protocol version mismatch")
        if not tx.tx_id or not tx.actor or not tx.domain or not tx.operation:
            raise ValueError("transaction fields must be non-empty")
        digest = tx.digest()
        if digest in self.applied_transactions:
            raise ValueError("transaction replay")
        if tx.operation != "put":
            raise ValueError("unsupported research operation")
        key = tx.payload.get("key")
        if not isinstance(key, str) or not key:
            raise ValueError("put requires non-empty string key")
        if "value" not in tx.payload:
            raise ValueError("put requires value")

        # Validate completely before mutation.
        domain = dict(self.domains.get(tx.domain, {}))
        domain[key] = tx.payload["value"]
        self.domains[tx.domain] = domain
        self.applied_transactions.add(digest)
        self.height += 1
