# PS-4 Basis Record Envelope Contract Report

## Result

Added the immutable `RealityGapCompatibilityDecisionBasisRecordEnvelope` as an
additive provenance boundary. It binds a typed historical basis identity to the
complete immutable decision-basis payload without combining their
responsibilities.

## Integrity

- Basis ID, basis version, and optional digest remain unchanged.
- The complete nested basis and historical reference snapshot are restored.
- Mutable source mappings cannot mutate the frozen basis after construction.
- Aware timestamps are normalized to UTC.
- Canonical JSON is deterministic and performs no digest calculation.
- No current-default lookup or historical substitution exists.

## Scope

The change adds one contract module, public exports, focused unit tests, this
report, and the accompanying specification. Existing contracts and production
behavior are unchanged. No evaluator, resolver, service, API, database,
persistence, migration, or runtime integration was added.
