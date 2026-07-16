# PS-4 Canonical Artifact Reference Contract Report

## Result

Implemented `RealityGapArtifactReference`, an immutable and lossless canonical
reference contract for Analysis, Classification, and MetricSet artifacts.

## Historical addressing

The contract preserves two independent locator forms:

- optional positive integer `artifact_version`;
- optional canonical `snapshot_digest`.

At least one locator is required. Neither is derived from the other, and both
may be retained together. Digest-only references never receive fake versions;
version-only references never receive fake digests.

## Public API

- `RealityGapArtifactType`
- `RealityGapArtifactReference`
- `ArtifactReferenceValidationError`

## Validation and serialization

- supported artifact types only;
- required non-empty identity;
- positive non-boolean versions;
- exact `sha256:<64 lowercase hex>` digest grammar;
- required version or digest locator;
- required reference-contract version;
- frozen dataclass;
- strict `to_dict()` / `from_dict()`;
- deterministic `canonical_json()`.

## Boundaries

No service, API, database, persistence, evaluator, migration, compatibility
resolver, runtime orchestration, production integration, or Telegram change was
added. Existing attachment contracts remain unchanged apart from additive
package exports.

The base integration retained the Read, Lifecycle, and Compatibility modules
but omitted part of their previously public package-root exports. This task
restores those additive exports so existing imports and focused tests remain
backward compatible. No existing contract implementation or runtime behavior
was changed by that restoration.

## Next review boundary

A future contract-only task may define explicit, lossless projections from the
existing core reference types to this canonical type. That work must not infer
missing locators or change historical source contracts.
