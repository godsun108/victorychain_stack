# Victory Assistant

Status: research orchestration skeleton, not a deployed assistant.

Victory Assistant is the conversational shell for the Victory Intelligence
Network. Sa'lioren may become a principal conversational identity after its
newest implementation is recovered; the protocol does not depend on one persona
or model provider.

## Lifecycle

1. Human conversation produces a versioned ConversationIntent.
2. Intent is bound to a canonical AgentRequest.
3. Deterministic routing selects eligible agents.
4. Agents use bounded tools and return provenance-bearing responses.
5. CouncilBundle preserves every response and disagreement.
6. A synthesizer produces a SynthesisRecord bound to the Council fingerprint.
7. A ProposedAction is bound to request + synthesis.
8. Privileged effects leave AI authority and enter deterministic policy and
   cryptographic authorization.
9. Only an independently authorized transaction may reach protocol execution.

Conversation -> Intent -> Request -> Route -> Evidence -> Council -> Synthesis
-> Proposal -> Policy -> Signature -> Protocol

## Non-authority rule

Conversation is not authorization.
Intent classification is not authorization.
Agent selection is not authorization.
Council agreement is not authorization.
Synthesis is not authorization.
A proposed transaction is not authorization.

## Privacy

Conversation content should remain off public-chain state by default. Public
commitments may contain hashes/proofs/receipts where useful, but private
plaintext should not be published merely to make the assistant auditable.

## Provider portability

Model provider, model ID, agent identity and protocol identity are distinct.
Victory should be able to use local models, hosted models, or multiple providers
without changing the authorization semantics.

## Next gates

- bind communications envelopes to conversation turns
- signed agent/service registrations
- response/tool receipt persistence
- authorization-ceremony adapter to Victory Identity
- prompt/tool-injection adversarial suite
- local/private model provider adapters
- recover Sa'lioren, ChurchCodex, ChurchChat and later RYLN implementations
