"""Victory Agent Protocol (VAP) v1 research boundary.

AI agents may request tools and prepare proposals. This protocol deliberately
does not grant signing, treasury, minting, governance, or consensus authority.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import hashlib, json
from typing import Any


class AgentCapability(str, Enum):
    READ = "read"
    REASON = "reason"
    COMMUNICATE = "communicate"
    PROPOSE = "propose"
    TOOL_REQUEST = "tool_request"


FORBIDDEN_IMPLICIT_AUTHORITIES = frozenset({
    "sign", "treasury", "mint", "governance_execute", "consensus", "root"
})


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    service: str
    version: str
    capabilities: tuple[str, ...]

    def validate(self) -> None:
        if not self.agent_id or not self.service or not self.version:
            raise ValueError("agent identity fields must be non-empty")
        caps = set(self.capabilities)
        if caps & FORBIDDEN_IMPLICIT_AUTHORITIES:
            raise ValueError("agent requests forbidden implicit authority")
        allowed = {c.value for c in AgentCapability}
        if not caps <= allowed:
            raise ValueError("unknown agent capability")


@dataclass(frozen=True)
class AgentRequest:
    request_id: str
    agent: AgentIdentity
    action: str
    resource: str
    payload: dict[str, Any] = field(default_factory=dict)
    evidence_refs: tuple[str, ...] = ()

    def digest(self) -> str:
        self.agent.validate()
        if not self.request_id or not self.action or not self.resource:
            raise ValueError("request fields must be non-empty")
        body = {
            "version": 1,
            "request_id": self.request_id,
            "agent": self.agent.__dict__,
            "action": self.action,
            "resource": self.resource,
            "payload": self.payload,
            "evidence_refs": self.evidence_refs,
        }
        return hashlib.sha256(_canonical(body)).hexdigest()


def requires_external_authorization(action: str) -> bool:
    """Privileged effects always leave the AI protocol for policy/signature auth."""
    prefixes = ("transfer", "sign", "mint", "burn", "treasury", "governance.execute",
                "validator", "consensus", "upgrade", "key.")
    return action.startswith(prefixes)
