# ADR-WR-024.5 — Intelligence Contracts

## Status

Accepted

## Context

Whale Radar AI currently has a working production path from the Arkham webhook
through filtering, scoring, clustering, and Telegram delivery. Future
intelligence components need a stable domain language, but the repository does
not yet contain the Experts or `MarketStateEngine` described in the roadmap.

WR-024.5 introduces contracts before orchestration so future components can
exchange explicit, validated values without coupling the domain layer to the
existing production pipeline or to infrastructure frameworks.

## Decision

Create `app.intelligence.contracts` as a pure domain package with:

- string-valued enums for direction, trend state, and lifecycle state;
- immutable `ExpertOpinion`, `MarketState`, and `DecisionState` models;
- validation for finite percentage-like values in the inclusive 0–100 range;
- timezone-aware timestamps normalized to UTC;
- explicit `to_dict()` and `from_dict()` round-trip serialization;
- defensive conversion of mutable collections into immutable structures;
- a lightweight, deterministic `ExpertRegistry` keyed by `expert_name`.

The contracts remain additive and are not integrated into the production
pipeline in WR-024.5.

## Alternatives considered

### Frozen dataclasses

Standard-library frozen dataclasses provide typed value objects, generated
equality, clear constructors, and field-level immutability without adding a
framework dependency. Validation and serialization remain explicit and easy to
audit.

### Pydantic

Pydantic offers rich parsing and validation and is already present indirectly
through FastAPI. It was not selected because these contracts are domain
primitives rather than API schemas. Depending on Pydantic would couple the
domain language to an infrastructure-oriented validation framework and make
the contracts less portable.

### Plain dictionaries

Plain dictionaries require no model layer, but they do not enforce field names,
enum types, immutability, timestamp rules, or validation boundaries. Errors
would move from contract construction to later runtime paths and make future
Expert integration harder to reason about.

## Reasons for selecting frozen dataclasses

- They are included in Python 3.9 and require no new dependency.
- They express an immutable domain boundary directly.
- They preserve type information and equality semantics.
- They keep validation and serialization behavior explicit.
- They are independent of FastAPI, Pydantic, persistence, and transport code.
- They can be consumed by future Experts, tests, CLI tools, or API adapters.

## Python 3.9 compatibility

The implementation targets the repository's actual Python 3.9.6 runtime. It
uses `typing.Optional`, `typing.Tuple`, and other Python 3.9-compatible syntax,
and does not use structural pattern matching, `X | Y` annotations, built-in
generic syntax that would violate the supported runtime, or newer dataclass
features.

## Positive consequences

- Future Experts share one explicit vocabulary.
- Invalid scores and naive timestamps fail at the domain boundary.
- Model instances cannot be mutated after construction.
- Serialization is deterministic and preserves enums and timestamps.
- The existing production pipeline remains untouched.
- The package can be tested without live services or infrastructure.

## Negative consequences / trade-offs

- Validation and serialization code is maintained manually.
- Frozen dataclasses do not make arbitrary user-defined metadata objects
  immutable; the contract recursively freezes standard mappings and
  collections only.
- `MappingProxyType` metadata is not directly JSON serializable without the
  provided `to_dict()` conversion.
- The registry intentionally provides only in-memory deterministic lookup and
  no lifecycle, dependency injection, or persistence features.
- Probability values are validated individually but are not required to sum to
  100 because the approved specification does not define that invariant.

## Dependency boundaries

`app.intelligence.contracts` may import Python standard-library modules and
other modules inside the same contracts package. It must not import Telegram,
FastAPI, Pydantic, databases, repositories, persistence, the production
pipeline, Arkham or other source adapters, funding adapters, networking clients,
or delivery mechanisms.

Adapters may depend on the contracts in future approved tasks; the contracts
must never depend on those adapters.

## Future compatibility with WR-025 Market State Engine

WR-025 may consume `ExpertOpinion` instances from registered Experts and
produce `MarketState` and `DecisionState` values. The registry and models define
the exchange boundary but do not prescribe orchestration, weighting,
aggregation, Expert execution, production integration, or lifecycle behavior.
Those decisions require a separate WR-025 architecture approval.
