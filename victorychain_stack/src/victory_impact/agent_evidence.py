"""Provenance-bearing outputs for Victory Intelligence."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any

def _canon(v: Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

@dataclass(frozen=True)
class AgentResponse:
    request_digest: str
    agent_id: str
    agent_version: str
    model_provider: str
    model_id: str
    output: dict[str, Any]
    evidence_refs: tuple[str,...]=()
    tool_receipt_digests: tuple[str,...]=()
    uncertainty: str|None=None

    def validate(self)->None:
        if not all((self.request_digest,self.agent_id,self.agent_version,self.model_provider,self.model_id)):
            raise ValueError("response provenance fields must be non-empty")
        if len(self.request_digest)!=64:
            raise ValueError("invalid request digest")
        for d in self.tool_receipt_digests:
            if len(d)!=64:
                raise ValueError("invalid tool receipt digest")

    def digest(self)->str:
        self.validate()
        return hashlib.sha256(_canon(self.__dict__)).hexdigest()
