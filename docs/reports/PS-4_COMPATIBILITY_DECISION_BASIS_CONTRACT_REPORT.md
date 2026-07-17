# PS-4 Compatibility Decision Basis Contract Report

## Summary

Added an immutable provenance contract that preserves why an externally
supplied attachment compatibility decision was made, which declared rule was
used, and which canonical historical references were compared.

## Implementation

- Added `CompatibilityDecisionBasisType`.
- Added frozen `RealityGapCompatibilityDecisionBasis`.
- Added strict validation and defensive mapping freezing.
- Added deterministic `to_dict()`, `from_dict()`, and `canonical_json()`.
- Added package exports and focused contract tests.

## Architecture boundaries

The basis is descriptive provenance only. It contains no compatibility status,
evaluation logic, resolver, service, persistence, API, or production
integration. Existing compatibility policy, compatibility decision, read,
lifecycle, and canonical reference implementations are unchanged.

## Historical integrity

All snapshot values are canonical artifact references. Their version and digest
locators are serialized exactly as supplied, without conversion or substitution
of current defaults.

## Verification

Verification includes Python compilation, focused tests, attachment-governance
and related regressions, safe smoke tests, diff checks, and dependency-boundary
inspection.
