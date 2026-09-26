# Victory Ecosystem Map

Status: canonical product architecture + recovery targets. A named plane is not
a claim that its current implementation is complete.

## Foundation

Victory Protocol
- identity and hybrid authorization
- deterministic state/proofs
- governance/policy
- assets/RWA/restoration
- treasury/settlement
- interoperability

## Intelligence

Victory Assistant / Sa'lioren, RYLN, ChurchCodex, VictoryAdvisor,
GenesisCore/VictoryBot, Council/Synod, Guardian/Sentinel, record agents.

## Communications

ChurchChat, identity-bound rooms/DMs, receipts, local/P2P/mesh/offline research,
notifications, and future voice/video transports.

## Social

Recovery target: Victory-native social profiles, posts, follows/communities,
creator identity, moderation, provenance and portable social graph.

Design boundary: ordinary social content should not be forced on-chain. Use
content storage plus optional commitments/receipts where verifiability matters.

## Media & Streaming

Recovery target: live/video/audio streaming, creator channels, music/media,
subscriptions/tipping and provenance.

Design boundary: blockchain is suitable for identity, rights, receipts and
settlement—not bulk media transport. Streaming requires a dedicated media/CDN/
P2P delivery plane.

## Victory News

Recovery target: news aggregation/publishing, source provenance, timestamped
claims, corrections, multi-source comparison and AI-assisted summaries.

Design boundary: provenance does not make a claim true. News AI must preserve
sources, distinguish reporting from inference/opinion, and retain corrections.

## Quantum Applications

Recovery target: inventory all previously built/designed quantum apps before
consolidation.

Canonical categories:
- post-quantum security (production-security research track)
- quantum computation/optimization experiments
- QRNG/randomness experiments
- quantum networking/communications research
- quantum simulation/science apps
- experimental quantum-AI applications

Scientific boundary: label simulation, quantum-inspired algorithms, real quantum
hardware, and post-quantum cryptography separately. Do not imply quantum
advantage, consciousness sensing, or physical effects without evidence.

## Gaming

Recovery target: Victory gaming runtime/ecosystem, player identity, achievements,
items/assets, tournaments, social play, creator content and optional economy.

Design boundary: game logic should remain performant and fun off-chain where
appropriate. Chain state is reserved for ownership/provenance/settlement that
actually benefits from consensus. AI agents cannot spend player assets without
authorization.

## Shared substrate

All product planes should reuse, where appropriate:
- Victory Identity
- Victory Communications Envelope
- Victory Agent Protocol
- provenance/evidence receipts
- deterministic policy
- user-controlled authorization
- portable service identities
- common observability
- explicit privacy boundaries

They should NOT each invent incompatible identity, messaging, wallet, AI
authority or provenance systems.

## Recovery rule

Before rebuilding Social, Streaming, News, Quantum or Gaming, search surviving
repositories/files/history and classify each recovered component:
A repository-confirmed; B prior implementation awaiting recovery; C concept/spec.

Preserve the strongest surviving implementation and migrate deliberately.
