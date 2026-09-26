# Victory Identity v0.1

Victory Identity v0.1 binds an authenticated intent to an actor, action and
resource using a short-lived, single-use challenge.

## Canonical authorization

A challenge commits to:

- version and challenge ID
- actor
- action
- resource
- nonce
- issuance and expiry
- cryptographic suite

The canonical JSON is SHA-256 digested before it enters a signature envelope.
Changing any security-relevant field changes the digest.

## Authorization flow

1. Server creates a cryptographically random nonce and short-lived challenge.
2. Client displays the requested action and resource to the human.
3. Client signs the exact canonical challenge digest using the required suite.
4. Server verifies identity/key binding, suite policy, signatures and expiry.
5. Server atomically consumes the challenge before executing the authorized action.
6. Audit log records the challenge digest, key identifiers and outcome, never private keys.

The in-memory ReplayGuard is a test/reference boundary only. Production replay
protection requires an atomic shared datastore with uniqueness/expiry semantics.

## Security boundaries

- No seed phrase or private signing key belongs in Victory source, CI, logs or server configuration.
- Hybrid policy requires both signature components when enabled; signature stripping must fail closed.
- A Soul Key research signal may be metadata only and has no authorization role.
- Identity v0.1 has no treasury or funds authority.
- The liboqs smoke result is research evidence, not certification or production approval.

## Next gates

A production candidate requires a mature classical/passkey verifier, provider-backed
ML-DSA verification, key registration and rotation, atomic replay storage, explicit
role/policy mapping, downgrade and revoked-key tests, authoritative vector evidence,
and independent security review.
