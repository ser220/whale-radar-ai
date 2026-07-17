# PS-4 Canonical Read Boundary v2

## Objective

Define a consumer-safe, immutable read reference that preserves every
historical locator carried by `RealityGapArtifactReference`.

## Why v2 exists

The existing `RealityGapAttachmentReadContract` uses
`AttachmentReadReference(reference_id, reference_version)`. That representation
cannot express a digest-only Classification or Metric Set reference without a
lossy or invented conversion. The v2 boundary therefore consumes the canonical
artifact reference directly.

## Backward compatibility

The v1 read contracts remain unchanged. Existing imports, serialized payloads,
and validation behavior continue to work. V2 is an additive contract with its
own public name and serialization shape.

## Public contract

`RealityGapAttachmentReadReferenceV2` exposes exactly:

- `artifact_reference: RealityGapArtifactReference`
- `availability_status: AttachmentAvailabilityStatus`
- `read_contract_version: str`

The allowed availability values are `AVAILABLE`, `UNAVAILABLE`, and
`SUPERSEDED`.

## Lossless reference rules

- `artifact_reference` is the canonical source of truth.
- `artifact_version` and `snapshot_digest` remain independent.
- A version-only reference remains version-only.
- A digest-only reference remains digest-only.
- A reference carrying both locators preserves both.
- The boundary never derives a digest from a version or a version from a
  digest.
- No current default may replace a historical locator.

The nested canonical contract continues to enforce artifact identity, artifact
type, locator presence, digest grammar, and reference contract version.

## Validation and serialization

The contract is a frozen dataclass. It requires an actual immutable
`RealityGapArtifactReference`, a supported availability state, and non-empty
`read_contract_version` text.

`to_dict()` returns a deterministic, consumer-safe mapping.
`from_dict()` rejects missing, extra, or invalid fields and restores the nested
canonical reference. `canonical_json()` produces deterministic JSON without
changing locator values.

## Consumer isolation

The read boundary exposes artifact identity, artifact type, historical
locators, availability, and contract version only. It does not expose evidence,
candidate objects, projections, mappings, evaluation internals, classification
payloads, or metrics payloads.

## Out of scope

- Runtime services or orchestration
- APIs
- Database or persistence
- Reference resolvers
- Migration logic
- Compatibility evaluation
- Production integration

## Dependencies

Python standard library and local immutable attachment contracts only. No new
third-party dependency is introduced.
