# PS-4 RealityGapAttachment Compatibility Policy Specification

## Objective

Define an immutable contract boundary for describing compatibility among
independently versioned Reality Gap attachment artifacts without implementing a
runtime compatibility service.

## Scope

- immutable compatibility categories;
- declarative semantic-version conditions and outcomes;
- immutable policy definition;
- immutable compatibility decision record;
- exact historical references and independent version axes;
- strict deterministic serialization.

## Out of scope

- compatibility evaluation or semantic-version parsing;
- validator services or artifact resolution;
- migration, synchronization, or current-version lookup;
- API, database, persistence, scheduler, or runtime orchestration;
- production or Telegram integration.

## Public API

- `AttachmentCompatibilityStatus`
- `AttachmentVersionCondition`
- `AttachmentVersionCompatibilityRule`
- `AttachmentCompatibilityValidationError`
- `RealityGapAttachmentCompatibilityPolicy`
- `RealityGapAttachmentCompatibilityDecision`
- `canonical_compatibility_categories()`
- `canonical_version_rules()`

## Categories

- `COMPATIBLE`
- `INCOMPATIBLE`
- `REQUIRES_REVIEW`

## Version rules

- `SAME_CONTRACT_VERSION -> COMPATIBLE`
- `PATCH_VERSION_CHANGE -> COMPATIBLE`
- `MINOR_VERSION_EVOLUTION -> REQUIRES_REVIEW`
- `MAJOR_VERSION_MISMATCH -> INCOMPATIBLE`
- `UNKNOWN_VERSION -> REQUIRES_REVIEW`

The contract validates this exact Phase 1 declaration. It does not inspect
version strings or calculate a decision.

## Policy fields

- `policy_version`
- `compatibility_categories`
- `version_rules`
- `independent_version_axes`
- `historical_integrity_required`
- `preserve_historical_references`
- `allow_current_default_substitution`

The historical invariants validate only as `True`, `True`, and `False`.

## Decision fields

- `attachment_reference`
- `analysis_reference`
- `classification_reference`
- `metrics_reference`
- `compatibility_status`
- `policy_version`
- `evaluated_at`

Each reference is an immutable `AttachmentReadReference` with its own identity
and positive version. Reference identities must remain distinct. Version
numbers are validated independently and are not synchronized.

## Timestamp rules

`evaluated_at` must be timezone-aware and is normalized to UTC. Naive values
are rejected.

## Historical preservation

- a decision retains the exact four references supplied at creation;
- a later artifact or policy cannot replace a historical reference;
- current defaults are forbidden;
- unknown schema versions are not treated as compatible;
- changing a decision requires a separate immutable record outside this task.

## Serialization

- `to_dict()` emits fixed public field names and enum values;
- `from_dict()` rejects missing and unknown fields;
- `canonical_json()` uses sorted keys and compact deterministic separators;
- round trips preserve enums, reference versions, policy version, and UTC time.

## Compatibility boundaries

The policy does not modify the lifecycle policy, read contract, Analysis,
Classification, Metrics, Mapping, Projection, Assembly, or production code.
Compatibility status does not mutate lifecycle state or availability.

## Acceptance criteria

- all contracts are frozen dataclasses;
- collections are immutable tuples;
- canonical categories, rules, and revision axes are enforced;
- focused tests cover compatible, incompatible, review-required, independent
  axes, historical integrity, immutability, UTC validation, and serialization;
- Python 3.9 compilation and existing safe regressions pass;
- no runtime service or third-party dependency is introduced.
