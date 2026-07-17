# PS-4 Decision Record Envelope Contract Report

## Result

Added the immutable `RealityGapCompatibilityDecisionRecordEnvelope` as an
additive provenance boundary. It binds a typed historical decision identity to
the complete immutable compatibility decision payload without combining their
responsibilities.

## Integrity

- Decision ID, decision version, and optional digest remain unchanged.
- The complete nested compatibility decision is serialized and restored.
- Aware timestamps are normalized to UTC.
- Canonical JSON is deterministic and performs no digest calculation.
- No current-default lookup or historical substitution exists.

## Scope

The change adds one contract module, public exports, focused unit tests, this
report, and the accompanying specification. Existing contracts and production
behavior are unchanged. No evaluator, resolver, service, API, database,
persistence, migration, or runtime integration was added.
