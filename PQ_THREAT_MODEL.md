# Victory Post-Quantum Threat Model

Status: research/testnet architecture.

## Assets

Victory protects signing authority, identity attestations, treasury approvals,
audit evidence, confidential session material, and long-lived records.

## Adversaries

- ordinary credential theft and phishing
- repository or CI compromise
- malicious dependency/update
- replay and downgrade attacks
- compromised signing host
- future cryptanalytically relevant quantum computer
- forged or misleading research evidence

## Required properties

1. Crypto agility: every protected object identifies a supported versioned suite.
2. Downgrade resistance: PQ-required policy rejects classical-only negotiation.
3. Dual-domain separation: experimental Soul Key evidence never becomes a signing key.
4. Key isolation: secret keys and recovery material never enter Git or evidence artifacts.
5. Evidence provenance: provider/version, parameter set, test class and fingerprint are preserved.
6. Failure visibility: malformed/tampered data fails closed.
7. Rotation: identities and protected objects must support replacement of algorithms and keys.
8. Replay defense: authorization protocols must bind challenge, actor, action, resource, expiry and nonce.
9. Least authority: cryptographic validity alone never grants a role or treasury permission.
10. Dependency containment: research PQ providers remain separate from the production dependency set until promoted.

## Hybrid rule

Hybrid does not mean concatenating cryptographic outputs ad hoc. A production
hybrid protocol must use a reviewed construction/profile. Victory's current
hybrid suite is an application policy target, not a home-grown combiner.

## Harvest-now-decrypt-later

Long-lived confidential material is the highest-priority migration target.
Where confidentiality must survive future quantum capability, transport/storage
design should move toward vetted PQ/hybrid key establishment before lower-value,
short-lived data.

## Non-goals

- proving a soul or consciousness field
- quantum randomness as identity
- claiming an EVM transaction is PQ-secure when the underlying account/chain is not
- replacing mature authorization policy with cryptographic novelty

## Promotion gates

Research -> known-answer vectors -> validation evidence -> integration
replay/downgrade/rotation tests -> key custody design -> independent review ->
explicit deployment approval.
