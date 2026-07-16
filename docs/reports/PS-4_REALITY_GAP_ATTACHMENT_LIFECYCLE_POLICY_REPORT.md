# PS-4 RealityGapAttachment Lifecycle Policy Report

## Result

Implemented an immutable contract-only lifecycle policy for Reality Gap
attachment revisions.

## Architecture

The fixed lifecycle is:

```text
CREATED -> ACTIVE -> SUPERSEDED -> ARCHIVED
```

Supersession preserves the predecessor and all exact historical artifact
references. Attachment, Analysis, Classification, and Metrics versions remain
independent axes. Current defaults cannot be substituted for historical values.

## Implementation

- lifecycle and revision-axis enums;
- immutable transition declaration with forward-only validation;
- immutable policy contract with fixed historical-integrity invariants;
- deterministic dictionary and canonical JSON serialization;
- package exports;
- focused unit tests;
- ADR and specification.

## Boundaries

No services, API, database, persistence, scheduler, runtime orchestration,
migration engine, production integration, or Telegram changes were added.

The existing `RealityGapAttachmentReadContract` remains unchanged. Lifecycle
state and read availability remain separate, with no automatic projection.
