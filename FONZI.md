# Fonzi — Portable Character Identity

Status: concept contract / pre-implementation. This document does **not** claim a
deployed NFT collection, bridge, token, airdrop, game integration, or Victory L1.

## Product idea

Fonzi is a portable character whose home is Victory.

The collectible begins as a small **pixel travel form**. The pixel artwork remains
part of the character's persistent identity and is not replaced or burned when a
richer manifestation becomes available.

When a compatible Fonzi arrives at Victory, Victory may recognize the canonical
identity and unlock or associate a second **Victory home form**: richer character
art and, eventually, a usable avatar/character experience.

Other compatible environments may render their own local manifestation while
preserving the same root identity and provenance.

```
PIXEL TRAVEL FORM
      |
      | prove/control canonical Fonzi identity
      v
VICTORY HOME FORM
      |
      +--> Portal manifestation
      +--> game manifestation
      +--> web/AR manifestation
      +--> external-chain representation
```

**Identity persists. Representation changes.**

## Narrative rule

> Fonzi travels light. Between worlds, he's pixels. At home, he's himself.

Fonzi is a fourth-wall-breaking collaborator and traveler. Interoperability should
feel like character behavior rather than a wallet-integration advertisement.

Victory is home base. Portal may be an encounter/travel surface, but Portal does
not own Fonzi identity.

## Ownership boundary

Victory owns the canonical Fonzi identity/provenance contract.

A future implementation should separate:

1. **Root identity** — stable Fonzi identifier and canonical provenance.
2. **Pixel travel art** — persistent collectible representation.
3. **Victory manifestation** — linked home-form artwork/metadata; additional, not
   a destructive replacement.
4. **Environment manifestations** — local renderings/adapters for games, sites,
   AR, or other chains.
5. **Visit/achievement attestations** — optional signed receipts from compatible
   environments. A claimed visit is never treated as verified without evidence.

The root identity should not require the original asset to cross a risky bridge
for every appearance. Where possible, environments verify ownership/control and
render a local manifestation.

## Marketing / access intent

Fonzi may serve as a playful discovery and access layer for Victory: collectible
ownership can eventually unlock experiences, cosmetics, quests, early access,
events, promotional items, or explicitly defined airdrops.

Those capabilities must be versioned and stated precisely. Ownership must not be
presented as a promise of profit, yield, appreciation, revenue share, or pooled
investment return. Any future treasury/fund concept is a separate design and legal
review boundary, not an implicit Fonzi entitlement.

## Fourth-wall behavior

Fonzi should not become a conventional banner advertisement or static mascot.

Good integrations let Fonzi:
- appear where a normal navigation object should not;
- acknowledge the environment he entered;
- retain recognizable pixel travel form between worlds;
- reveal a richer local form where supported;
- leave verifiable travel receipts where an integration actually supports them;
- occasionally help, interrupt, reveal, or connect experiences.

The character may break fictional/UI rules. He may **not** bypass authorization,
security policy, wallet consent, access control, or asset ownership rules.

## Proposed interoperability contract

A future adapter should be able to resolve, without assuming a particular chain:

- `fonzi_id`
- root provenance reference
- current controller/ownership proof
- pixel travel-form media + immutable/content-addressed hash where available
- known Victory manifestation reference
- supported environment capabilities
- signed attestations/receipts
- metadata/schema version

Chain-specific NFT contracts are representations of this identity model, not the
definition of Fonzi itself.

## First canonical incursion

The Portal contains an intentionally tiny, browser-local Fonzi encounter. It is an
experience prototype only: no wallet check, NFT ownership, on-chain state, or
financial entitlement is implied.

Its purpose is to test the fiction: Fonzi can appear outside the normal room
taxonomy and behave as though he crossed a system boundary.

## Implementation gates

Before a public mint or cross-chain release:

1. recover/confirm Victory's actual chain and asset implementation state;
2. freeze a versioned Fonzi identity + metadata schema;
3. choose canonical settlement/ownership chain(s) deliberately;
4. content-address and preserve both pixel and home-form art;
5. implement wallet/control verification without exposing private keys;
6. test replay, spoofing, duplicate IDs and bridge/adapter failure modes;
7. define exact access/airdrop terms;
8. obtain appropriate contract/security and legal review before value-bearing use.

Until those gates are met, Fonzi remains a product/interop specification plus
experimental Portal character.
