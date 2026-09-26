import pytest
from src.victory_impact.agent_evidence import AgentResponse

D="a"*64
def response(**kw):
 d=dict(request_digest=D,agent_id="ryln",agent_version="1",model_provider="local",model_id="m1",output={"x":1},evidence_refs=("state:1",),tool_receipt_digests=(),uncertainty="medium")
 d.update(kw); return AgentResponse(**d)

def test_response_digest_reproducible(): assert response().digest()==response().digest()
def test_output_mutation_changes_digest(): assert response(output={"x":1}).digest()!=response(output={"x":2}).digest()
def test_bad_request_digest_fails():
 with pytest.raises(ValueError,match="request digest"): response(request_digest="bad").validate()
