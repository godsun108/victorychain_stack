"""Bounded tool manifests and receipts for Victory agents."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Any
from .agent_protocol import requires_external_authorization

def _canon(v: Any)->bytes:
    return json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()

@dataclass(frozen=True)
class ToolManifest:
    tool_id: str
    version: str
    actions: tuple[str,...]
    read_only: bool=True

    def validate(self)->None:
        if not self.tool_id or not self.version or not self.actions:
            raise ValueError("invalid tool manifest")
        if self.read_only and any(requires_external_authorization(a) for a in self.actions):
            raise ValueError("read-only tool advertises privileged action")

    def permits(self, action:str)->bool:
        self.validate()
        return action in self.actions

@dataclass(frozen=True)
class ToolReceipt:
    tool_id: str
    tool_version: str
    action: str
    request_digest: str
    result_digest: str
    privileged: bool

    def digest(self)->str:
        if len(self.request_digest)!=64 or len(self.result_digest)!=64:
            raise ValueError("invalid receipt digest")
        return hashlib.sha256(_canon(self.__dict__)).hexdigest()

def make_receipt(manifest:ToolManifest, action:str, request_digest:str, result:Any)->ToolReceipt:
    if not manifest.permits(action):
        raise ValueError("tool action not permitted")
    result_digest=hashlib.sha256(_canon(result)).hexdigest()
    return ToolReceipt(manifest.tool_id,manifest.version,action,request_digest,result_digest,
                       requires_external_authorization(action))
