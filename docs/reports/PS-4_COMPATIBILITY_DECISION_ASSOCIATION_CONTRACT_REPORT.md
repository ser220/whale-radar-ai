# PS-4 Compatibility Decision Association Contract Report

## Summary

Added an immutable provenance association linking a compatibility decision
identity, decision-basis identity, and lossless canonical attachment reference.

## Implementation

- Added `ATTACHMENT` additively to `RealityGapArtifactType`.
- Added frozen `RealityGapCompatibilityDecisionAssociation`.
- Added strict identity, reference, timestamp, and contract-version validation.
- Added deterministic `to_dict()`, `from_dict()`, and `canonical_json()`.
- Added package exports and focused tests for immutability and historical
  locator preservation.

## Backward compatibility

The existing `ANALYSIS`, `CLASSIFICATION`, and `METRIC_SET` enum names and values
are unchanged. Existing canonical reference payloads and imports remain valid.
Compatibility Policy, Compatibility Decision, Compatibility Decision Basis,
Read, Lifecycle, and Canonical Reference model implementations are unchanged.

## Architecture boundaries

The association is provenance only. It contains no evaluator, resolver,
service, API, database, persistence, migration, networking, Telegram, or
runtime integration.

## Historical integrity

Attachment version and digest locators remain independent and are serialized
without conversion. Decision and basis identities remain opaque; their payloads
are not embedded, recomputed, or replaced.

## Verification

Verification covers Python compilation, focused association and canonical
reference tests, attachment governance regressions, safe smoke tests, diff
checks, and dependency-boundary inspection.
