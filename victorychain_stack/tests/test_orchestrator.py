import pytest
from src.victory_impact.agent_protocol import AgentIdentity,AgentRequest
from src.victory_impact.agent_router import AgentRegistration,AgentRegistry
from src.victory_impact.agent_evidence import AgentResponse
from src.victory_impact.council import CouncilBundle
from src.victory_impact.orchestrator import ConversationIntent,VictoryOrchestrator,ProposedAction

def ident(n): return AgentIdentity(n,n,"1",("read","reason","propose"))
def setup(action="analyze.property"):
 reg=AgentRegistry(); reg.register(AgentRegistration(ident("ryln"),("property","treasury"),(action,),1))
 req=AgentRequest("r1",ident("assistant"),action,"base-one",{"x":1})
 intent=ConversationIntent("s1","t1","did:alice","property" if action.startswith("analyze") else "treasury",action,"base-one",{"x":1})
 return VictoryOrchestrator(reg),intent,req

def council(req):
 d=req.digest()
 return CouncilBundle(d,(AgentResponse(d,"ryln","1","local","m1",{"answer":"x"}),))

def test_end_to_end_research_plan_synthesis_proposal():
 o,i,r=setup(); p=o.plan(i,r)
 assert p.selected_agent_ids==("ryln",)
 s=o.synthesize(r,council(r),"assistant",{"summary":"x"})
 a=o.propose(r,s,{"note":"no effect"})
 assert not a.external_authorization_required
 assert len(a.digest())==64

def test_intent_request_mismatch_fails():
 o,i,r=setup()
 bad=AgentRequest("r1",ident("assistant"),"different","base-one",{})
 with pytest.raises(ValueError,match="intent"): o.plan(i,bad)

def test_foreign_council_fails():
 o,i,r=setup()
 c=CouncilBundle("b"*64,(AgentResponse("b"*64,"ryln","1","local","m1",{}),))
 with pytest.raises(ValueError,match="council"): o.synthesize(r,c,"assistant",{})

def test_privileged_proposal_requires_external_authorization():
 o,i,r=setup("treasury.pay"); o.plan(i,r)
 s=o.synthesize(r,council(r),"assistant",{"summary":"prepare payment"})
 a=o.propose(r,s,{"amount":"10","asset":"vUSD"})
 assert a.external_authorization_required

def test_privileged_action_cannot_be_relabelled_unprivileged():
 with pytest.raises(ValueError,match="bypass"):
  ProposedAction("a"*64,"b"*64,"treasury.pay","treasury",{},False).digest()
