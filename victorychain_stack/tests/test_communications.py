from datetime import datetime, timezone, timedelta
import pytest
from src.victory_impact.communications import CommunicationEnvelope, MessageReplayGuard

FIXTURE_TIME = datetime.now(timezone.utc)

def msg(**kw):
    d=dict(message_id="m1",sender="did:victory:alice",recipient="agent:ryln",channel="direct",kind="request",created_at=FIXTURE_TIME,nonce="n1",payload={"b":2,"a":1})
    d.update(kw); return CommunicationEnvelope(**d)

def test_message_digest_is_canonical():
    a=msg(payload={"b":2,"a":1})
    b=msg(payload={"a":1,"b":2})
    assert a.digest()==b.digest()

def test_replay_fails_closed():
    guard=MessageReplayGuard(); m=msg()
    guard.consume(m)
    with pytest.raises(ValueError,match="replay"):
        guard.consume(m)

def test_naive_timestamp_rejected():
    with pytest.raises(ValueError,match="timezone"):
        msg(created_at=datetime(2026,9,27)).validate()

def test_far_future_message_rejected():
    now=datetime(2026,9,27,tzinfo=timezone.utc)
    with pytest.raises(ValueError,match="future"):
        msg(created_at=now+timedelta(minutes=2)).validate(now=now)

def test_payload_mutation_changes_digest():
    assert msg(payload={"x":1}).digest()!=msg(payload={"x":2}).digest()
