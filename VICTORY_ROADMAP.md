# Victory Reformation Roadmap

## Gate 0 — Preserve and tell the truth

- Canonical architecture map committed.
- Security audit committed.
- Legacy trading and Victory Impact explicitly separated conceptually.
- Unimplemented chain concepts labeled roadmap rather than shipped capability.

## Gate 1 — Security boundary

- Rotate any historically committed credentials.
- Remove tracked secret backups and rewrite secret-bearing Git history.
- Replace literal role tokens with fail-closed authentication.
- Add explicit authorization tests for donor/admin/board/compliance boundaries.
- Separate trading and impact runtime secrets.

## Gate 2 — Testnet Victory identity

Build challenge -> signature -> verified address -> server-side role/policy.

No biometric or Soul Key data on-chain. No seed phrases/private keys in application storage.

## Gate 3 — Public proof layer

Upgrade shared-secret HMAC audit proofs to a versioned asymmetric attestation/notary scheme. Preserve canonical payload fingerprints and append-only evidence.

## Gate 4 — Registry modules

Implement separately testable modules before calling them protocol features:

- identity attestations
- scroll/document notarization
- RWA registry
- restoration/impact registry

Each gets schemas, threat model, tests, migration strategy and testnet evidence.

## Gate 5 — vUSD research

Specify issuance/redemption, reserves, custody, settlement, oracle assumptions, failure modes and legal/compliance boundaries before implementing value-bearing stablecoin behavior. Begin with a testnet/mock ledger.

## Gate 6 — Victory protocol

Only after earlier gates pass should the project decide whether a dedicated Cosmos-SDK chain is justified versus using existing EVM infrastructure.

## Gate 7 — Soul Key experiment bridge

Victory can consume a versioned presence **attestation** as non-authoritative metadata. Cryptographic wallet authorization remains independent unless a future security review explicitly promotes a validated conventional factor.

## Definition of progress

A feature is not "built" because a document names it. It is built when implementation, tests, threat model and reproducible evidence agree.
