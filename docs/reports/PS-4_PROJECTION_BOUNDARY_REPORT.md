# PS-4 Candidate Projection Boundary Report

## Summary

This documentation-only task defines the immutable mapping boundary between
conceptual `CandidateHypothesis` and approved `RootCauseCandidate` without
merging their identity, lifecycle, evidence, explanation, tree, or assembly
responsibilities.

## Projection boundary

```text
CandidateHypothesis
        |
        v
CandidateProjection
        |
        v
RootCauseCandidate
        |
        v
RootCauseTree
```

Projection validates an explicit explanation decision and creates an auditable
representation. It assigns no truth, cause, classification, rank, confidence,
metric, or tree placement.

## Ownership

- Candidate Layer: hypothesis, candidate ID/version, lifecycle, evidence
  relationships.
- Projection Layer: projection ID/version, mapping validation, immutable
  projection lineage.
- Explanation Layer: role, disposition, placement, tree, and future authorized
  explanation metrics.
- Assembler: final validation and `RealityGapAnalysis` construction.

## Projection identity

Projection identity is separate from candidate identity. It represents one
hypothesis lineage in a stable explanation context. Multiple projections of one
candidate may coexist. Identity excludes role, disposition, metrics, timestamps,
and mutable tree placement. ID encoding remains deferred.

## Candidate mapping

Category, subject, hypothesis reference, description, evidence refs, and
limitations are preserved from the selected candidate version. Explicit role,
disposition, and placement values come from the Explanation Layer under a
versioned policy.

The existing `RootCauseCandidate.candidate_id` is mapped from `projection_id`
because it is the tree-node identity. Source candidate ID/version remain in the
projection and assembly provenance metadata.

## Status/disposition policy

No automatic mapping is allowed. In particular, `SUPPORTED` does not imply
`ACCEPTED`, `CHALLENGED` does not imply `REJECTED`, and `CREATED` does not imply
`UNRESOLVED`. Projection validates and records an explicit policy decision.

## Evidence handling

Supporting, contradicting, and limitation references must exactly match the
source candidate version. Projection adds, removes, repairs, upgrades,
downgrades, or reinterprets no evidence.

## Tree relationship

Projection carries a stable tree-context reference but creates no tree or
edges. Explanation owns placement. Assembly-facing parent, child, alternative,
and tree candidate references use projection IDs and must satisfy the existing
`RootCauseTree` validator.

## Versioning

Candidate, projection, and tree versions are independent and append-only.
Candidate changes never mutate projections; projection changes never mutate
candidates; tree placement changes never alter candidate identity.

## Existing metric-like fields

Projection does not calculate confidence, temporal precedence, direct
relevance, evidence coverage, or independence. Optional fields remain `None`
without an approved policy. Required `independent_support_count` is a future
explicit explanation input, not a projection calculation.

## Anti-hindsight

Only the selected candidate version, its original evidence boundary, an
explicit explanation decision, and the historical projection policy may be
used. Future evidence, outcomes, later Timeline/candidate versions, learning,
and automatic reinterpretation are forbidden.

## Failure model

Defined categories: `UNKNOWN_CANDIDATE`, `VERSION_MISMATCH`,
`POLICY_MISMATCH`, `INVALID_EVIDENCE_REFERENCE`,
`INVALID_DISPOSITION_MAPPING`, and `TREE_CONTEXT_CONFLICT`. Failure creates no
partial output and mutates no existing artifact.

## Alternatives

- Direct Candidate/RootCause identity: rejected; responsibilities collapse.
- RootCauseCandidate replacing CandidateHypothesis: rejected; tree state leaks
  into hypothesis lifecycle.
- Dedicated projection boundary: selected.

## Production impact

None. Only ADR, specification, and this report are added. Candidate and Reality
Gap contracts, runtime projection, classification, metrics, ranking,
confidence, persistence, learning, production, Telegram, Hostinger, and Outcome
Analysis remain unchanged.

## Open questions

- Which digest, encoding, namespace, and collision strategy will implement
  `projection_id`?
- What stable projection-slot reference distinguishes multiple representations
  of one candidate inside one analysis context?
- Which primitive metadata keys become mandatory for source lineage?
- Which future policy supplies and validates `independent_support_count`?
- Should a role/disposition change always create a projection revision, or can
  a new explanation context require a new projection identity?
- How will a future runtime object represent the separate placement snapshot
  while materializing the current tree-linked `RootCauseCandidate`?

## Recommended Step 7H

First review and implement immutable projection contracts and explicit
Explanation Layer decision inputs in a dedicated task. Only after that boundary
is executable should Step 7H design classification and metrics as consumers of
immutable projections, without candidate/evidence mutation.
