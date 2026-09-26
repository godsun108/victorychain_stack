from datetime import datetime, timezone

import pytest

from src.victory_impact.identity import AuthorizationChallenge, ReplayGuard, identity_manifest


NOW = datetime(2026, 9, 26, 19, 0, tzinfo=timezone.utc)


def challenge(**overrides):
    values = dict(
        version=1,
        challenge_id="challenge-001",
        actor="did:victory:alice",
        action="attestation:create",
        resource="victory:record:123",
        nonce="nonce-unique-001",
        issued_at="2026-09-26T18:59:00Z",
        expires_at="2026-09-26T19:05:00Z",
        suite_id="victory-hybrid-v1",
    )
    values.update(overrides)
    return AuthorizationChallenge(**values)


def test_canonical_digest_is_stable():
    assert challenge().digest() == challenge().digest()
    assert len(challenge().digest()) == 64


@pytest.mark.parametrize("field,value", [
    ("actor", "did:victory:bob"),
    ("action", "attestation:delete"),
    ("resource", "victory:record:999"),
    ("nonce", "other-nonce"),
    ("suite_id", "victory-classical-v1"),
])
def test_security_relevant_mutation_changes_digest(field, value):
    assert challenge(**{field: value}).digest() != challenge().digest()


def test_expired_challenge_rejected():
    with pytest.raises(ValueError, match="expired"):
        challenge(expires_at="2026-09-26T18:59:30Z").validate(now=NOW)


def test_future_challenge_rejected():
    with pytest.raises(ValueError, match="not active"):
        challenge(
            issued_at="2026-09-26T19:01:00Z",
            expires_at="2026-09-26T19:05:00Z",
        ).validate(now=NOW)


def test_replay_is_rejected():
    guard = ReplayGuard()
    item = challenge()
    guard.consume(item, now=NOW)
    with pytest.raises(ValueError, match="already consumed"):
        guard.consume(item, now=NOW)


def test_identity_has_no_funds_or_soul_key_authority():
    manifest = identity_manifest()
    assert manifest["funds_authority"] == "disabled"
    assert manifest["soul_key_authority"] == "none"
    assert manifest["server_key_custody"] == "none"
