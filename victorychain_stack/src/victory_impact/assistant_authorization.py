"""Bridge Victory Assistant proposals into Victory Identity challenges.

The Assistant prepares an exact challenge; it never signs it.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import hashlib
from .identity import AuthorizationChallenge
from .orchestrator import ConversationIntent, ProposedAction

def challenge_from_proposal(
    *,
    intent: ConversationIntent,
    proposal: ProposedAction,
    nonce: str,
    issued_at: datetime,
    ttl_seconds: int = 300,
    suite_id: str = "victory-hybrid-v1",
) -> AuthorizationChallenge:
    if not proposal.external_authorization_required:
        raise ValueError("proposal does not require external authorization")
    if proposal.action != intent.action or proposal.resource != intent.resource:
        raise ValueError("proposal does not match conversational intent")
    if ttl_seconds <= 0 or ttl_seconds > 900:
        raise ValueError("authorization ttl outside allowed range")
    if issued_at.tzinfo is None:
        raise ValueError("issued_at must be timezone-aware")
    issued=issued_at.astimezone(timezone.utc)
    expires=issued+timedelta(seconds=ttl_seconds)
    # Bind the challenge id to the exact proposal so changing parameters creates
    # a different ceremony even when action/resource are unchanged.
    challenge_id="proposal:"+proposal.digest()
    return AuthorizationChallenge(
        version=1,
        challenge_id=challenge_id,
        actor=intent.actor,
        action=proposal.action,
        resource=proposal.resource,
        nonce=nonce,
        issued_at=issued.isoformat(),
        expires_at=expires.isoformat(),
        suite_id=suite_id,
    )
