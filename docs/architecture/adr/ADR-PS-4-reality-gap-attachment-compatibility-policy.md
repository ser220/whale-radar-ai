# ADR: PS-4 RealityGapAttachment Compatibility Policy

## Status

Proposed; awaiting Architecture Review.

## Context

Reality Gap attachments preserve a relationship among four independently
versioned artifacts: Attachment, Analysis, Classification, and Metrics. The
lifecycle policy protects revision history, but it does not define how contract
schema evolution is described or how a compatibility outcome is recorded.

Without an explicit compatibility boundary, a future consumer could silently
substitute a current artifact, synchronize unrelated versions, or treat an
unknown schema as compatible. Each would rewrite historical meaning.

## Decision

Introduce immutable, declarative compatibility contracts only:

- `AttachmentCompatibilityStatus` defines `COMPATIBLE`, `INCOMPATIBLE`, and
  `REQUIRES_REVIEW`;
- `AttachmentVersionCondition` defines the supported schema-version
  relationships;
- `AttachmentVersionCompatibilityRule` records one fixed condition/outcome;
- `RealityGapAttachmentCompatibilityPolicy` declares the complete rule set,
  independent version axes, and historical-integrity invariants;
- `RealityGapAttachmentCompatibilityDecision` records an externally supplied
  outcome against four exact immutable artifact references.

No parser or evaluator is implemented. The policy is data, not a compatibility
service.

## Initial version rules

| Condition | Status | Reason |
|---|---|---|
| Same contract version | `COMPATIBLE` | No schema difference exists. |
| Patch version change | `COMPATIBLE` | Phase 1 treats patch changes as contract-compatible. |
| Minor version evolution | `REQUIRES_REVIEW` | Additive evolution may still affect a consumer boundary. |
| Major version mismatch | `INCOMPATIBLE` | Breaking schema evolution cannot be silently accepted. |
| Unknown version | `REQUIRES_REVIEW` | Absence of version knowledge is not compatibility evidence. |

These rules describe semantic contract-version relationships. They do not
compare or synchronize attachment/artifact record-version integers.

## Independent version axes

Attachment, Analysis, Classification, and Metrics versions are separate. No
axis derives from another, and equal numeric values do not imply compatibility.
Advancing one artifact does not advance or invalidate another automatically.

The immutable decision therefore retains four separate
`AttachmentReadReference` records. Their versions may differ freely, while
their identities must remain distinct.

## Historical compatibility

Every decision preserves the exact references under evaluation:

```text
attachment reference/version
analysis reference/version
classification reference/version
metrics reference/version
policy version
evaluated_at
```

The decision cannot carry replacement artifacts, latest-version pointers,
payloads, migration output, or current defaults. Existing attachments and
references are never modified. Re-evaluation under a later policy would create
a separate immutable decision; it cannot rewrite the earlier decision.

## Compatibility and lifecycle

Compatibility status is separate from lifecycle state and read availability.
`INCOMPATIBLE` does not archive an attachment. `SUPERSEDED` does not prove
schema incompatibility. A future orchestration layer may consume all three
boundaries only after separate review.

## Anti-substitution boundary

The policy requires historical integrity and exact reference preservation and
forbids current-default substitution. Unknown versions require review rather
than optimistic acceptance. The contract does not resolve references or fetch
artifacts, so it cannot silently replace them.

## Alternatives considered

### Infer compatibility from record-version integers

Rejected. Record versions and schema versions have different meanings, and the
four record axes are independent.

### Accept minor and unknown versions automatically

Rejected. That would create silent compatibility assumptions and weaken
historical reconstruction.

### Declarative immutable policy and decision records

Selected. It makes categories, rules, lineage, and policy version explicit
without introducing runtime behavior.

## Consequences

Positive:

- deterministic policy comparison and audit;
- explicit treatment of unknown and major versions;
- no silent artifact substitution;
- attachment and artifact version independence is preserved;
- no production behavior changes.

Trade-offs:

- no version parser or compatibility evaluator exists;
- no service selects, migrates, or resolves artifacts;
- minor evolution requires an external reviewed decision;
- a future service must define authorization and evidence for decisions.
