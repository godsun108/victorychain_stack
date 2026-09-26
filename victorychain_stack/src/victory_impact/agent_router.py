"""Deterministic discovery and routing for Victory agents.

Routing selects eligible agents; it does not authorize the requested effect.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Iterable
from .agent_protocol import AgentIdentity, AgentRequest, requires_external_authorization


@dataclass(frozen=True)
class AgentRegistration:
    identity: AgentIdentity
    domains: tuple[str, ...]
    actions: tuple[str, ...]
    priority: int = 100
    enabled: bool = True

    def validate(self) -> None:
        self.identity.validate()
        if not self.domains or not self.actions:
            raise ValueError("agent registration requires domains and actions")
        if self.priority < 0:
            raise ValueError("priority must be non-negative")


@dataclass(frozen=True)
class RoutingPlan:
    request_digest: str
    selected_agent_ids: tuple[str, ...]
    external_authorization_required: bool
    reason: str

    def fingerprint(self) -> str:
        body = {
            "version": 1,
            "request_digest": self.request_digest,
            "selected_agent_ids": self.selected_agent_ids,
            "external_authorization_required": self.external_authorization_required,
            "reason": self.reason,
        }
        raw=json.dumps(body,sort_keys=True,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, AgentRegistration] = {}

    def register(self, registration: AgentRegistration) -> None:
        registration.validate()
        key=registration.identity.agent_id
        if key in self._agents:
            raise ValueError("duplicate agent id")
        self._agents[key]=registration

    def route(self, request: AgentRequest, *, domain: str) -> RoutingPlan:
        digest=request.digest()
        eligible: list[AgentRegistration]=[]
        for reg in self._agents.values():
            if not reg.enabled:
                continue
            if domain not in reg.domains and "*" not in reg.domains:
                continue
            if request.action not in reg.actions and "*" not in reg.actions:
                continue
            eligible.append(reg)
        eligible.sort(key=lambda r:(r.priority,r.identity.agent_id))
        if not eligible:
            raise ValueError("no eligible agent")
        return RoutingPlan(
            request_digest=digest,
            selected_agent_ids=tuple(r.identity.agent_id for r in eligible),
            external_authorization_required=requires_external_authorization(request.action),
            reason="eligible_by_declared_domain_action_priority",
        )
