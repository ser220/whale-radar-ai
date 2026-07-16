# PS-4 Projection to RootCauseCandidate Mapping Boundary Report

## Summary

This documentation-only task defines the immutable mapping boundary between
`CandidateProjection` and `RootCauseCandidate`. It preserves Candidate,
Projection, Mapping, Explanation, Tree, and Assembler ownership without
implementing a mapper or analytical behavior.

## Mapping boundary

```text
CandidateProjection
        +
explicit Explanation Layer snapshots
        |
        v
RootCauseCandidateMapping
        |
        v
RootCauseCandidate
```

The real projection alone is not sufficient: it lacks target subject,
description, hypothesis reference, independent-support declaration, rejection
reason, and tree placement. The design therefore requires explicit immutable
descriptor, decision, placement, and historical catalog inputs. Nothing is
inferred from arbitrary metadata.

## Ownership

- Candidate Layer owns hypothesis identity/version.
- Projection Layer owns CandidateProjection identity/version.
- Mapping Layer owns mapping policy, validation, lineage, and failure records.
- Explanation Layer owns descriptors, role, disposition, rejection reason,
  support declaration, and placement.
- Assembler owns final RealityGapAnalysis construction.

## Mapping contract

Conceptual `RootCauseCandidateMapping` records mapping ID/version, policy,
candidate/projection lineage, analysis/tree context, conceptual target version,
input snapshot references, immutable target snapshot, validation facts,
timestamp, and primitive metadata.

## Field mapping

Tree-facing `RootCauseCandidate.candidate_id` equals projection ID. Category and
evidence/limitation refs come from projection. Subject/description come from a
descriptor snapshot. Role/disposition/rejection reason and explicit
independent-support count come from a decision snapshot. Placement comes from a
tree-placement snapshot. Confidence and metric-like optional fields remain
`None`.

## Identity model

Candidate, projection, mapping, target, and tree identities remain separate.
Source candidate ID/version survive in mapping and target primitive provenance.
Multiple targets may preserve one hypothesis lineage through different
projection contexts.

## Disposition and role

Explanation owns both. Mapping performs equality and target-invariant checks
only. No status conversion exists. `UNRESOLVED` is correctly treated as a
disposition; the current enum has no unresolved role.

## Evidence handling

References are copied exactly and checked against a historical immutable
catalog view. Mapping cannot add, remove, change eligibility, or reinterpret
evidence. Evidence Preparation remains the owner.

## Tree relationship

Mapping creates no tree or placement. It validates/copies an explicit
Explanation Layer placement snapshot whose references use projection IDs.
RootCauseTree validation remains authoritative.

## Versioning

Candidate, projection, mapping policy/mapping, conceptual target, and tree
versions are independent. Historical records remain immutable. Because the
current target lacks a version field, its conceptual version is preserved in
the mapping record and target metadata.

## Anti-hindsight

Only historical immutable projection, catalog, descriptor, decision, placement,
and policy snapshots are usable. Future evidence, later Timeline/projection
versions, outcomes, learning, and automatic reinterpretation are forbidden.

## Failure model

Defined failures: `UNKNOWN_PROJECTION`, `VERSION_MISMATCH`, `INVALID_LINEAGE`,
`INVALID_EVIDENCE_REFERENCE`, `POLICY_CONFLICT`, and
`INVALID_EXPLANATION_DECISION`. No partial target or mapping is allowed.

## Alternatives

- Projection equals target: rejected because responsibilities and identity
  collapse.
- Assembler performs mapping: rejected because construction gains explanation
  ownership.
- Dedicated mapping boundary: selected.

## Production impact

None. Only ADR, specification, and report are added. No runtime mapper,
contract, classification, metric, confidence, rank, severity, tree,
persistence, learning, production, Telegram, Hostinger, or Outcome Analysis
change is included.

## Open questions

- What immutable runtime contracts represent descriptor, decision, placement,
  evidence-catalog view, mapping result, and failure?
- What deterministic mapping ID namespace/digest/collision policy is approved?
- Which policy validates independent-support provenance without calculating it?
- Should RootCauseCandidate gain an explicit version in a future contract, or
  remain versioned only through mapping lineage and metadata?
- How are multiple mapping slots distinguished within one projection/tree
  context?
- Must a placement-only change create a new mapping version, a target version,
  or both?

## Recommended Step 7H

Before Step 7H, review and implement the immutable mapping request/result/
failure contracts and a pure mapper in separate tasks. Step 7H may then consume
mapped targets and lineage without changing candidates, projections, evidence,
or historical mappings.
