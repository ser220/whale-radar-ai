# PS-4 Decision Reference Envelope Contract Report

## Summary

Added an immutable identity-only envelope for one historical compatibility
decision revision. This addresses the Decision-reference portion of
`GOV-CLOSURE-001` without modifying the existing Decision, Basis, or Association
contracts.

## Implementation

- Added frozen `RealityGapCompatibilityDecisionReference`.
- Added required identity and positive version validation.
- Added optional canonical SHA-256 digest validation.
- Added deterministic `to_dict()`, `from_dict()`, and `canonical_json()`.
- Added package exports and focused tests.

## Historical integrity

Decision version and optional digest are preserved exactly. The contract does
not generate, infer, resolve, or replace either locator and contains no decision
payload.

## Backward compatibility

`RealityGapAttachmentCompatibilityDecision`,
`RealityGapCompatibilityDecisionBasis`, and
`RealityGapCompatibilityDecisionAssociation` are unchanged. Existing package
imports remain valid and exports are additive.

## Architecture boundaries

No resolver, evaluator, service, API, database, persistence, migration,
networking, Telegram, production integration, or runtime orchestration is added.

## Verification

Verification covers Python compilation, focused reference tests, attachment
governance regressions, safe smoke tests, diff checks, and dependency-boundary
inspection.
