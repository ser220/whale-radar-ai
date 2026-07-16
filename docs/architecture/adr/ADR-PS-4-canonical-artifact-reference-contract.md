# ADR: PS-4 Canonical Artifact Reference Contract

## Status

Proposed; awaiting Architecture Review.

## Context

The merged Reality Gap attachment governance stack contains two historically
valid reference vocabularies:

- core Analysis references use identity plus a positive integer version;
- core Classification and MetricSet references use identity plus a canonical
  snapshot digest;
- the read boundary uses generic identity plus a positive integer version.

Governance review finding GOV-002 determined that these shapes cannot be made
equivalent by inventing values. A digest is not an integer record version, and
an integer version is not a content digest. Dropping either loses historical
addressing information.

## Decision

Add the immutable `RealityGapArtifactReference` as a canonical, lossless
reference vocabulary. It contains:

- `artifact_type`;
- `artifact_id`;
- optional `artifact_version`;
- optional `snapshot_digest`;
- `reference_contract_version`.

Supported artifact types are `ANALYSIS`, `CLASSIFICATION`, and `METRIC_SET`.
At least one historical locator must exist. Both locators may coexist when an
artifact source owns both forms.

The contract is additive. It does not replace or mutate the current core,
read, lifecycle, or compatibility contracts. No mapper or projection is added
in this task.

## Independent locator semantics

`artifact_version` is a source-owned positive integer revision.
`snapshot_digest` is exact canonical content addressing using
`sha256:<64 lowercase hex>`.

The two locators are independent:

- version-only references serialize the digest as `null`;
- digest-only references serialize the version as `null`;
- references with both preserve both values unchanged;
- the contract never calculates, guesses, or synchronizes either value.

This distinction preserves historical truth and avoids fake compatibility.

## Reference contract version

`reference_contract_version` versions this reference schema, not the referenced
artifact. It must never be substituted for `artifact_version`, a snapshot
digest, attachment version, or policy version.

## Validation

- artifact type must be supported;
- identity and reference-contract version are required;
- integer versions must be positive and cannot be booleans;
- digests must match the exact lowercase SHA-256 grammar;
- at least one locator is required;
- unknown serialized fields are rejected.

## Serialization

`to_dict()` uses fixed field names and retains absent locators as explicit
`None`. `from_dict()` is strict. `canonical_json()` uses sorted keys and compact
deterministic separators. Round trips preserve enum type and locator values.

## Historical boundary

The record has no current-default field and no resolver. Once created, it is a
frozen historical reference. Any future projection from core or read contracts
must be separately reviewed and must prove that no locator is dropped or
fabricated.

## Alternatives considered

### Convert digests to version numbers

Rejected because there is no lossless or authoritative conversion.

### Convert versions to digests

Rejected because a digest requires canonical artifact bytes, not a revision
integer.

### Use an untyped string locator

Rejected because it loses locator semantics and makes validation ambiguous.

### Preserve independent optional locators

Selected because it represents every current source model without information
loss and remains extensible under an explicit reference-contract version.

## Consequences

Positive:

- resolves the canonical vocabulary portion of GOV-002;
- preserves exact historical addressing;
- supports version-only, digest-only, and dual-locator artifacts;
- introduces no runtime or production behavior.

Trade-offs:

- existing contracts are not automatically migrated;
- future adapters must map source fields explicitly;
- semantic compatibility remains a separate policy decision;
- digest verification remains outside this contract.
