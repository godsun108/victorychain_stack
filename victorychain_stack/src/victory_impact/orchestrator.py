"""Victory Assistant orchestration records.

This module binds conversational intent to deterministic routing, Council
evidence, synthesis provenance, and an explicit authorization boundary.
It does not call models or execute privileged effects.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any
from .agent_protocol import AgentRequest, requires_external_authorization
from .agent_router import AgentRegistry, RoutingPlan
from .council import CouncilBundle

def _canon(v: Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

@dataclass(frozen=True)
class ConversationIntent:
    session_id: str
    turn_id: str
    actor: str
    domain: str
    action: str
    resource: str
    payload: dict[str,Any]

    def validate(self)->None:
        if not all((self.session_id,self.turn_id,self.actor,self.domain,self.action,self.resource)):
            raise ValueError("intent fields must be non-empty")

    def digest(self)->str:
        self.validate()
        return hashlib.sha256(_canon({"version":1,**self.__dict__})).hexdigest()

@dataclass(frozen=True)
class SynthesisRecord:
    request_digest: str
    council_fingerprint: str
    synthesizer_agent_id: str
    output: dict[str,Any]
    disagreement_refs: tuple[str,...]=()

    def digest(self)->str:
        if len(self.request_digest)!=64 or len(self.council_fingerprint)!=64:
            raise ValueError("invalid synthesis provenance")
        if not self.synthesizer_agent_id:
            raise ValueError("missing synthesizer")
        return hashlib.sha256(_canon(self.__dict__)).hexdigest()

@dataclass(frozen=True)
class ProposedAction:
    request_digest: str
    synthesis_digest: str
    action: str
    resource: str
    parameters: dict[str,Any]
    external_authorization_required: bool

    def digest(self)->str:
        if len(self.request_digest)!=64 or len(self.synthesis_digest)!=64:
            raise ValueError("invalid proposal provenance")
        if not self.action or not self.resource:
            raise ValueError("invalid proposed action")
        if requires_external_authorization(self.action) and not self.external_authorization_required:
            raise ValueError("privileged action cannot bypass authorization")
        return hashlib.sha256(_canon(self.__dict__)).hexdigest()

class VictoryOrchestrator:
    def __init__(self, registry:AgentRegistry)->None:
        self.registry=registry

    def plan(self,intent:ConversationIntent,request:AgentRequest)->RoutingPlan:
        intent.validate()
        if request.action!=intent.action or request.resource!=intent.resource:
            raise ValueError("request does not match conversational intent")
        return self.registry.route(request,domain=intent.domain)

    def synthesize(self,request:AgentRequest,council:CouncilBundle,
                   synthesizer_agent_id:str,output:dict[str,Any],
                   disagreement_refs:tuple[str,...]=())->SynthesisRecord:
        rd=request.digest()
        council.validate()
        if council.request_digest!=rd:
            raise ValueError("council does not match request")
        return SynthesisRecord(rd,council.fingerprint(),synthesizer_agent_id,
                               output,disagreement_refs)

    def propose(self,request:AgentRequest,synthesis:SynthesisRecord,
                parameters:dict[str,Any])->ProposedAction:
        rd=request.digest()
        if synthesis.request_digest!=rd:
            raise ValueError("synthesis does not match request")
        return ProposedAction(rd,synthesis.digest(),request.action,request.resource,
                              parameters,requires_external_authorization(request.action))
