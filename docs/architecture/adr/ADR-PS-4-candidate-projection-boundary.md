# ADR: PS-4 Candidate Projection Boundary

## Status

Proposed; awaiting Architecture Review.

## Context

PS-4 Step 7G defined a conceptual immutable `CandidateHypothesis`: an
evidence-referenced hypothesis with its own identity, version, and lifecycle.
The approved Reality Gap runtime already contains `RootCauseCandidate`, an
explanation-layer and assembly record whose ID, role, disposition, optional
metrics, and parent/child references must agree with `RootCauseTree`.

These objects cannot be treated as aliases. A hypothesis can participate in
more than one explanation context, while a tree-facing candidate represents
one placement and disposition inside a particular analysis. Directly copying
the hypothesis ID into every `RootCauseCandidate.candidate_id` would collapse
those identities and make multiple projections ambiguous.

This task defines the mapping boundary only. It changes no runtime contract and
implements no projection, classification, metric, rank, confidence, causal
decision, persistence, learning, or production behavior.

## Decision

Introduce a future immutable Candidate Projection Boundary:

```text
CandidateHypothesis
        |
        | hypothesis identity and evidence snapshot
        v
Candidate Projection Boundary
        |
        | validated explicit explanation decision
        v
CandidateProjection
        |
        | assembly-compatible projection
        v
RootCauseCandidate
        |
        v
RootCauseTree
```

Projection is a deterministic representation step. It does not decide whether
a hypothesis is true, select a role or disposition, calculate confidence or
metrics, rank candidates, or create tree structure. Role, disposition, and
placement values are owned by the Explanation Layer and must be supplied
explicitly under a versioned projection policy.

## Ownership model

### Candidate Layer

Owns:

- `CandidateHypothesis`;
- `candidate_id` and `candidate_version`;
- hypothesis identity and lifecycle;
- the immutable support, contradiction, and limitation relationships captured
  by each candidate version.

### Projection Layer

Owns:

- `projection_id` and `projection_version`;
- projection identity-policy and mapping-policy versions;
- validation of an explicit mapping decision;
- immutable projection lineage;
- preservation of the source candidate and evidence snapshot.

It does not own the semantic decision values it validates.

### Explanation Layer

Owns:

- explanation-context membership;
- `RootCauseRole` and `RootCauseDisposition` decisions;
- root, parent, child, and alternative placement;
- `RootCauseTree` structure and `tree_version`;
- any future explicitly authorized explanation metrics.

### Assembler

Owns final validation and construction of `RealityGapAnalysis`. It receives
already-projected `RootCauseCandidate` records and an already-constructed tree.
It remains free of projection and analytical decision logic.

## Projection identity

Candidate identity means “the hypothesis itself.” Projection identity means
“one representation of that candidate lineage inside an explanation context.”
They are separate namespaces.

Conceptual deterministic projection identity material is:

1. projection identity-policy version;
2. projection namespace;
3. source `candidate_id`;
4. stable `analysis_context_id`;
5. stable projection-slot/context reference.

Role, disposition, metrics, timestamps, and mutable tree placement are not
projection identity material. Their change creates a new projection version,
or only a new tree version when the projection payload is unchanged. A source
`candidate_version` change creates a new projection version under the same
projection ID when the candidate lineage and context remain the same.

The same candidate may therefore have different projection IDs in different
analysis or projection contexts—for example primary in one explanation and
alternative in another. Digest, encoding, length, and collision handling remain
deferred to a separately reviewed runtime contract.

## Conceptual `CandidateProjection`

The future immutable record contains at least:

- `projection_id` and positive `projection_version`;
- source `candidate_id` and positive `candidate_version`;
- `projection_policy_version` and identity-policy version;
- `analysis_context_id`;
- category, subject, hypothesis reference, and description snapshot;
- explicitly supplied role and disposition;
- `tree_context_reference`;
- ordered supporting and contradicting evidence-reference snapshots;
- ordered limitation references;
- caller-supplied aware UTC `created_at`;
- deeply immutable primitive metadata.

The extra source-description and reference fields are explicit because hiding
them in metadata or one opaque evidence object would prevent deterministic,
auditable mapping to the existing `RootCauseCandidate` fields.

## Mapping to the approved `RootCauseCandidate`

The assembly-facing mapping is explicit:

| `RootCauseCandidate` field | Projection source |
| --- | --- |
| `candidate_id` | `CandidateProjection.projection_id` |
| `category` | validated category snapshot |
| `subject` | validated subject snapshot |
| `description` | validated description snapshot |
| `role` | explicit Explanation Layer decision |
| `disposition` | explicit versioned policy decision |
| supporting/contradicting refs | exact preserved projection snapshot |
| `limitations` | exact preserved limitation snapshot |
| parent/child/alternative refs | explicit tree-placement snapshot supplied by Explanation Layer |
| `rejection_reason` | explicit policy output required only for rejection |
| `policy_version` | projection mapping-policy version |
| metadata | source candidate/projection lineage and policy references |

The original hypothesis ID is never overwritten: source `candidate_id` and
`candidate_version` remain in the projection and in the primitive provenance
metadata of the assembly projection.

Existing optional `confidence`, `temporal_precedence`, `direct_relevance`, and
`evidence_coverage` fields are `None` unless a future separately approved layer
supplies them. Projection does not calculate them. The required
`independent_support_count` must be explicit caller-supplied explanation input
validated by a future runtime contract; this boundary neither infers
independence nor calculates that value.

## Status and disposition

There is no default mapping from conceptual `CandidateStatus` to
`RootCauseDisposition`:

- `SUPPORTED` is not automatically `ACCEPTED`;
- `CHALLENGED` is not automatically `REJECTED`;
- `CREATED` is not automatically `UNRESOLVED`;
- `REJECTED` candidate lifecycle status does not bypass explanation policy.

A future explicit `ProjectionPolicy` consumes a candidate status snapshot and
an Explanation Layer decision and validates the selected disposition. Its
version is mandatory. Projection stores the result and policy reference; it
does not derive the result.

## Evidence preservation

Projection uses only evidence references already present in the selected
candidate version. It must preserve supporting references, contradicting
references, limitations, order/canonicalization policy, eligibility, and source
lineage.

Projection cannot add, remove, replace, repair, upgrade, downgrade, or
reinterpret evidence. A request that does not reproduce the exact candidate
evidence snapshot fails. Tree placement and disposition cannot change evidence.

## Relationship with `RootCauseTree`

`CandidateProjection.tree_context_reference` identifies the explanation/tree
context for which projection was prepared. It is not a tree, edge, parent, or
child assignment.

The Explanation Layer supplies placement separately. When materialized into the
current `RootCauseCandidate`, the record must use projection IDs for its own ID
and all parent, child, and alternative references. Those references must agree
with `RootCauseTree.candidate_ids` and edges. Projection never creates a tree or
automatically assigns placement.

## Independent version lineages

- `candidate_version` changes when the hypothesis revision changes;
- `projection_version` changes when its representation, source candidate
  version, role, disposition, mapping policy, evidence snapshot validation, or
  projection-level context changes;
- `tree_version` changes when explanation structure or placement changes.

A new tree placement does not change candidate identity. A tree-only change
need not change projection version when the projection stores only a stable
tree-context reference; its materialized assembly record is regenerated for
the new tree version without mutating prior records. A changed candidate
version never mutates an old projection. All prior versions remain readable.

## Anti-hindsight

Projection may use only the selected existing candidate version, its exact
evidence references, the approved analysis boundary, the explicit Explanation
Layer decision, and the approved projection policy version. It must not use
future evidence, outcomes, learning feedback, later Timeline data, later
candidate revisions, or automatic reinterpretation. Creation timestamps are
caller-supplied and never define identity.

## Failure model

Define future immutable `ProjectionFailure` categories:

- `UNKNOWN_CANDIDATE`;
- `VERSION_MISMATCH`;
- `POLICY_MISMATCH`;
- `INVALID_EVIDENCE_REFERENCE`;
- `INVALID_DISPOSITION_MAPPING`;
- `TREE_CONTEXT_CONFLICT`.

A failure preserves a concise structured reason, involved IDs/versions, and
policy references. It creates no partial projection or partial
`RootCauseCandidate`, and mutates neither hypotheses nor previous projections.

## Alternatives considered

### A. `CandidateHypothesis` directly equals `RootCauseCandidate`

Rejected. Hypothesis lifecycle, explanation disposition, metrics, and tree
placement would collapse into one identity and one mutable responsibility.

### B. `RootCauseCandidate` replaces `CandidateHypothesis`

Rejected. The hypothesis could not exist independently of one explanation or
be reused across contexts without carrying tree-specific state.

### C. Dedicated Candidate Projection Boundary

Selected. It preserves independent candidate, projection, and tree lineages and
makes every explanation-layer decision explicit and auditable.

## Consequences

### Positive

- hypothesis identity is preserved independently of explanation context;
- multiple projections of one hypothesis are unambiguous;
- evidence cannot drift during projection;
- status/disposition and candidate/tree responsibilities stay separate;
- existing approved runtime contracts need not change in this design task;
- future assembly records retain source candidate lineage.

### Negative and trade-offs

- a future runtime contract must define projection ID encoding and primitive
  provenance keys;
- the current `RootCauseCandidate` uses `candidate_id` for a tree-node identity,
  so the projection ID must occupy that field;
- tree linkage is duplicated in the assembly projection and tree contract and
  must remain consistent;
- required metric-like fields need explicit future input policy even when no
  metric engine is enabled.

## Future boundary

After a separately reviewed runtime projection contract exists, Step 7H may
consume immutable `CandidateProjection` records, evidence references, and
Explanation Layer structures for classification and metrics. It must not
create/mutate candidates, change evidence, silently map status to disposition,
or rewrite projection/tree history.

This task does not implement or begin Step 7H.
