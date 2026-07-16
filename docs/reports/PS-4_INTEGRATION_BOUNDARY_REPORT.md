# PS-4 Classification and Metrics Integration Boundary Report

## Summary

This documentation-only task defines how exact immutable Classification and
MetricSet outputs relate to one exact `RealityGapAnalysis` revision. The design
selects a separate reference-based `RealityGapAnalysisAttachment` and leaves
Analysis, consumers, contracts, Assembly, and production unchanged.

## Documents

- [ADR](../architecture/adr/ADR-PS-4-classification-metrics-integration-boundary.md)
- [Specification](../specs/PS-4-classification-metrics-integration-boundary.md)
- this report

## Architecture choice

Option B, reference-based attachment, is selected. Full embedding would couple
Analysis serialization and independently evolving outputs. Recalculation during
integration would violate attachment-only semantics and anti-hindsight.

```text
RealityGapAnalysis <--- RealityGapAnalysisAttachment
                              |
                              +-- exact Classification reference
                              +-- exact MetricSet reference
```

## Attachment model

The conceptual immutable attachment contains explicit attachment ID/version,
exact Analysis/Classification/Metric references, attachment-policy version,
caller-supplied UTC timestamp, and immutable metadata. Both output references
are mandatory; validation is all-or-nothing.

## Identity and lineage

Analysis uses `gap_id + analysis_version`. Current Classification and MetricSet
records lack explicit record-version fields, so their exact revision reference
uses ID plus a canonical snapshot digest. Classification/metric policy versions
remain separate validation provenance and are not misused as record versions.

The Analysis Layer owns only the relationship. Classification and Metrics retain
ownership of objects, policies, values, traces, and canonical serialization.

## Versioning

A changed source snapshot or attachment policy creates a new attachment version.
Historical Analysis and attachments remain immutable and readable. No source
record is rewritten or reinterpreted.

## Anti-hindsight

Attachment validates exact Analysis alignment, source/input lineage, policy
versions, snapshot digests, and historical boundaries. Future output/evidence,
later Timeline entries, outcomes, learning feedback, recalculation, and
historical Analysis backfilling are forbidden.

## Failures

Defined categories: `MISSING_CLASSIFICATION`, `MISSING_METRICS`,
`VERSION_CONFLICT`, `ANALYSIS_MISMATCH`, `POLICY_CONFLICT`, and
`INVALID_REFERENCE`. Failures produce no partial attachment.

## Repository impact

Only the Step 7H Integration Boundary ADR, specification, and report are added.
There is no Python/runtime, `RealityGapAnalysis`, Assembly, consumer, contract,
formula, scoring, ranking, confidence, severity, persistence, learning,
production, Telegram, Hostinger, or Outcome Analysis change.

## Open questions

- What attachment reference-policy version, digest algorithm, encoding, and
  collision strategy should the first runtime contract use?
- Should Classification and MetricSet gain explicit record-version fields in a
  future independently reviewed contract revision?
- What exact canonical Analysis reference grammar maps `gap_id` and
  `analysis_version` without ambiguity?
- Which policy proves that output input references are a valid subset of the
  Analysis candidate/evidence lineage?
- Should a later phase support classification-only or metrics-only attachments,
  or preserve the all-or-nothing Phase 1 rule?

## Recommended next step

Submit this design for Architecture Review. Do not implement the attachment
contract or service until separately approved.
