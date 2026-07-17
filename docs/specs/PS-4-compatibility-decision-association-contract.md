# PS-4 Immutable Compatibility Decision Association Contract

## Objective

Define an immutable provenance association between an externally supplied
compatibility decision, its immutable decision basis, and the exact historical
attachment reference described by that decision.

## Canonical attachment identity

`RealityGapArtifactType.ATTACHMENT` is added to the canonical artifact
vocabulary. Existing `ANALYSIS`, `CLASSIFICATION`, and `METRIC_SET` values remain
unchanged. The addition allows an attachment itself to use the same lossless
canonical identity and locator rules as the other immutable artifacts.

`RealityGapArtifactReference` continues to preserve `artifact_version` and
`snapshot_digest` independently. The association accepts only a canonical
reference whose artifact type is `ATTACHMENT`; it performs no locator
conversion.

## Public contract

`RealityGapCompatibilityDecisionAssociation` is a frozen dataclass containing:

- `association_id`
- `attachment_reference`
- `compatibility_decision_reference`
- `decision_basis_reference`
- `associated_at`
- `association_contract_version`

Decision and basis references are opaque, required identity tokens. They do not
embed decision or basis payloads and do not imply evaluation behavior.

## Provenance-only boundary

The association records which immutable decision belongs to which immutable
basis and attachment history. It does not recalculate compatibility, recreate a
basis, resolve identities, fetch current artifacts, or replace historical
references.

The compatibility decision and decision basis remain independently immutable.
The association links their identities without taking ownership of their
content or lifecycle.

## Validation and serialization

The contract requires distinct non-empty association, attachment, decision, and
basis identities; an `ATTACHMENT` canonical reference; an aware timestamp
normalized to UTC; and a non-empty syntactically valid contract version.

`to_dict()` is deterministic. `from_dict()` rejects missing or unknown fields
and reconstructs the typed canonical reference. `canonical_json()` preserves
version-only, digest-only, and dual-locator reference values exactly.

## Out of scope

- Compatibility evaluation or resolution
- Runtime orchestration or integration
- Services and APIs
- Database or persistence
- Migration logic
- Current-version lookup or default substitution

## Dependencies

Python standard library and local immutable attachment contracts only. No new
third-party dependency is introduced.
