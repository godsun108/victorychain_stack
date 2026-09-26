"""Deterministic Council evidence bundle.

The Council preserves member outputs and disagreements. Natural-language
synthesis may be produced separately; this layer never fabricates consensus.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from .agent_evidence import AgentResponse

@dataclass(frozen=True)
class CouncilBundle:
    request_digest: str
    responses: tuple[AgentResponse,...]

    def validate(self)->None:
        if not self.responses:
            raise ValueError("council requires responses")
        ids=set()
        for r in self.responses:
            r.validate()
            if r.request_digest!=self.request_digest:
                raise ValueError("response belongs to different request")
            if r.agent_id in ids:
                raise ValueError("duplicate council agent")
            ids.add(r.agent_id)

    def member_digests(self)->tuple[tuple[str,str],...]:
        self.validate()
        return tuple(sorted((r.agent_id,r.digest()) for r in self.responses))

    def fingerprint(self)->str:
        body={"version":1,"request_digest":self.request_digest,
              "members":self.member_digests()}
        raw=json.dumps(body,sort_keys=True,separators=(",",":")).encode()
        return hashlib.sha256(raw).hexdigest()

    def outputs(self)->dict[str,dict]:
        self.validate()
        return {r.agent_id:r.output for r in self.responses}
