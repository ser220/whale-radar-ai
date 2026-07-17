# PS-4 Immutable Compatibility Decision Association V2 Contract

## Objective

Define an immutable typed provenance association among one historical
attachment artifact, compatibility decision identity, and decision-basis
identity.

## Public contract

`RealityGapCompatibilityDecisionAssociationV2` is a frozen dataclass containing:

- `association_id`
- `attachment_reference: RealityGapArtifactReference`
- `decision_reference: RealityGapCompatibilityDecisionReference`
- `basis_reference: RealityGapCompatibilityDecisionBasisReference`
- `associated_at`
- `association_contract_version`

The attachment reference must have canonical artifact type `ATTACHMENT`.
Decision and Basis references are the separately versioned identity-only
envelopes introduced for historical provenance.

## Provenance-only boundary

Association V2 records which immutable decision revision and basis revision
belong to one exact attachment history. It contains reference envelopes only.
It does not embed Decision or Basis payloads, calculate compatibility, resolve
identities, fetch current state, or replace historical locators.

Decision, Basis, and both reference envelopes remain independently immutable.
V2 links them without taking ownership of their content or lifecycle.

## Independent historical verification

Typed envelopes replace the opaque Decision/Basis strings used by Association
V1. Each edge now preserves a contract-owned identity and positive historical
version, plus an optional independently supplied digest. The attachment edge
preserves version-only, digest-only, or dual-locator canonical history.

No version is inferred from a digest, no digest from a version, and no current
default is substituted. Deterministic nested serialization makes the provenance
record independently addressable without adding a resolver.

## Validation and serialization

The contract requires distinct association, attachment, decision, and basis
identities; an `ATTACHMENT` canonical reference; exact typed Decision and Basis
reference envelopes; an aware timestamp normalized to UTC; and a syntactically
valid contract version.

`to_dict()` serializes all nested envelopes deterministically. `from_dict()`
rejects missing or unknown fields and reconstructs the exact nested contract
types. `canonical_json()` preserves all historical locator values.

## Backward compatibility

Association V1 remains unchanged and readable. V2 has a separate public name
and serialized shape. Existing Decision, Basis, Decision Reference, Basis
Reference, canonical artifact, Read, Lifecycle, and Compatibility contracts are
not modified.

## Out of scope

- Compatibility evaluator or resolver
- Service or API
- Database or persistence
- Migration
- Runtime integration or orchestration
- Current-state lookup or substitution

## Dependencies

Python standard library and local immutable attachment contracts only. No new
third-party dependency is introduced.
