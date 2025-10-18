# Governance and Compliance

Scope
- Applies to VictoryChain Trillion Bot governance, approvals, and guardrails

Key controls
- Emergency lockdown (deny-all) with immutable ledger events
- Approval tokens: HMAC-SHA256 using APPROVAL_SECRET
  - Live mode: real APPROVAL_SECRET required (no fallback)
  - Paper/CI: deterministic fallback allowed
- Guardrails: forbid raw ccxt imports except allowlist in adapter

Audit trail
- Ledger events include: ts, event, component, prompt_hash, git_commit
- Proof artifacts: proof.log + reports/** (daily bundle filename includes prompt hash)

CI policy
- GitHub Actions runs Paper-Mode Proof end-to-end
- Artifacts uploaded for verification and audit

Runbook
- See docs/RUNBOOK.md for operational steps and validation
