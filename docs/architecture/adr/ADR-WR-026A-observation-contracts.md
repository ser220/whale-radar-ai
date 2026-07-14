# ADR-WR-026A — Observation Contracts

## Status

Accepted for implementation; Architecture Review is required before merge.

## Context

WR-024.5 introduced immutable intelligence output contracts and WR-025 added a
pure engine that combines `ExpertOpinion` values into `MarketState`. Future
independent Experts still need a stable input language. Existing raw source
payloads vary by provider, transport, field naming, and availability, so they
are not an appropriate permanent domain boundary.

WR-026A adds normalized fact contracts only. It does not add builders, source
parsing, Experts, orchestration, persistence, or production integration.

## Decision

Create `app.intelligence.observations` as a standard-library-only package with:

- an abstract common `Observation` contract;
- five shared string enums used specifically by observations;
- six immutable typed observations for trend, momentum, structure, funding,
  open interest, and liquidity facts;
- explicit finite/range/type validation;
- timezone-aware timestamps normalized to UTC;
- recursively frozen metadata;
- per-type `to_dict()` and `from_dict()` round-trip serialization;
- a version field defaulting to `1` and a stable serialized type identifier.

Concrete observations use frozen dataclasses. The abstract base centralizes
common validation and serialization but is not itself directly instantiable.

## Why an Observation Layer exists

The Observation Layer separates acquisition and normalization from analytical
interpretation. Builders will translate source-specific data into stable facts;
Experts will consume those facts and produce `ExpertOpinion`. This boundary
makes both sides independently testable and prevents infrastructure concepts
from leaking into future intelligence logic.

## Why Experts must not parse raw source payloads directly

- Raw payload schemas can change independently of Expert semantics.
- Multiple sources may express the same fact differently.
- Transport errors and normalization rules should not be duplicated by every
  Expert.
- Direct payload parsing couples analysis to networking and provider adapters.
- Shared normalized facts make comparisons and deterministic tests possible.

## Why immutable normalized facts are preferred

- An Observation is a snapshot and should not change after creation.
- Defensive freezing prevents source-side collection mutations from changing
  evidence already supplied to an Expert.
- Explicit typed fields expose missing or invalid data at construction time.
- Value equality and deterministic serialization support future caching,
  replay, audit, and independent Expert tests.

## Alternatives considered

### Experts consume raw payloads

Rejected because it couples every Expert to providers, transports, and schema
drift, while duplicating parsing and validation behavior.

### Generic untyped dictionaries

Rejected because dictionaries provide no immutable schema, field validation,
enum vocabulary, UTC guarantee, or discoverable version boundary.

### One universal observation model

Rejected because a single wide model would contain many unrelated optional
fields and weaken invariants. Trend, funding, structure, open interest, and
liquidity facts have different validation rules.

### Typed domain-specific observations

Selected. A small common base handles identity, provenance, quality, time,
metadata, and version; focused concrete models define only their normalized
fact family.

## Selected approach

Use a non-instantiable abstract `Observation` base with shared helpers and six
frozen dataclasses. Each concrete type serializes an `observation_type` string
and restores itself through its own `from_dict()` method. No global polymorphic
factory or migration registry is introduced in Phase 1.

The observation-specific `TrendBias` is kept distinct from WR-024.5
`Direction`: a bias is an observed normalized property, while `Direction` is an
Expert's analytical conclusion. Existing `Direction`, `TrendState`, and
`LifecycleState` are not duplicated.

## Trade-offs

- Concrete modules repeat common field declarations so Python 3.9 dataclasses
  can retain required fields while `version` defaults to `1`; common behavior
  remains centralized in the abstract base.
- Manual validation and serialization require maintenance but avoid framework
  coupling and make the domain boundary explicit.
- Per-type loading is less convenient than a global factory but avoids an
  unnecessary registry and migration framework before real builders exist.
- Typed models are less flexible than arbitrary payloads; schema changes must
  be deliberate and version-aware.
- Contradictory trend flags are preserved instead of rejected because later
  Experts, not contracts, own interpretation and data-quality reasoning.

## Versioning strategy

Every observation defaults to version `1`; values below `1` and booleans are
rejected. Serialization preserves the version exactly. WR-026A adds no
migrations and does not silently coerce one schema version into another.
Future Observation Builders and Experts must explicitly state and test the
versions they produce or consume.

## Consequences

### Positive

- Future Experts receive stable, typed, immutable facts.
- Source adapters and analytical logic can evolve independently.
- Invalid numeric values and naive timestamps fail at the domain boundary.
- No third-party dependency or production change is introduced.
- Each observation can be serialized, audited, and tested independently.

### Negative

- Future schema evolution requires explicit version support.
- Builders must perform normalization before an Expert can consume data.
- Cross-observation relationships and multi-timeframe aggregation remain
  unresolved future concerns.

## Dependency boundaries

The package may import Python standard-library modules and modules inside
`app.intelligence.observations`. It must not import Telegram, FastAPI,
pipelines, Arkham, exchange clients, funding services, databases, repositories,
persistence, HTTP/networking, `MarketStateEngine`, Expert registries, concrete
Experts, ML, or LLM code.

## Future compatibility with Observation Builders and WR-026B Trend Expert

Future approved builders may normalize raw input into these contracts. A
future WR-026B Trend Expert may consume supported `TrendObservation` and related
fact versions and produce an `ExpertOpinion`. Neither component may be inferred
or implemented by this ADR. WR-026A does not begin WR-026B or integrate with the
production pipeline.
