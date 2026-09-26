import pytest
from src.victory_impact.agent_protocol import AgentIdentity, AgentRequest, requires_external_authorization

def agent(**kw):
    d=dict(agent_id="ryln:1",service="ryln",version="1",capabilities=("read","reason","propose"))
    d.update(kw); return AgentIdentity(**d)

def test_agent_request_is_canonical():
    a=AgentRequest("r1",agent(),"analyze","market",{"b":2,"a":1})
    b=AgentRequest("r1",agent(),"analyze","market",{"a":1,"b":2})
    assert a.digest()==b.digest()

def test_agent_cannot_claim_signing_authority():
    with pytest.raises(ValueError,match="forbidden"):
        agent(capabilities=("read","sign")).validate()

def test_unknown_capability_fails():
    with pytest.raises(ValueError,match="unknown"):
        agent(capabilities=("telepathy",)).validate()

@pytest.mark.parametrize("action",["transfer.asset","sign.tx","mint.token","treasury.pay","governance.execute","validator.rotate","consensus.vote","upgrade.protocol","key.rotate"])
def test_privileged_actions_leave_ai_authority(action):
    assert requires_external_authorization(action)

def test_reasoning_does_not_require_privileged_authority():
    assert not requires_external_authorization("analyze.market")
