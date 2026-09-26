# Victory PQ Conformance

Status: **provider-neutral harness; no production PQ provider selected**

Victory does not implement ML-KEM or ML-DSA primitives itself.

The application boundary now exposes a provider protocol for:

- ML-KEM key generation, encapsulation and decapsulation
- ML-DSA key generation, signing and verification
- explicit standardized parameter-set allowlists

The conformance harness accepts normalized verification/decapsulation vectors so authoritative test data can be exercised against a selected provider without changing Victory business logic.

## Evidence ladder

1. Application interface exists.
2. Synthetic harness tests pass.
3. Vetted provider selected and version pinned.
4. Authoritative known-answer / validation vectors pass.
5. Hybrid integration, downgrade, replay and key-rotation tests pass.
6. Threat model and independent review complete.
7. Only then consider promotion toward value-bearing use.

A synthetic/fake provider proves only that the Victory harness works. It does **not** establish that ML-KEM or ML-DSA has been correctly implemented.

## Standards boundary

Victory targets FIPS 203 (ML-KEM) and FIPS 204 (ML-DSA). NIST ACVP algorithm specifications define validation testing for their component operations. Victory should preserve the exact provider/version and validation evidence used for any promoted implementation.

## Financial boundary

No provider is production-approved yet. The PQ layer therefore has no independent authority over production funds.
