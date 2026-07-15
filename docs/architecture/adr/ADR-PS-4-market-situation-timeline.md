# ADR-PS-4: Immutable Market Situation Timeline

## Status

Accepted

## Context

Whale Radar AI needs a historical backbone for the complete lifecycle of one
Market Situation. The record must preserve what the system knew at each moment
without retroactively replacing missing evidence, reinterpreting expectations,
or turning the history into trade or execution records.

## Decision

Use an immutable, versioned, in-memory `MarketSituationTimeline`. Each
`MarketSituationTimelineEntry` contains a point-in-time `SituationDNA`, the
upstream `EmergingStage`, explicit expectation facts, and source references.
Appending produces a new timeline with the previous entries plus exactly one
new entry and increments the version by one.

### Historical Integrity Principle

Whale Radar AI never rewrites history. Every entry represents exactly what was
known when it was created. Later evidence creates a new entry and a replacement
timeline version. Earlier objects remain unchanged.

### Separation of Observation and Interpretation

Expected, observed, missing expected, and unexpected events are stored as four
explicit collections. Timeline does not infer one collection from another and
does not evaluate whether an expectation succeeded. `SituationDNA` captures the
normalized knowledge snapshot; the entry adds lifecycle interpretation and
provenance without changing the source facts.

### Stage ownership

Timeline reuses `EmergingStage` from the Early Bird package to avoid duplicate
lifecycle vocabularies. It records the exact supplied stage and enforces only
structural consistency between a timeline and its final entry. It does not
decide, infer, validate progression, or prevent regressions between stages.

## Alternatives considered

### Mutable journal

Rejected because in-place edits can silently rewrite earlier knowledge and make
reconstruction unreliable.

### Database log

Deferred. A database is an infrastructure decision and would couple the Phase 1
domain contract to persistence, migrations, and deployment concerns.

### Signal history

Rejected because a Market Situation lifecycle is broader than BUY/SELL or
prediction records and must not acquire trading authorization semantics.

### Immutable versioned Timeline

Selected because it makes append behavior explicit, preserves old objects,
supports deterministic serialization, and provides a stable future persistence
boundary.

## Consequences

Positive consequences:

- point-in-time Situation DNA and provenance are preserved;
- history cannot be mutated through the public model API;
- missing data remains distinct from a measured zero;
- expectation gaps remain explicit facts;
- stages share the approved Early Bird vocabulary;
- serialization supports later storage without introducing storage now.

Negative consequences and trade-offs:

- each append constructs a complete replacement tuple and timeline object;
- callers must retain the latest version explicitly;
- immutability does not itself provide durable storage or concurrency control;
- structural validation cannot establish that an upstream stage is semantically
  correct;
- duplicated full histories can use more memory than a mutable structure.

## Dependency boundaries

Runtime code may use only the Python standard library, public
`app.intelligence.early_bird.EmergingStage`, and local timeline modules. It must
not depend on providers, exchanges, Telegram, FastAPI, databases, repositories,
pipelines, Decision Engine, Trade Readiness, MarketStateEngine, Experts,
scanners, or networking.

## Future boundaries

A future persistence adapter may store serialized timeline versions without
changing domain append semantics. A future `MarketSituation` attachment should
reference or contain a timeline only after a separate approved task; Phase 1
does not modify `MarketSituation`. Outcome and learning components may attach
new facts or references in future contracts, but must not rewrite old entries.
