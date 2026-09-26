from datetime import datetime, timezone

import pytest

from src.victory_impact.key_registry import KeyRegistry, PublicKeyRecord


NOW = datetime(2026, 9, 26, 20, 0, tzinfo=timezone.utc)


def key(key_id="k1", actor="did:victory:alice", purpose="authorization", material=b"pk1"):
    return PublicKeyRecord(
        key_id=key_id,
        actor=actor,
        purpose=purpose,
        algorithm="ML-DSA-65",
        public_key=material,
        created_at="2026-09-26T19:00:00Z",
    )


def test_register_and_require_active():
    registry = KeyRegistry()
    registry.register(key())
    assert registry.require_active("k1", actor="did:victory:alice", purpose="authorization").fingerprint


def test_private_key_is_not_a_registry_field():
    assert "secret_key" not in PublicKeyRecord.__dataclass_fields__
    assert "private_key" not in PublicKeyRecord.__dataclass_fields__


def test_duplicate_active_purpose_rejected():
    registry = KeyRegistry()
    registry.register(key())
    with pytest.raises(ValueError, match="active key"):
        registry.register(key(key_id="k2", material=b"pk2"))


def test_wrong_actor_rejected():
    registry = KeyRegistry()
    registry.register(key())
    with pytest.raises(ValueError, match="not bound"):
        registry.require_active("k1", actor="did:victory:bob", purpose="authorization")


def test_rotation_retires_old_and_activates_new():
    registry = KeyRegistry()
    registry.register(key())
    registry.rotate("k1", key(key_id="k2", material=b"pk2"), at=NOW)
    old = registry.get("k1")
    assert old.status == "rotated"
    assert old.replaced_by == "k2"
    assert registry.require_active("k2", actor=old.actor, purpose=old.purpose).status == "active"
    with pytest.raises(ValueError, match="not active"):
        registry.require_active("k1", actor=old.actor, purpose=old.purpose)


def test_revoked_key_cannot_authorize():
    registry = KeyRegistry()
    registry.register(key())
    registry.revoke("k1", at=NOW)
    with pytest.raises(ValueError, match="not active"):
        registry.require_active("k1", actor="did:victory:alice", purpose="authorization")


def test_rotation_cannot_cross_actor_boundary():
    registry = KeyRegistry()
    registry.register(key())
    with pytest.raises(ValueError, match="not bound"):
        registry.rotate(
            "k1",
            key(key_id="k2", actor="did:victory:bob", material=b"pk2"),
            at=NOW,
        )
