# PS-4 Compatibility Decision Association V2 Contract Report

## Summary

Added an immutable typed provenance association joining a canonical historical
attachment reference with independently versioned Decision and Basis identity
envelopes. This resolves the remaining opaque-reference portion of
`GOV-CLOSURE-001` at the association boundary.

## Implementation

- Added frozen `RealityGapCompatibilityDecisionAssociationV2`.
- Enforced canonical `ATTACHMENT` references.
- Enforced typed Decision and Basis reference envelopes.
- Added strict identity, timestamp, and contract-version validation.
- Added deterministic nested `to_dict()`, `from_dict()`, and `canonical_json()`.
- Added package exports and focused provenance tests.

## Historical integrity

Attachment, Decision, and Basis identities and historical revisions remain
explicit and immutable. Version and digest locators are preserved independently
without conversion, resolution, inference, or current-default substitution.

## Backward compatibility

Association V1 and all existing Decision, Basis, Decision Reference, Basis
Reference, canonical artifact, Read, Lifecycle, and Compatibility contracts are
unchanged. V2 is additive.

## Architecture boundaries

The implementation adds no evaluator, resolver, service, API, database,
persistence, migration, provider, networking, Telegram, production integration,
or runtime orchestration.

## Verification

Verification covers Python compilation, focused V2 and reference-envelope tests,
attachment governance regressions, safe smoke tests, diff checks, and
dependency-boundary inspection.
