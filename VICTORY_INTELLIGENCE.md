# Victory Intelligence Network

Status: research architecture.

Victory Intelligence is a network of bounded agents, not a single omnipotent
model. The conversational assistant is the human-facing orchestrator.

## Flow

Human -> Victory Assistant -> canonical AgentRequest -> deterministic discovery
-> eligible specialist agents -> evidence/proposals -> synthesis -> policy gate
-> explicit cryptographic authorization for privileged effects.

## Initial recovered roles

- Sa'lioren: conversational/orchestration identity; implementation recovery pending.
- RYLN: financial/analytical intelligence; early repository generation recovered.
- ChurchCodex: software/code specialist; prior implementation recovery pending.
- VictoryAdvisor: advisory/reporting specialist; recovery pending.
- GenesisCore/VictoryBot: market research/trading specialist; legacy code recovered.
- Council/Synod: critique/multi-agent deliberation; recovery pending.
- Guardian/Sentinel: security/risk/observability role; must remain bounded.
- Scrollkeeper/Ledgerkeeper/Archivist: evidence and record specialists.

Names describe roles, not authority.

## Routing invariants

1. Agents advertise explicit domains/actions/capabilities.
2. Routing is deterministic for the same registry and request.
3. Disabled or ineligible agents are not selected.
4. Selection does not equal authorization.
5. Privileged actions are flagged for external policy/signature authorization.
6. Routing plans are fingerprintable for audit/replay.
7. Model provider is replaceable; protocol identity is not tied to one vendor.
8. Evidence references should survive synthesis so a final answer can be traced
   to its inputs and participating agents.

## ChatGPT-like interface

Victory Assistant should support ordinary conversation while internally using
structured requests. It may retrieve authorized state, call specialist agents,
compare outputs, explain transactions, prepare actions and maintain user-approved
context. It must never hide the exact privileged action that will be signed.

## Next gates

- recover newest agent implementations
- signed/versioned agent registrations
- provenance-bearing agent responses
- bounded tool manifests
- council/synthesis protocol
- communication-envelope integration
- durable registry and replay store
- adversarial prompt/tool injection tests
- model-provider adapters and local/private inference
