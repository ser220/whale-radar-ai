# ADR: PS-4 Classification and Metrics Integration Boundary

## Status

Proposed; awaiting Architecture Review.

## Context

Whale Radar AI now has immutable `RealityGapClassification` and
`RealityGapMetricSet` records plus deterministic read-only consumers. The
records preserve their own IDs, policy versions, analysis reference, input
lineage, creation boundary, trace reference, and canonical serialization.

`RealityGapAnalysis` predates those records. It currently owns the original
Reality Gap snapshot, candidate/tree/evidence relationships, capabilities,
provenance, and decision trace. Changing it to embed new outputs would revise a
stable historical contract and couple Analysis serialization to independently
evolving Classification and Metrics records.

The actual identity models are asymmetric:

- Analysis has `gap_id` plus positive `analysis_version`;
- Classification has `classification_id` and
  `classification_policy_version`, but no separate record-version field;
- Metrics has `metric_set_id` and `metric_policy_version`, but no separate
  record-version field.

Policy version is not record version. The integration boundary must preserve
the exact immutable snapshots without pretending those fields are equivalent.

## Decision

Select **Option B: a separate immutable reference-based attachment**.

```text
RealityGapAnalysis <--- RealityGapAnalysisAttachment
                              |
                              +-- classification_reference
                              +-- metric_reference
```

`RealityGapAnalysis` remains unchanged. Classification and Metrics remain
independent artifacts owned by their source layers. The Analysis Layer owns
only the immutable relationship that says which exact outputs are attached to
which exact Analysis revision.

Integration is attachment only. It does not recalculate, reinterpret, mutate,
replace, backfill, or explain the Analysis.

## Why references instead of embedding

Reference attachment preserves independent ownership and versioning, avoids
duplicating complete objects in Analysis serialization, and allows an audit to
verify exact canonical snapshots. A new Classification or MetricSet creates a
new reference and attachment version rather than rewriting the original
Analysis.

The trade-off is that reconstruction needs the exact immutable artifacts to be
provided by a caller or future resolver. This design does not add storage or a
resolver.

## Conceptual artifact references

An attachment reference identifies an exact artifact snapshot, not merely a
logical ID:

- Analysis reference: artifact kind, `gap_id`, and `analysis_version`;
- Classification reference: artifact kind, `classification_id`, canonical
  snapshot digest, and classification-policy version as validation provenance;
- Metric reference: artifact kind, `metric_set_id`, canonical snapshot digest,
  and metric-policy version as validation provenance.

Until Classification and MetricSet gain explicit record-version fields in a
separately reviewed change, the canonical serialization digest is their exact
immutable revision reference. The digest algorithm, encoding, namespace, and
collision policy must be versioned by the future attachment policy. Policy
versions remain separate and must never be used as record versions.

## Conceptual `RealityGapAnalysisAttachment`

The minimum task fields are:

- `analysis_reference`;
- `classification_reference`;
- `metric_reference`;
- `attachment_policy_version`;
- caller-supplied aware UTC `created_at`;
- deeply immutable primitive `metadata`.

Because the record must itself be identifiable and versioned, the future
contract also requires:

- `attachment_id`;
- positive `attachment_version`.

Adding those explicit fields avoids hiding identity/version in metadata or
misusing `attachment_policy_version`. The attachment is frozen, deterministic,
serialization-safe, and lineage preserving.

Both Classification and Metrics references are required in Phase 1. Missing
either produces a typed failure; there is no partial attachment. An optional or
single-artifact attachment requires a separate policy decision.

## Ownership

### Classification Layer

Owns the Classification object, its policy, identity/revision, dimensions,
categories, trace, and serialization.

### Metrics Layer

Owns the MetricSet object, its policy, identity/revision, availability-aware
values, trace, and serialization.

### Analysis Layer

Owns only attachment identity/version, attachment policy, reference validation,
and the relationship among exact artifacts. It owns no Classification or
Metrics values and does not mutate `RealityGapAnalysis`.

## Validation and lineage

A future attachment service receives an existing `RealityGapAnalysis`, an
existing `RealityGapClassification`, an existing `RealityGapMetricSet`, and an
explicit attachment policy. It validates, without modifying them:

- Classification and MetricSet `analysis_reference` both identify the exact
  supplied Analysis ID/version;
- Classification and MetricSet input references are within the Analysis
  candidate/evidence lineage approved by the attachment policy;
- policy versions are approved and internally consistent;
- canonical snapshot digests reproduce the supplied artifact references;
- artifact IDs and attachment ID remain distinct;
- output historical boundaries do not postdate the Analysis creation/evaluation
  boundary allowed by policy;
- no future or outcome-derived input is introduced.

The attachment preserves Analysis, Classification, Metrics, trace, policy, and
snapshot-reference identities separately. It never collapses one into another.

## Versioning

- a changed Analysis creates a new `analysis_version` and Analysis reference;
- a changed Classification creates a new immutable Classification snapshot and
  canonical reference;
- a changed MetricSet creates a new immutable MetricSet snapshot and canonical
  reference;
- a changed attachment relationship or attachment policy creates a new
  `attachment_version`;
- an attachment-policy change never reinterprets an old attachment in place.

Historical Analysis remains readable without Classification/Metrics integration.
Historical attachments remain readable with the exact referenced artifacts and
reference-policy version.

## Anti-hindsight

Attachment may use only already-existing immutable artifacts whose lineage and
historical boundaries match the target Analysis revision. It must reject:

- Classification or Metrics for another Analysis revision;
- output/evidence created outside the approved historical boundary;
- later Timeline entries, outcomes, or learning feedback;
- current defaults substituted for historical policies;
- recalculation during attachment;
- mutation or backfilling of the historical Analysis.

An attachment created operationally after an Analysis is clearly recorded as a
later relationship record. It does not make the attached outputs appear to have
been embedded in the original Analysis.

## Failure model

The future service returns one immutable failure and no attachment for:

- `MISSING_CLASSIFICATION`;
- `MISSING_METRICS`;
- `VERSION_CONFLICT`;
- `ANALYSIS_MISMATCH`;
- `POLICY_CONFLICT`;
- `INVALID_REFERENCE`.

It cannot repair references, select replacement outputs, silently omit one
artifact, or return a partial relationship.

## Serialization and audit

Canonical attachment serialization uses fixed public field names, explicit
artifact kinds, normalized UTC timestamps, deterministic metadata ordering,
and a versioned reference policy. Equal attachments produce identical bytes.

Audit-friendly reconstruction requires the attachment plus exact artifacts
whose canonical digests match its references. Reconstruction validates; it
does not recalculate Classification, Metrics, Analysis, or traces.

## Alternatives considered

### A. Embed complete Classification and MetricSet objects

Rejected. Embedding expands and changes `RealityGapAnalysis`, duplicates
artifacts, couples serialization/versioning, and risks historical rewrites.

### B. Separate reference-based attachment

Selected. It preserves ownership, backward compatibility, immutable history,
independent versioning, and exact snapshot audit.

### C. Recalculate during Analysis integration

Rejected. It violates attachment-only semantics, couples Analysis to consumer
policies, introduces policy drift and hindsight risk, and prevents byte-stable
historical reconstruction.

## Consequences

Positive:

- `RealityGapAnalysis` and existing contracts remain unchanged;
- Classification and Metrics evolve independently;
- exact artifacts and policies remain auditable;
- attachment revisions do not rewrite historical Analysis.

Trade-offs:

- a future caller/resolver must supply exact referenced artifacts;
- digest/reference policy requires explicit versioning and collision rules;
- Classification/MetricSet lack explicit record-version fields today;
- Phase 1 requires both outputs and cannot represent a partial attachment.

## Future implementation

After Architecture Review, a separate task may add the immutable attachment
contract, categorized validation, and a pure attachment service. It must not add
persistence, learning, automatic recalculation, Assembly integration, production
integration, or changes to `RealityGapAnalysis` unless separately approved.
