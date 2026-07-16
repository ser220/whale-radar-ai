# PS-4 Classification and Metrics Integration Boundary Specification

## Objective

Define the normative attachment-only boundary that relates exact immutable
`RealityGapClassification` and `RealityGapMetricSet` artifacts to one exact
`RealityGapAnalysis` revision without modifying or recalculating any artifact.

## Scope

This specification defines:

- reference-based attachment architecture;
- ownership and input boundaries;
- conceptual attachment identity, fields, and versions;
- exact lineage and canonical reference rules;
- anti-hindsight and no-partial-result guarantees;
- typed attachment failures;
- deterministic serialization and reconstruction requirements.

## Out of scope

- Python/runtime attachment contracts or services;
- changes to `RealityGapAnalysis`, Classification/Metric contracts, consumers,
  Candidate, Projection, Mapping, Evidence Preparation, or Assembly;
- recalculation, formulas, scoring, ranking, confidence, severity, explanation,
  or causality;
- persistence, repositories, learning, Outcome Analysis, production, Telegram,
  Hostinger, deployment, providers, or networking.

## Normative terminology

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` describe requirements for a future
separately reviewed implementation. This task adds documentation only.

## Selected architecture

The system MUST use a separate immutable reference-based attachment:

```text
RealityGapAnalysis
        ^
        |
RealityGapAnalysisAttachment
        |
        +-- exact RealityGapClassification reference
        +-- exact RealityGapMetricSet reference
```

`RealityGapAnalysis` MUST remain unchanged. Attachment is a new relationship
record, not an embedded field, Analysis revision, assembler step, or consumer.

## Required source objects

A future pure attachment request MUST receive:

- one existing immutable `RealityGapAnalysis` snapshot;
- one existing immutable `RealityGapClassification` snapshot;
- one existing immutable `RealityGapMetricSet` snapshot;
- one approved attachment-policy identity/version;
- one caller-supplied aware UTC attachment timestamp;
- immutable primitive request metadata.

The service MUST NOT load providers, repositories, databases, later Timeline
state, outcomes, current defaults, or learning feedback.

## Canonical artifact references

References MUST include an explicit artifact kind and exact revision material.

### Analysis

The exact revision is `gap_id + analysis_version`. The reference policy MUST
also validate the Analysis canonical snapshot supplied to the service.

### Classification

The reference contains `classification_id` plus a digest of canonical
`RealityGapClassification.to_json_bytes()`. The
`classification_policy_version` is separate validation provenance and MUST NOT
be treated as record version.

### Metrics

The reference contains `metric_set_id` plus a digest of canonical
`RealityGapMetricSet.to_json_bytes()`. The `metric_policy_version` is separate
validation provenance and MUST NOT be treated as record version.

The attachment-policy version owns artifact kind labels, digest algorithm,
encoding, digest length, namespace, and collision handling. Digest choices are
deferred to implementation review. A bare logical ID is insufficient.

## Conceptual `RealityGapAnalysisAttachment`

Required immutable fields:

- `attachment_id: str`;
- `attachment_version: positive int`;
- `analysis_reference: exact artifact reference`;
- `classification_reference: exact artifact reference`;
- `metric_reference: exact artifact reference`;
- `attachment_policy_version: str`;
- `created_at: aware UTC datetime`;
- `metadata: deeply immutable primitive mapping`.

The first six fields from the design request are preserved. Explicit
`attachment_id` and `attachment_version` are additionally required because a
versioned relationship cannot safely hide its identity/version in metadata or
policy version.

The contract MUST be frozen, deterministic, serialization-safe, round-trippable,
and lineage preserving. The three artifact references and attachment ID MUST
remain distinct.

## Required references and no partial attachment

Both Classification and Metrics references are mandatory in Phase 1.
Classification-only or Metrics-only attachment MUST fail. A future optional
attachment policy requires a separate ADR/spec change.

Construction MUST be all-or-nothing. Validation failure creates no partial
attachment and does not mutate any input.

## Ownership

Classification Layer owns its record, policy, dimensions/categories, trace,
canonical bytes, and revision reference.

Metrics Layer owns its record, policy, values/availability, trace, canonical
bytes, and revision reference.

Analysis Layer owns only attachment ID/version, attachment policy, reference
validation, and the immutable relationship. It does not own or copy source
values and MUST NOT call the consumers.

## Lineage validation

Before creating an attachment, the future service MUST validate:

1. Analysis reference identifies the supplied `gap_id` and `analysis_version`.
2. Classification `analysis_reference` identifies that exact Analysis revision.
3. MetricSet `analysis_reference` identifies that exact Analysis revision.
4. Classification and Metrics input references are allowed by the Analysis
   candidate/evidence lineage under the approved attachment policy.
5. Classification and Metrics policy versions are approved by attachment policy.
6. Canonical digests reproduce the exact supplied output snapshots.
7. Attachment identity differs from all artifact identities.
8. Attachment version follows the approved lineage rule.

The attachment MUST preserve Analysis, Classification, Metrics, source trace,
source policy, snapshot digest, and attachment policy identities separately.

## Versioning rules

- Initial relationship uses attachment version 1.
- Replacing any one artifact reference creates the next attachment version.
- Changing attachment policy creates the next attachment version.
- Reordering semantically canonical inputs MUST NOT create a new version.
- Repeating identical input under identical policy MUST reproduce the same
  attachment identity/reference result, not create a divergent revision.
- Historical attachments MUST never be mutated.

Classification/Metric policy versions do not substitute for output revision.
Until explicit record versions are approved, canonical snapshot digest is the
exact revision component.

## Anti-hindsight validation

The future service MUST reject:

- output bound to another Analysis or Analysis version;
- output whose historical boundary postdates the allowed Analysis boundary;
- input references outside the Analysis candidate/evidence lineage;
- future Timeline/evidence references;
- outcome-derived or learning-derived metadata/lineage;
- current policy substituted for the recorded historical policy;
- recalculation or consumer invocation during attachment.

The attachment timestamp records when the relationship was created. A later
attachment MUST NOT mutate or pretend to be part of the original Analysis
snapshot.

## Failure contract

Conceptual categories:

- `MISSING_CLASSIFICATION`;
- `MISSING_METRICS`;
- `VERSION_CONFLICT`;
- `ANALYSIS_MISMATCH`;
- `POLICY_CONFLICT`;
- `INVALID_REFERENCE`.

A future immutable failure MUST contain category, deterministic reason,
attachment-policy version, available source references, caller-supplied UTC
timestamp, and immutable primitive metadata. It MUST NOT contain a partial
attachment or substitute artifact.

## Serialization

`to_dict()` MUST use stable public names and primitive values. Collections and
metadata MUST have canonical deterministic ordering. UTC timestamps MUST use
one normalized ISO-8601 representation. `from_dict()` MUST reject unknown and
missing fields. Canonical JSON bytes MUST use a versioned serialization policy
and produce identical bytes for equal attachments.

## Audit-friendly reconstruction

Reconstruction requires:

- one attachment record;
- exact Analysis, Classification, and MetricSet snapshots;
- attachment reference/serialization policy.

The reconstructor validates IDs, versions, policy provenance, and canonical
digests. It MUST NOT rerun Classification, Metrics, Assembly, explanation, or
source retrieval. No persistence/resolver is defined in this phase.

## Dependency boundary

Future runtime may depend only on Python standard library and approved local
immutable Analysis, Classification, Metrics, and attachment contracts. It MUST
NOT import Telegram, providers, exchange clients, networking, databases,
repositories, pipelines, Assembly, persistence, learning, or Outcome Analysis.

## Acceptance criteria for this design task

- exactly one ADR, one specification, and one report are added;
- reference-based attachment is selected and justified;
- `RealityGapAnalysis` remains unchanged;
- identity/version asymmetry is explicitly addressed;
- ownership, lineage, versioning, failures, serialization, and anti-hindsight
  are normative;
- no runtime, formula, score, rank, confidence, severity, persistence,
  learning, production, Telegram, or Hostinger change is included.

## Verification commands

```bash
git diff --check
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git status --short
```

## Future implementation

After Architecture Review, a separate task MAY implement the immutable
attachment contract, categorized validation, and pure attachment service.
RealityGapAnalysis/Assembly integration, persistence, automatic recalculation,
learning, production integration, and consumer changes remain forbidden unless
separately approved.
