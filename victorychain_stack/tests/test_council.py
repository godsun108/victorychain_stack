import pytest
from src.victory_impact.agent_evidence import AgentResponse
from src.victory_impact.council import CouncilBundle
D="a"*64

def r(agent,out):
 return AgentResponse(D,agent,"1","local","m1",out)

def test_council_preserves_disagreement():
 c=CouncilBundle(D,(r("ryln",{"verdict":"yes"}),r("guardian",{"verdict":"no"})))
 assert c.outputs()["ryln"]!=c.outputs()["guardian"]

def test_council_fingerprint_independent_of_input_order():
 a=r("ryln",{"x":1}); b=r("guardian",{"x":2})
 assert CouncilBundle(D,(a,b)).fingerprint()==CouncilBundle(D,(b,a)).fingerprint()

def test_foreign_request_response_rejected():
 with pytest.raises(ValueError,match="different request"):
  CouncilBundle(D,(r("ryln",{}),AgentResponse("b"*64,"guardian","1","local","m1",{}))).validate()

def test_duplicate_agent_rejected():
 with pytest.raises(ValueError,match="duplicate"):
  CouncilBundle(D,(r("ryln",{"x":1}),r("ryln",{"x":2}))).validate()
