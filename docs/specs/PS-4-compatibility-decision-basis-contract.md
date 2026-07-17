# PS-4 Immutable Compatibility Decision Basis Contract

## Objective

Preserve the historical reason, declared policy rule, and exact canonical
references that formed the basis of an externally supplied Reality Gap
attachment compatibility decision.

## Public API

`CompatibilityDecisionBasisType` supports:

- `VERSION_RULE`
- `DIGEST_RULE`
- `MANUAL_REVIEW`

`RealityGapCompatibilityDecisionBasis` is a frozen dataclass with:

- `basis_type`
- `policy_version`
- `rule_code`
- `reference_snapshot`

`reference_snapshot` is an immutable mapping from comparison-role names to
`RealityGapArtifactReference` values.

## Historical explanation only

This contract records provenance supplied by an external decision owner. It is
not an evaluator, resolver, compatibility service, or policy engine. It does
not infer a rule, compare artifacts, or calculate compatibility status.

Compatibility status and decision basis remain independent. The basis contract
contains no status field and does not modify the existing compatibility
decision or policy contracts.

## Reference integrity

Canonical references remain immutable and lossless:

- version and digest locators remain independent;
- digest-only references receive no invented version;
- version-only references receive no invented digest;
- current defaults never replace historical references;
- mutable input mappings are defensively copied and frozen.

## Validation and serialization

The contract rejects unknown basis types, empty policy versions, empty rule
codes, empty snapshots, invalid reference names, and values that are not valid
`RealityGapArtifactReference` instances.

`to_dict()` serializes references in deterministic role-name order.
`from_dict()` strictly reconstructs nested canonical references and rejects
unknown or missing fields. `canonical_json()` provides deterministic JSON.

## Dependencies and exclusions

The implementation uses the Python standard library and local immutable
attachment contracts only. It adds no evaluator, resolver, service, API,
database, persistence, migration, networking, Telegram, or runtime integration.
