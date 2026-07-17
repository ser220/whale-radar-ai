# PS-4 Basis Reference Envelope Contract Report

## Summary

Added an immutable identity-only envelope for one historical compatibility
decision-basis revision. This resolves the Basis-reference portion of
`GOV-CLOSURE-001` without modifying the existing Basis, Decision, Decision
Reference, or Association contracts.

## Implementation

- Added frozen `RealityGapCompatibilityDecisionBasisReference`.
- Added required identity and positive version validation.
- Added optional canonical SHA-256 digest validation.
- Added deterministic `to_dict()`, `from_dict()`, and `canonical_json()`.
- Added package exports and focused tests.

## Historical integrity

Basis version and optional digest are preserved exactly. The contract does not
generate, infer, resolve, or replace either locator and contains no basis
payload.

## Backward compatibility

`RealityGapCompatibilityDecisionBasis`,
`RealityGapAttachmentCompatibilityDecision`,
`RealityGapCompatibilityDecisionReference`, and
`RealityGapCompatibilityDecisionAssociation` are unchanged. Existing package
imports remain valid and exports are additive.

## Architecture boundaries

No resolver, evaluator, service, API, database, persistence, migration,
networking, Telegram, production integration, or runtime orchestration is added.

## Verification

Verification covers Python compilation, focused reference tests, attachment
governance regressions, safe smoke tests, diff checks, and dependency-boundary
inspection.
