# PS-4 RealityGapAttachment Compatibility Policy Report

## Result

Implemented immutable compatibility policy and decision contracts for Reality
Gap attachment revisions.

## Policy

The Phase 1 declaration records:

- same and patch contract versions as `COMPATIBLE`;
- major mismatches as `INCOMPATIBLE`;
- minor evolution and unknown versions as `REQUIRES_REVIEW`.

No version parsing or compatibility evaluation is performed.

## Historical integrity

Attachment, Analysis, Classification, and Metrics remain independent version
axes. Compatibility decisions preserve their four exact references, policy
version, and UTC evaluation time. Historical references cannot be substituted
with current defaults.

## Deliverables

- compatibility enums;
- immutable version-rule, policy, and decision contracts;
- deterministic dictionary and canonical JSON serialization;
- package exports;
- focused unit tests;
- ADR and specification.

## Boundaries

No compatibility or validator service, API, database, persistence, migration,
scheduler, runtime orchestration, production integration, or Telegram change
was added. Existing read and lifecycle contracts remain unchanged.
