# ADR: PS-4 RealityGapAttachment Lifecycle Policy

## Status

Proposed; awaiting Architecture Review.

## Context

`RealityGapAttachmentReadContract` exposes a minimal immutable view of an
attachment and its independently versioned Analysis, Classification, and
Metrics references. A lifecycle policy is required before any future service
may activate, supersede, or archive attachment revisions. Without an explicit
policy, a consumer could overwrite an old relationship, reinterpret an old
attachment using current defaults, or collapse attachment revision into an
artifact version.

This task defines architecture and contracts only. It does not perform state
transitions or change an attachment.

## Decision

Adopt a forward-only lifecycle:

```text
CREATED -> ACTIVE -> SUPERSEDED -> ARCHIVED
```

The immutable `RealityGapAttachmentLifecyclePolicy` declares:

- the lifecycle state under which the policy is represented;
- a versioned policy identity;
- the exact ordered transition graph;
- a revision-policy identifier;
- four independent revision axes: Attachment, Analysis, Classification, and
  Metrics;
- mandatory immutable-history and reference-preservation invariants;
- a mandatory prohibition on substituting current defaults.

`AttachmentLifecycleTransition` rejects backward, skipped, repeated, or
otherwise unknown transitions at contract construction.

## Supersession semantics

`SUPERSEDED` means that a newer attachment revision exists. The earlier
attachment remains historically valid and retains the exact Analysis,
Classification, Metrics, policy, and version references recorded when it was
created. Supersession creates history; it never replaces history.

The contract does not find the newer revision, update a status, or persist a
relationship. Those responsibilities require separately reviewed runtime
architecture.

## Revision semantics

Attachment revision is independent from Analysis, Classification, and Metrics
revision. A future successor attachment must advance according to its own
revision policy. No rule requires referenced artifact versions to equal or
advance with the attachment version; each reference remains the exact version
selected for that attachment revision.

Policy version and revision-policy identifier are also distinct. Neither is an
artifact version.

## Historical preservation

An attachment is immutable after creation. A lifecycle change must be
represented by a new immutable record or relationship in a future layer; it
must not edit the old attachment. Historical reconstruction follows:

```text
attachment revision
  -> Analysis identity/version
  -> Classification identity/version
  -> Metrics identity/version
```

Current defaults, current policy versions, later artifact revisions, outcomes,
or learning results must never be substituted into that chain.

## Compatibility boundary

The lifecycle policy is additive. It does not modify:

- `RealityGapAttachmentReadContract` or its seven-field read boundary;
- `RealityGapAnalysisAttachment` on its parallel contract history;
- Analysis, Classification, Metrics, Mapping, Projection, or Assembly records;
- production, Telegram, API, database, or persistence behavior.

`AttachmentLifecycleState` is intentionally separate from
`AttachmentAvailabilityStatus`. A future read consumer may project lifecycle
state into availability only under a separately versioned policy. This task
adds no automatic mapping.

## Alternatives considered

### Mutable status on the attachment

Rejected because it rewrites historical truth and prevents exact replay.

### Infer lifecycle from the latest artifact versions

Rejected because artifact and attachment revisions are independent and
inference would substitute current state for historical facts.

### Forward-only immutable policy contracts

Selected because they are deterministic, auditable, additive, and compatible
with future runtime services without implementing those services now.

## Consequences

Positive:

- lifecycle vocabulary and transitions are explicit;
- invalid transitions fail before a runtime layer exists;
- independent version lineage is preserved;
- historical attachments remain reconstructable.

Trade-offs:

- no transition is executed by this package;
- no latest-revision lookup or archive storage exists;
- future orchestration must provide concurrency, authorization, and persistence
  rules without weakening this contract.
