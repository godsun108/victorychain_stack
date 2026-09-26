from datetime import datetime,timezone
import pytest
from src.victory_impact.orchestrator import ConversationIntent,ProposedAction
from src.victory_impact.assistant_authorization import challenge_from_proposal

NOW=datetime(2026,9,27,12,0,tzinfo=timezone.utc)
def intent(action="treasury.pay",resource="treasury"):
 return ConversationIntent("s","t","did:victory:alice","treasury",action,resource,{})
def proposal(**kw):
 d=dict(request_digest="a"*64,synthesis_digest="b"*64,action="treasury.pay",resource="treasury",parameters={"amount":"10","asset":"vUSD"},external_authorization_required=True)
 d.update(kw); return ProposedAction(**d)

def test_challenge_binds_exact_proposal_digest():
 p=proposal(); c=challenge_from_proposal(intent=intent(),proposal=p,nonce="n",issued_at=NOW)
 assert c.challenge_id=="proposal:"+p.digest()
 assert c.actor=="did:victory:alice"
 assert c.suite_id=="victory-hybrid-v1"

def test_parameter_mutation_changes_challenge():
 a=proposal(parameters={"amount":"10"}); b=proposal(parameters={"amount":"11"})
 ca=challenge_from_proposal(intent=intent(),proposal=a,nonce="n",issued_at=NOW)
 cb=challenge_from_proposal(intent=intent(),proposal=b,nonce="n",issued_at=NOW)
 assert ca.challenge_id!=cb.challenge_id

def test_nonprivileged_proposal_cannot_enter_ceremony():
 p=proposal(action="analyze.property",resource="property",external_authorization_required=False)
 with pytest.raises(ValueError,match="does not require"):
  challenge_from_proposal(intent=intent("analyze.property","property"),proposal=p,nonce="n",issued_at=NOW)

def test_intent_substitution_fails():
 with pytest.raises(ValueError,match="intent"):
  challenge_from_proposal(intent=intent(resource="other"),proposal=proposal(),nonce="n",issued_at=NOW)

@pytest.mark.parametrize("ttl",[0,-1,901])
def test_ttl_is_bounded(ttl):
 with pytest.raises(ValueError,match="ttl"):
  challenge_from_proposal(intent=intent(),proposal=proposal(),nonce="n",issued_at=NOW,ttl_seconds=ttl)
