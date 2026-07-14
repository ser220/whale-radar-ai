# ADR-WR-035 — Market Situation Runtime, Phase 1

## Status

Accepted for implementation; Architecture Review is required before merge.

## Context

Whale Radar AI has immutable contracts for early events, observations, expert
opinions, and synthesized market state, but it lacks a runtime identity that
keeps one market story coherent over time. Isolated artifacts cannot preserve
how evidence, confidence, expectations, health, outcome, and learning relate to
the same developing situation.

WR-035 creates only the domain contracts for that identity. It does not attach
them to the production pipeline or implement orchestration, persistence,
evaluation, lifecycle automation, Early Bird, or learning.

The baseline is `origin/main` at `c2028c1`. The WR-034 architecture document is
still under separate Architecture Review and is not present in that baseline.
This ADR therefore records the complete runtime decision needed by WR-035
without importing unreviewed branch history.

## Decision

Create `app.intelligence.situations` as a Python 3.9-compatible,
standard-library-only package containing:

- five string enums for lifecycle, health, timeline, expectation status, and
  expectation violation vocabulary;
- immutable `SituationTimelineEntry`, `ConfidencePoint`, `ExpectationRecord`,
  and `MarketSituation` frozen dataclasses;
- strict validation, UTC normalization, defensive deep freezing, and
  dictionary round-trip serialization;
- ordered, unique string references to external artifacts instead of embedded
  domain or infrastructure objects;
- explicit constructor-only immutable version replacement.

No model infers lifecycle progress, health, confidence, expectation outcome,
market interpretation, or trade meaning.

## Why MarketSituation is the central domain identity

`MarketSituation` supplies one durable `situation_id` for a market story while
the story accumulates different artifact families. It preserves chronology and
the evolution of system knowledge without promoting any individual event,
indicator, Expert, provider, UI, or persistence mechanism into the system's
primary unit of intelligence.

The identity is central, but the object is not a central decision maker. It is
an immutable record of explicitly supplied facts and references.

## Why artifact references are used

Embedding `FastObservation`, Observation, `ExpertOpinion`, correlation, or
`MarketState` objects would couple the aggregate to their schemas and import
graphs, duplicate data, and blur ownership of versioning. Stable string IDs:

- isolate the contract from artifact implementation and infrastructure;
- support independent artifact evolution;
- avoid accidental mutation or oversized nested snapshots;
- make provenance explicit;
- leave retrieval and referential integrity to future repository boundaries.

References are ordered and duplicates are rejected. Invalid input is not
silently deduplicated because that could conceal producer errors.

## Why immutable version history is required

Market understanding changes as late evidence arrives. Rewriting a prior
object would destroy what the system knew at an earlier time and weaken audit,
replay, outcome review, and learning. Every later state must be represented by
a replacement `MarketSituation` with an explicit version increment and
`updated_at` value. Prior versions and their history are not mutated.

Phase 1 deliberately provides constructors only. Cross-version checks,
concurrency, storage, and append orchestration need a future repository and
orchestrator, so helper methods would provide only partial guarantees now.

## Why confidence and expectation histories are preserved

A final confidence number cannot explain when or why confidence changed.
`ConfidencePoint` keeps the timestamp, source, reason, and metadata for each
explicitly recorded value. It has no trade authorization meaning.

Expectations allow later review of both key learning questions:

- What happened that should not have happened?
- What did not happen that should have happened?

`ExpectationRecord` fixes the expected event, evidence basis, and time window,
then stores an explicitly supplied status and gap classification. It does not
infer violations. Missing observations are not automatically a `MISSING`
outcome, and an expectation cannot be invented after the fact within an
existing immutable record.

## Why no component owns the whole situation

Providers produce source data, builders produce observations, Experts produce
opinions, correlation describes relationships, synthesis produces market
state, and UIs present selected views. None should control the whole story.
A future orchestrator may coordinate replacement versions, and a future
repository may persist them, but neither changes the domain identity or gains
authority to infer analytical meaning silently.

## Alternatives considered

### Mutable aggregate

Rejected. In-place updates erase historical knowledge, complicate concurrent
writers and audit, and can let downstream consumers observe partially updated
state.

### Database-owned record

Rejected. Making a table or ORM object the domain authority couples semantics
to persistence, makes pure testing harder, and blocks alternative stores or
replay. Persistence is a future adapter around the domain contract.

### Signal-centric model

Rejected. BUY/SELL labels collapse a developing situation into an action and
discard expectation gaps, expert behavior, outcomes, and learning context.
Whale Radar AI tracks situations for decision support; it does not make a
signal the primary identity.

### Immutable versioned situation

Selected. It preserves temporal knowledge, supports replay and learning, keeps
infrastructure outside the domain, and allows artifacts to remain independently
versioned and referenced.

## Trade-offs

- Callers must explicitly reconstruct a full replacement object.
- String references cannot prove that an artifact exists; future repositories
  must enforce referential integrity.
- Manual serialization and validation require deliberate schema maintenance.
- Strict ordering and duplicate rejection put normalization responsibility on
  future orchestrators.
- Full histories can grow; future persistence may need snapshots or indexed
  storage without changing the immutable domain semantics.
- Phase 1 cannot enforce that `version + 1` follows an actually stored prior
  version because no repository exists.

## Dependency boundaries

The package may import only Python standard-library modules and modules under
`app.intelligence.situations`. It must not import artifact object classes,
Telegram, FastAPI, APIs, databases, repositories, providers, source adapters,
pipelines, external services, networking, or third-party dependencies.

No requirements, production pipeline, Telegram, database, API, or Hostinger
change is authorized.

## Future orchestrator and repository boundaries

A future reviewed orchestrator may validate commands, gather stable artifact
IDs, construct `version + 1`, and append explicit timeline, confidence, or
expectation records. It must not mutate old versions or infer transitions
without an approved policy.

A future repository may store and retrieve all versions, enforce optimistic
concurrency and referential integrity, and provide history queries. Storage
models remain adapters; they do not replace `MarketSituation` as the domain
identity.

## Future compatibility

- **Early Bird:** may create opportunity-related artifacts referenced by ID;
  it does not authorize a trade or own the situation.
- **Experts:** contribute independent opinion IDs and expert names.
- **Correlation:** contributes relationship IDs without calculating direction.
- **Market state and decision support:** attach versioned result/context IDs;
  neither mutates the situation.
- **Outcomes:** attach outcome IDs and explicit timeline records.
- **Learning and memory:** consume complete version history and attach learning
  or memory references rather than reducing the story to isolated labels.

These components are compatibility targets only and are not implemented or
integrated by WR-035.
