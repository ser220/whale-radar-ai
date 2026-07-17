# PS-4 Canonical Read Boundary v2 Report

## Summary

Added an additive, immutable v2 consumer boundary around
`RealityGapArtifactReference`. The new contract preserves version-only,
digest-only, and dual-locator references without conversion.

## Implementation

- Added `RealityGapAttachmentReadReferenceV2` as a frozen dataclass.
- Added strict validation for the canonical reference, availability state, and
  read contract version.
- Added deterministic `to_dict()`, `from_dict()`, and `canonical_json()`.
- Exported the v2 contract and its validation error from the attachment package.
- Added focused tests for all required artifact types, availability states,
  locator preservation, serialization, strict shape, and immutability.

## Backward compatibility

`RealityGapAttachmentReadContract`, `AttachmentReadReference`, and their source
module were not modified. V2 is additive and has a distinct public name and
payload shape.

## Architecture boundaries

The implementation contains no service, API, database, persistence, resolver,
migration, compatibility evaluator, provider, networking, Telegram, or
production-pipeline integration.

## Historical integrity

The nested `RealityGapArtifactReference` remains the source of truth. V2 does
not synthesize versions from digests, synthesize digests from versions, or
substitute current defaults for historical locators.

## Verification

Verification covers Python compilation, focused v2 tests, attachment governance
regressions, related Reality Gap regressions, safe smoke tests, diff checks, and
dependency-boundary inspection. Final command results are recorded in the task
handoff after all checks complete.
