# Victory Quantum Security v0.1

Status: **architecture + policy scaffold; not production cryptography**

Victory uses the term **quantum security** to mean migration toward standardized post-quantum cryptography (PQC), not an assertion that quantum hardware or consciousness provides authentication.

## Standards target

- FIPS 203 / ML-KEM: post-quantum key establishment
- FIPS 204 / ML-DSA: primary post-quantum digital signatures
- FIPS 205 / SLH-DSA: hash-based signature alternative / diversity

Implementations must use maintained, independently reviewed cryptographic libraries. Victory will not invent its own ML-KEM, ML-DSA, SLH-DSA, hash, KDF, RNG, or signature primitive.

## v0.1 policy

The default target suite is `victory-hybrid-v1`:

- conventional signature + ML-DSA
- conventional key establishment + ML-KEM

The application layer is crypto-agile: records carry a versioned suite identifier so algorithms can be migrated without redefining the business object.

Classical-only downgrade is rejected by the PQ policy boundary by default.

## Why hybrid

Migration is a systems problem, not merely an algorithm swap. Hybrid operation lets Victory retain an established conventional path while PQ implementations and interoperability mature. The exact production combiner/protocol must follow a vetted standard/protocol profile rather than an ad-hoc construction.

## Key custody

- private keys never belong in Git;
- seed phrases never belong in application logs or chat;
- production signing should be hardware-backed where practical;
- privileged actions require explicit policy authorization;
- rotation/recovery/revocation are first-class operations;
- algorithm identifiers and public keys are versioned.

## QRNG

A documented quantum random-number generator may be evaluated as an additional entropy source. It is not required for PQC and is never assumed to detect identity, consciousness, intent, or presence. A vetted OS CSPRNG remains the baseline.

## Blockchain boundary

Existing EVM chains may continue to rely on chain-native signatures at the transaction layer. PQ protection can initially secure Victory's off-chain identity, attestations, approvals, archives and communication. Claims of fully PQ-secure on-chain settlement require the underlying chain/account model to support it.

## Soul Key boundary

Soul Key can eventually emit a versioned experimental presence attestation. That attestation has **zero signing authority**. Presence evidence and cryptographic authorization remain separate security domains.

## Promotion gate

No meaningful funds rely on this layer until:

1. a vetted PQ library/provider is selected;
2. official test vectors pass;
3. interoperability tests pass;
4. downgrade/replay/key-rotation tests pass;
5. secrets are removed from repository history and rotated;
6. threat modeling is complete;
7. independent security review is complete.

Until then, the quantum-security module is a policy and test harness only.
