# Victory Archaeology — AI & Communications Recovery Map

Status: recovery inventory, 2026-09-27.

This file distinguishes repository-confirmed code from previously recorded
implementations and from concepts. It exists to prevent duplicate rebuilds and
overclaiming.

## Evidence classes

- **A — repository-confirmed:** visible in an accessible GitHub repository now.
- **B — prior implementation record:** prior project work records exact code paths
  or runtime artifacts, but those files are not visible in the current canonical
  Victory repository and must be recovered before reuse.
- **C — architecture/concept:** named or designed, but no surviving implementation
  has yet been verified.

## Intelligence systems

| System | Class | Recovered evidence | Canonical direction |
|---|---|---|---|
| RYLN | A/B | Separate private repo `godsun108/ryln-ai` contains LSTM/TensorFlow market model/training and Binance-US bot code. Later records describe RYLN as an advisor/local service. | Recover newest generation; do not treat early trading bot as final RYLN. |
| VictoryBot / GenesisCore | A/B | Current Victory tree contains `src/victory_bot/` and extensive legacy AI/trading code. Prior records name `genesis_core.py`, multicore/advisor/risk integration. | Preserve as specialized market intelligence; isolate from protocol authority. |
| VictoryAdvisor | B | Prior records name report/replay/dashboard/anchor scripts and multi-advisor work. | Recover exact latest files before integration. |
| ChurchCodex | B | Prior records name `services/church_codex/service.py`. | Recover; classify code-writing/reasoning permissions before activation. |
| ChurchChat AI / Sa’lioren | B | Prior records name `services/church_chat/service.py` and later local-provider integration. | Recover as conversational intelligence, never signing authority. |
| Sa’lioren Council / AI Synod | C/B | Recorded multi-agent/council architecture; surviving canonical implementation not yet verified. | Reconstruct only after recovery search. |
| Scrollkeeper / Ledgerkeeper / Archivist | C/B | Recorded specialized agent roles; exact surviving implementation not yet verified. | Define least-privilege read/write scopes. |
| Guardian / Sentinel | A/B | Sentinel naming/artifacts exist in legacy trading tree; broader guardian role recorded. | Separate market safety from protocol/security sentinel. |
| Agent economy | C/B | Prior architecture includes agent identity, permissions, escrow/wallet/service economy. | Require bounded identities, budgets, policy and audit trails. |

## Communications systems

| System | Class | Recovered evidence | Canonical direction |
|---|---|---|---|
| ChurchChat Native | B | Prior records name `services/church_chat/service.py` and `native_church_chat.py`; identity-bound rooms, membership, private-message hashes, moderation, receipts, Postgres storage. | Recover source; preserve private-content boundary. |
| QuantumChat | B/C | Prior capability map records `services/quantum_compute` as research/operator-lab communications/intelligence work. | Keep experimental until recovered and threat-modeled. |
| Victory bot communications | A | Current tree contains `intelligent_bot_communicator.py`, FastAPI agent, Rust WebSocket code and backend AI analyzer. | Audit as legacy transport/orchestration building blocks. |
| Mesh/offline/local-first | B | Prior audit records `docs/victory_resilience_mesh_offline_audit.md` and a mesh/offline inventory report. No iPhone/LoRa hardware field validation was recorded. | Recover software; hardware claims require field evidence. |
| Pulse/notifications | C/B | Prior records say centralized Pulse/webhook/email/Slack/SMS/notification-bell wiring was incomplete. | Build only behind explicit user notification policy. |
| Voice/video | C | No surviving implementation verified in this pass. | Future communications module; do not claim built. |

## Canonical architecture

```
Human / Organization
        |
Victory Interface (chat / app / API)
        |
+---------------- Victory Intelligence ----------------+
| Sa’lioren | RYLN | ChurchCodex | Advisors | Council |
| specialist agents | security/observability agents     |
+-------------------------------------------------------+
        |
Policy + Tool Permission Boundary
        |
+--------------- Victory Communications ---------------+
| ChurchChat | private rooms/DM | receipts | local/P2P |
| mesh/offline research | notifications | future media |
+-------------------------------------------------------+
        |
Victory Identity / Authorization
        |
Deterministic Victory Protocol
        |
Consensus / State / Proofs / Settlement
```

## Authority invariant

AI and communications services MAY observe authorized data, reason, summarize,
simulate, retrieve, communicate and prepare proposed actions.

They MUST NOT gain consensus authority, root/governance authority, minting
authority, treasury authority, or custody of a user's signing secrets merely
because an AI model or communications service requested an action.

Privileged effects require deterministic policy plus explicit cryptographic
authorization appropriate to the action.

## Recovery order

1. Preserve repository-confirmed code without rewriting it.
2. Recover exact latest ChurchCodex, ChurchChat, VictoryAdvisor and GenesisCore
   implementations from surviving artifacts/history.
3. Recover Sa’lioren/Council and specialist-agent implementations where present.
4. Recover mesh/offline audits and distinguish simulation from field evidence.
5. Define one versioned agent/tool protocol and one communications envelope.
6. Only then consolidate services into the canonical Victory stack.

## Truth rule

A remembered or documented subsystem is not called current implementation until
its source is recovered and tested. Missing code is a recovery target, not an
invitation to silently recreate a different system under the same name.
