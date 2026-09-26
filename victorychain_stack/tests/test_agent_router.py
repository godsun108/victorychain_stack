import pytest
from src.victory_impact.agent_protocol import AgentIdentity, AgentRequest
from src.victory_impact.agent_router import AgentRegistration, AgentRegistry

def ident(name,caps=("read","reason","propose")):
    return AgentIdentity(name,name,"1",caps)

def req(action="analyze.property"):
    return AgentRequest("r1",ident("orchestrator"),action,"base-one",{"parcel":"demo"})

def test_routes_only_matching_domain_and_action_in_stable_order():
    r=AgentRegistry()
    r.register(AgentRegistration(ident("property"),("property",),("analyze.property",),20))
    r.register(AgentRegistration(ident("ryln"),("finance","property"),("analyze.property",),10))
    r.register(AgentRegistration(ident("churchcodex"),("software",),("*",),1))
    p=r.route(req(),domain="property")
    assert p.selected_agent_ids==("ryln","property")
    assert not p.external_authorization_required

def test_disabled_agent_not_routed():
    r=AgentRegistry()
    r.register(AgentRegistration(ident("off"),("property",),("analyze.property",),1,False))
    with pytest.raises(ValueError,match="no eligible"):
        r.route(req(),domain="property")

def test_duplicate_agent_rejected():
    r=AgentRegistry(); a=AgentRegistration(ident("ryln"),("finance",),("*",))
    r.register(a)
    with pytest.raises(ValueError,match="duplicate"):
        r.register(a)

def test_privileged_request_is_flagged_not_silently_authorized():
    r=AgentRegistry()
    r.register(AgentRegistration(ident("treasury-advisor"),("treasury",),("treasury.pay",),1))
    p=r.route(req("treasury.pay"),domain="treasury")
    assert p.selected_agent_ids==("treasury-advisor",)
    assert p.external_authorization_required

def test_plan_fingerprint_is_reproducible():
    r=AgentRegistry()
    r.register(AgentRegistration(ident("ryln"),("property",),("analyze.property",),10))
    a=r.route(req(),domain="property"); b=r.route(req(),domain="property")
    assert a.fingerprint()==b.fingerprint()
