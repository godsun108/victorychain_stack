import copy

import pytest

from src.victory_impact.protocol_state import ProtocolState, Transaction


def tx(**overrides):
    values = dict(
        version=1,
        tx_id="tx-1",
        actor="did:victory:alice",
        domain="identity",
        operation="put",
        payload={"key": "alice", "value": {"status": "active"}},
    )
    values.update(overrides)
    return Transaction(**values)


def test_same_state_and_input_produce_same_commitment():
    a, b = ProtocolState(), ProtocolState()
    a.apply(tx())
    b.apply(tx())
    assert a.commitment() == b.commitment()


def test_canonical_payload_order_does_not_change_transaction_digest():
    left = tx(payload={"key": "alice", "value": {"b": 2, "a": 1}})
    right = tx(payload={"value": {"a": 1, "b": 2}, "key": "alice"})
    assert left.digest() == right.digest()


def test_transaction_replay_fails_closed():
    state = ProtocolState()
    item = tx()
    state.apply(item)
    with pytest.raises(ValueError, match="replay"):
        state.apply(item)


@pytest.mark.parametrize(
    "bad",
    [
        tx(version=2),
        tx(operation="delete"),
        tx(payload={"value": 1}),
        tx(payload={"key": "x"}),
    ],
)
def test_invalid_transition_does_not_mutate_state(bad):
    state = ProtocolState()
    before = copy.deepcopy(state)
    with pytest.raises(ValueError):
        state.apply(bad)
    assert state == before
    assert state.commitment() == before.commitment()


def test_order_is_explicit_and_state_commitment_detects_it():
    first = tx(tx_id="1", payload={"key": "x", "value": 1})
    second = tx(tx_id="2", payload={"key": "x", "value": 2})
    a, b = ProtocolState(), ProtocolState()
    a.apply(first); a.apply(second)
    b.apply(second); b.apply(first)
    assert a.commitment() != b.commitment()
