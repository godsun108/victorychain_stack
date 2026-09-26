# Victory PQ Evidence Policy

Victory separates algorithm standards, implementation evidence, and deployment approval.

FIPS 203 defines ML-KEM and FIPS 204 defines ML-DSA. A local round-trip test is research evidence, not NIST validation. NIST CAVP records validation for a specific implementation and operating environment.

## Evidence ladder

- unit: Victory interface and harness behavior
- research-smoke: a concrete provider performs selected operations
- known-answer: provider passes authoritative fixed vectors
- ACVP/CAVP: evidence tied to validation data for the exact implementation/environment
- integration: replay, downgrade, rotation, corruption, and interoperability tests
- reviewed: independent security review

## Required negative testing

ML-DSA testing includes valid verification plus rejection of altered messages and signatures. ML-KEM testing must extend beyond happy-path shared-secret equality to applicable validation and malformed-input behavior supported by the provider.

## Promotion rule

Research evidence never automatically authorizes deployment with meaningful value. Promotion is an explicit policy decision after the required evidence exists.
