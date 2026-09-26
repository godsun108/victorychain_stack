# Victory Architecture — Canonical Map

Status: architecture audit, 2026-09-26.

Victory currently contains two materially different systems in one repository. This document prevents their boundaries from being confused.

## A. Legacy trading/research system

The repository root is primarily an AI/cryptocurrency trading and portfolio automation codebase. It contains trading strategies, exchange integration, analytics, MCP tooling, runtime artifacts, historical reports, backups, logs, model artifacts and generated outputs.

**Policy:** preserve it as legacy/research until intentionally extracted. Do not treat trading automation as the canonical Victory protocol or treasury.

## B. Victory Impact

The nested `victorychain_stack/` directory is the cleaner current application boundary. It contains:

- FastAPI impact/donation backend
- relational schema and models
- beneficiary/disbursement workflows
- governance and compliance scaffolding
- payment/webhook adapters
- transparency/audit-proof services
- React frontend
- Wagmi/WalletConnect integration for Ethereum, Base and Polygon
- Solidity impact receipt, treasury-routing and disbursement contract stubs

This is the current canonical application foundation.

## C. What is NOT currently demonstrated

Repository inspection did **not** find an implemented Cosmos-SDK chain, native identity module, scroll/notary module, RWA registry, or native vUSD stablecoin protocol in the current tree.

Those remain roadmap concepts unless/until code and tests establish them.

## Canonical future layers

```
Human / Organization
        |
Identity & Authentication
        |
Policy / Governance
        |
Assets / Receipts / RWA Registry
        |
Treasury & Settlement
        |
Transparency / Audit Proofs
        |
External chains & payment rails
```

AI systems are advisers/observers around this stack, not privileged key holders.

## Soul Key boundary

Soul Key may eventually supply an experimental presence attestation. It MUST NOT hold a Victory private key, derive a private key from biometrics, or independently authorize value transfer. Production authorization must use established cryptographic challenge/signature authentication with explicit policy.

## Separation objective

The next architectural milestone is not a destructive rewrite. It is to:

1. freeze a canonical boundary around `victorychain_stack/`;
2. harden authentication and secret handling;
3. establish testnet-only contract integration;
4. define identity/notary/RWA/vUSD as separately testable modules;
5. extract or archive legacy trading concerns only after reproducibility is preserved.
