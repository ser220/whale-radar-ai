# ADR: PS-4 Projection to RootCauseCandidate Mapping Boundary

## Status

Proposed; awaiting Architecture Review.

## Context

Whale Radar AI now has an immutable `CandidateProjection` contract and an
existing immutable `RootCauseCandidate` contract. They intentionally represent
different layers:

- `CandidateProjection` preserves one candidate lineage inside an explanation
  context and stores an explicit role/disposition decision plus an exact
  evidence-reference snapshot;
- `RootCauseCandidate` is the tree-facing Explanation Layer record consumed by
  `RootCauseTree` and `RealityGapAnalysis`.

The real contracts are not field-compatible. `CandidateProjection` does not
contain the required target `subject` or `description`, and it contains no
`hypothesis_reference`. The target also requires tree placement fields,
`independent_support_count`, and disposition-specific `rejection_reason`.
Conversely, `RootCauseCandidate` has no explicit candidate, projection,
mapping, or RootCauseCandidate version fields.

A runtime mapper that accepts only `CandidateProjection` would therefore have
to invent missing data, use defaults with hidden meaning, or collapse lineage.
All are forbidden. This task defines a documentation-only boundary and makes
the missing explicit inputs visible.

## Decision

Adopt a dedicated immutable Mapping Layer:

```text
CandidateProjection
        +
ExplanationDescriptorSnapshot
        +
ExplanationDecisionSnapshot
        +
TreePlacementSnapshot
        |
        v
RootCauseCandidateMapping
        |
        v
RootCauseCandidate
        |
        v
RootCauseTree
```

`CandidateProjection` is the primary source input, but it is not a sufficient
input by itself. The additional immutable snapshots contain values owned by the
Explanation Layer. The Mapping Layer validates and copies them under an
explicit policy; it never creates or interprets them.

Mapping is not truth assignment, causal confirmation, classification,
severity, ranking, confidence, metric calculation, or tree generation.

## Ownership

### Candidate Layer

Owns `CandidateHypothesis`, `candidate_id`, `candidate_version`, and hypothesis
lineage.

### Projection Layer

Owns `CandidateProjection`, `projection_id`, `projection_version`, and the
immutable evidence-reference/context snapshot.

### Mapping Layer

Owns mapping identity/version, mapping-policy validation, source/target lineage
preservation, deterministic materialization, and failure records. It owns no
explanation value.

### Explanation Layer

Owns subject/description presentation, hypothesis reference, role,
disposition, disposition decision reference, rejection reason, explicit
independent-support count, and tree placement. It supplies those facts as
immutable snapshots.

In the approved runtime enums, unresolved is a `RootCauseDisposition`, not a
`RootCauseRole`. Explanation may use `UNRESOLVED` disposition with an allowed
non-rejected role; it must not invent an `UNRESOLVED` role.

### Assembler

Owns final validation and construction of `RealityGapAnalysis` from already
mapped candidates and an already-defined tree. It does not perform mapping.

## Conceptual mapping contract

Define an immutable `RootCauseCandidateMapping` audit record containing:

- `mapping_id` and positive `mapping_version`;
- `mapping_policy_version`;
- source candidate ID/version;
- source projection ID/version;
- analysis and tree-context references;
- `root_cause_candidate_id` and conceptual
  `root_cause_candidate_version`;
- exact input snapshot references;
- the immutable mapped `RootCauseCandidate` snapshot;
- caller-supplied aware UTC `created_at`;
- deterministic warnings/failure-free validation facts;
- deeply immutable primitive metadata.

The mapping ID identifies one source projection in one explanation/mapping
context. Digest and encoding are deferred. The mapping record is the owner of
mapping and conceptual RootCauseCandidate revision lineage because the current
target contract has no version field.

## Required immutable mapping request

### CandidateProjection

Supplies projection/candidate lineage, analysis/tree context, category, role,
disposition, evidence refs, limitations, policy version, and creation time.

### ExplanationDescriptorSnapshot

Supplies required `subject`, `description`, and stable
`hypothesis_reference`. These values must reference the same source candidate
lineage and may not be synthesized from metadata.

### ExplanationDecisionSnapshot

Supplies the explicit role/disposition decision reference, rejection reason
when required, and explicit `independent_support_count` plus its provenance.
The mapper does not count independent sources or infer independence.

Role and disposition must exactly agree with the values already stored in the
selected `CandidateProjection`; disagreement is a policy/decision failure.

### TreePlacementSnapshot

Supplies optional parent projection ID, child projection IDs, and alternative
projection IDs for one explicit tree context/version. The Mapping Layer does
not select or calculate placement. A placement-neutral snapshot uses `None`,
empty children, and empty alternatives.

## Field mapping decision

| `RootCauseCandidate` field | Source |
| --- | --- |
| `candidate_id` | source `CandidateProjection.projection_id` |
| `category` | projection category |
| `subject` | descriptor snapshot |
| `description` | descriptor snapshot |
| `role` | explicit decision, equal to projection role |
| `disposition` | explicit decision, equal to projection disposition |
| `confidence` | `None` in this boundary |
| `temporal_precedence` | `None` in this boundary |
| `direct_relevance` | `None` in this boundary |
| `evidence_coverage` | `None` in this boundary |
| `independent_support_count` | explicit Explanation Layer input; never calculated |
| supporting refs | exact projection evidence snapshot |
| contradicting refs | exact projection evidence snapshot |
| `parent_candidate_id` | explicit placement snapshot using projection IDs |
| `child_candidate_ids` | explicit placement snapshot using projection IDs |
| `limitations` | exact projection limitation snapshot |
| `alternative_candidate_ids` | explicit placement snapshot using projection IDs |
| `rejection_reason` | explicit decision input under target invariant |
| `policy_version` | mapping-policy version |
| `metadata` | primitive source/mapping/target lineage and decision references |

The hypothesis reference is preserved in mapping/target primitive provenance;
the current target has no dedicated hypothesis-reference field.

## Identity model

- candidate identity: hypothesis lineage (`candidate_id`, `candidate_version`);
- projection identity: representation lineage (`projection_id`,
  `projection_version`);
- mapping identity: deterministic materialization lineage (`mapping_id`,
  `mapping_version`);
- RootCauseCandidate identity: tree-facing explanation identity, represented by
  `RootCauseCandidate.candidate_id = projection_id`;
- tree identity: tree ID/version supplied outside the mapper.

Multiple mapped records may preserve the same hypothesis lineage through
different projection/explanation contexts. Mapping never replaces or renames
the source candidate identity.

## Disposition and role

`RootCauseDisposition` and `RootCauseRole` belong to the Explanation Layer.
Candidate lifecycle status is not an input to this mapper and has no default
conversion. In particular, supported is not accepted, challenged is not
rejected, and unresolved is not failed.

The mapping validates:

- explicit decision values equal the selected projection snapshot;
- `REJECTED` requires `REJECTED_CANDIDATE` role and a rejection reason;
- non-rejected dispositions forbid rejection reason and rejected role;
- unresolved is a disposition, not a role.

These are contract checks, not analytical decisions.

## Evidence handling

Supporting, contradicting, and limitation references are copied exactly from
the immutable projection snapshot. Mapping cannot add, remove, replace,
reorder outside canonical policy, upgrade/downgrade eligibility, or reinterpret
any reference. Eligibility remains owned by Evidence Preparation and the
approved evidence catalog.

Because `CandidateProjection` stores IDs rather than evidence objects, a future
runtime mapper requires an immutable evidence-catalog view to validate that
every ID still resolves without changing its eligibility. No catalog or lookup
is implemented here.

## Tree relationship

The mapper does not create `RootCauseTree`, roots, edges, or placement. It only
validates/copies an explicit Explanation Layer placement snapshot. All
parent/child/alternative references use projection IDs, resolve inside the same
tree context/version, and must later agree with `RootCauseTree` validation.

## Independent versioning

- candidate version changes only in Candidate Layer;
- projection version changes only in Projection Layer;
- mapping-policy version changes when mapping rules change;
- mapping version changes whenever any mapped representation input changes;
- conceptual RootCauseCandidate version changes with a new immutable mapped
  target snapshot;
- tree version changes with tree structure/placement.

Historical mappings and targets remain readable. A changed policy never
reinterprets an old mapping automatically. Because the current
`RootCauseCandidate` has no explicit version field, its conceptual version and
mapping lineage must be preserved in `RootCauseCandidateMapping` and primitive
target metadata until a separately reviewed contract change is approved.

## Anti-hindsight

Mapping may use only the selected existing projection version, its exact
reference snapshot, immutable descriptor/decision/placement snapshots, the
historical evidence catalog view, and the approved mapping policy. Future
evidence, later Timeline/projection versions, outcomes, learning feedback, and
automatic reinterpretation are forbidden.

## Failure model

Define future immutable `MappingFailure` categories:

- `UNKNOWN_PROJECTION`;
- `VERSION_MISMATCH`;
- `INVALID_LINEAGE`;
- `INVALID_EVIDENCE_REFERENCE`;
- `POLICY_CONFLICT`;
- `INVALID_EXPLANATION_DECISION`.

Failure preserves structured IDs/versions, policy reference, stage, and concise
reason. It creates no partial mapping or `RootCauseCandidate` and mutates no
source or historical output.

## Alternatives considered

### A. Projection equals RootCauseCandidate

Rejected. Projection lineage and Explanation/tree ownership would collapse,
and required target-only data would leak into the projection contract.

### B. Assembler creates RootCauseCandidate

Rejected. The pure construction boundary would acquire explanation decisions,
mapping policy, and lineage responsibilities.

### C. Dedicated mapping boundary

Selected. It makes every non-projection value explicit, preserves independent
lineage, and keeps Assembler and tree generation unchanged.

## Consequences

### Positive

- no missing target value is invented;
- identity and version lineage remain auditable;
- status, role, disposition, metrics, and tree placement stay with their owners;
- evidence references remain exact;
- current runtime contracts remain unchanged;
- future mapping can be deterministic and independently tested.

### Negative and trade-offs

- `CandidateProjection` alone is intentionally insufficient for mapping;
- additional immutable Explanation Layer input contracts are required;
- RootCauseCandidate revision lineage currently relies on mapping record and
  metadata because the target has no version field;
- tree placement is duplicated between mapped candidates and tree validation;
- runtime mapping remains blocked until request/audit contracts and catalog
  validation are separately reviewed.

## Future boundary

After immutable mapping request/result contracts and a pure mapper are
separately reviewed and implemented, Step 7H may consume mapped
`RootCauseCandidate` records, projection lineage, and evidence references. It
must not create candidates, modify projections/evidence, calculate hidden
defaults, or rewrite mapping history.

This task does not implement mapping or begin Step 7H.
