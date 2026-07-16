# PS-4 Candidate Projection Boundary Specification

## Objective

Define the immutable, deterministic mapping boundary between conceptual
`CandidateHypothesis` records and approved `RootCauseCandidate` assembly
records without merging hypothesis, projection, explanation, tree, or assembly
ownership. This specification is documentation-only.

## Scope

This specification defines:

- ownership of candidate, projection, explanation, and assembly artifacts;
- projection identity and lineage;
- conceptual `CandidateProjection` fields;
- explicit source-to-projection and projection-to-assembly mapping;
- status/disposition separation;
- evidence preservation;
- tree-context and placement rules;
- independent candidate/projection/tree versions;
- anti-hindsight and failure behavior;
- future Step 7H consumption boundary.

## Out of scope

- runtime projection code or runtime contracts;
- modifications to Candidate or Reality Gap contracts;
- candidate creation/generation or causal detection;
- automatic role, disposition, classification, ranking, confidence, metric, or
  severity decisions;
- tree construction or automatic parent/child assignment;
- evidence extraction, mutation, eligibility changes, or new evidence;
- persistence, learning, historical similarity, Outcome Analysis;
- production, Telegram, Hostinger, deployment, provider, database, repository,
  cache, API, or networking changes.

## Normative language

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` describe requirements for a future
reviewed implementation. This Candidate Projection Boundary task contains no
runtime code.

## Core semantics

`CandidateHypothesis` is an immutable evidence-referenced hypothesis.
`RootCauseCandidate` is an explanation/assembly projection used by
`RootCauseTree` and `RealityGapAnalysis`.

Projection is not truth assignment, causal confirmation, classification,
ranking, confidence calculation, metric calculation, or evidence evaluation.

## Ownership requirements

### Candidate Layer MUST own

- `CandidateHypothesis`;
- `candidate_id` and `candidate_version`;
- hypothesis identity, status, and lifecycle;
- support, contradiction, and limitation references in each immutable version.

### Projection Layer MUST own

- `projection_id` and `projection_version`;
- projection identity and mapping policy versions;
- validation of explicitly supplied mapping decisions;
- immutable projection lineage and source snapshots.

It MUST NOT author role, disposition, placement, confidence, or metrics.

### Explanation Layer MUST own

- analysis-context membership;
- role and disposition decisions;
- tree root/parent/child/alternative placement;
- `RootCauseTree` and `tree_version`;
- any future separately authorized explanation metrics.

### Assembler MUST own

- final contract validation;
- deterministic construction of `RealityGapAnalysis` from already-prepared
  evidence, candidates, tree, and decision trace.

The Assembler MUST NOT create hypotheses, projections, or explanation choices.

## Projection identity policy

Projection identity is separate from candidate identity:

- candidate identity: the hypothesis itself;
- projection identity: one representation of a candidate lineage inside an
  explanation context.

Conceptual fixed-order identity material:

1. projection identity-policy version;
2. projection namespace;
3. source `candidate_id`;
4. normalized `analysis_context_id`;
5. normalized stable projection-slot/context reference.

The same normalized material under the same policy version MUST produce the
same `projection_id`. Different candidate lineage or explanation context MUST
produce a different projection identity. ID generation MUST be independent of
runtime, host, database, random UUID, current time, locale, environment,
network, and collection/hash order.

Role, disposition, metrics, timestamp, and mutable tree placement MUST NOT be
identity material. A changed source `candidate_version` or representation
creates a new projection version rather than silently changing identity.

Digest, encoding, ID length, collision policy, and projection namespace values
are deferred to a future reviewed runtime contract.

## Conceptual `CandidateProjection`

Required fields:

- `projection_id: str`;
- `projection_version: int`;
- `candidate_id: str`;
- `candidate_version: int`;
- `projection_identity_policy_version: str`;
- `projection_policy_version: str`;
- `analysis_context_id: str`;
- `category`;
- `subject: str`;
- `hypothesis_reference: str`;
- `description: str`;
- `role`;
- `disposition`;
- `tree_context_reference: str`;
- ordered `supporting_evidence_refs`;
- ordered `contradicting_evidence_refs`;
- ordered `limitation_references`;
- `created_at` as an aware UTC datetime;
- deeply immutable primitive `metadata`.

`evidence_reference_snapshot` is the combined immutable view of the explicit
supporting and contradicting fields plus their source eligibility/lineage
facts. It MUST NOT be an opaque mutable provider payload.

### Contract behavior

1. IDs, versions, category, subject, hypothesis reference, role, disposition,
   context, and policy versions are required.
2. Integer versions are positive; booleans are invalid.
3. Timestamp is caller-supplied, timezone-aware, and normalized to UTC.
4. Collections are immutable, unique, deterministic, and primitive-serializable.
5. Supporting and contradicting sets are disjoint.
6. Metadata is deeply immutable and contains no secrets or runtime objects.
7. `to_dict()`/`from_dict()` must preserve all identities, versions, enums,
   timestamps, evidence relationships, and context.
8. No candidate, input, tree, or prior projection is mutated.

## Candidate-to-projection mapping

The following source facts MAY be copied after validation:

- source `candidate_id` and `candidate_version`;
- category, subject, hypothesis reference, and description;
- exact supporting and contradicting evidence references;
- exact limitation references;
- source candidate policy/identity versions in provenance metadata.

The following MUST NOT be inferred or automatically copied:

- `CandidateStatus` into `RootCauseDisposition`;
- candidate status into role;
- any field into confidence, relevance, temporal precedence, evidence coverage,
  rank, classification, severity, or final truth;
- any candidate field into tree parent/child/alternative placement.

## Projection decision input

A future mapping request MUST carry an explicit immutable Explanation Layer
decision containing:

- selected source candidate ID/version;
- analysis context and tree-context reference;
- role;
- disposition;
- disposition decision reference and projection policy version;
- explicit tree-placement snapshot when materializing an assembly record;
- explicit rejection reason when disposition is `REJECTED`;
- any metric-like field values only when a separately approved capability and
  policy authorizes them.

Projection validates and preserves this decision; it does not produce it.

## Status-to-disposition policy

There is no default automatic mapping.

```text
CandidateStatus snapshot
          +
explicit Explanation Layer decision
          +
versioned ProjectionPolicy
          |
          v
validated RootCauseDisposition snapshot
```

The projection-policy version MUST be explicit and preserved. It may validate
an allowed decision but MUST NOT silently convert:

- `SUPPORTED` to `ACCEPTED`;
- `CHALLENGED` to `REJECTED`;
- `CREATED` to `UNRESOLVED`;
- any status into a truth value.

## Evidence handling

For the selected candidate version, projection MUST preserve exactly:

- supporting evidence references;
- contradicting evidence references;
- limitation references;
- evidence eligibility and source-lineage facts;
- deterministic ordering/canonicalization policy.

Projection MUST NOT add, remove, replace, repair, upgrade, downgrade, or
reinterpret evidence. Ineligible evidence remains ineligible. Missing or
unavailable evidence remains a limitation. A mismatch between requested and
source snapshots is an `INVALID_EVIDENCE_REFERENCE` failure.

## Projection-to-`RootCauseCandidate` mapping

The approved runtime contract is mapped as follows:

| Target field | Required source/policy |
| --- | --- |
| `candidate_id` | `projection_id` |
| `category` | candidate category snapshot |
| `subject` | candidate subject snapshot |
| `description` | candidate description snapshot |
| `role` | explicit Explanation Layer role |
| `disposition` | explicit validated disposition |
| `supporting_evidence_refs` | exact supporting snapshot |
| `contradicting_evidence_refs` | exact contradicting snapshot |
| `limitations` | exact limitation snapshot |
| `parent_candidate_id` | explicit placement using projection IDs |
| `child_candidate_ids` | explicit placement using projection IDs |
| `alternative_candidate_ids` | explicit placement using projection IDs |
| `rejection_reason` | explicit decision reason for rejected disposition |
| `policy_version` | projection mapping-policy version |
| `metadata` | source candidate/projection lineage and policy references |

The target metadata SHOULD contain primitive keys for source `candidate_id`,
source `candidate_version`, `projection_id`, `projection_version`,
`analysis_context_id`, and policy versions. It MUST NOT contain the source
object or mutable payload.

### Existing metric-like target fields

- `confidence`, `temporal_precedence`, `direct_relevance`, and
  `evidence_coverage` MUST be `None` unless supplied by a separately approved
  capability and policy. Projection MUST NOT calculate them.
- `independent_support_count` MUST be an explicit input from a future approved
  explanation policy. Projection may validate type and provenance but MUST NOT
  infer evidence independence or calculate the count.

## Tree relationship

`tree_context_reference` identifies the intended explanation/tree context. It
does not create a tree or assign an edge.

The Explanation Layer owns all placement. When an existing
`RootCauseCandidate` is materialized:

1. its `candidate_id` is the projection ID;
2. parent, children, and alternative references use projection IDs;
3. every reference resolves within the same tree context;
4. placement agrees exactly with `RootCauseTree.candidate_ids`, roots, edges,
   disposition groups, and maximum-depth validation;
5. projection does not automatically choose or modify placement.

One source candidate MAY have multiple projections in different contexts. Each
tree references the applicable projection IDs, never ambiguous source IDs.

## Independent versioning

### Candidate version

Changes only through the Candidate Layer. A changed candidate version does not
mutate existing projections.

### Projection version

Changes when the source candidate version, role, disposition, description
snapshot, mapping policy, validated evidence snapshot, or projection-level
context changes. Previous projection versions remain readable.

### Tree version

Changes when roots, edges, placement, alternatives, or tree structure changes.
A tree-only placement change does not change candidate identity. If the stable
projection context and payload are unchanged, it need not change projection
version; a new assembly projection is produced for the new tree version while
old records remain immutable.

No version is edited in place, skipped silently, or inferred from current time.

## Deterministic ordering

A future policy SHOULD use:

- support and contradiction refs in canonical evidence-ID order;
- limitations by stable reference type then ID;
- projections by `projection_id`;
- placement references by projection ID;
- validation/failure details in fixed policy order.

No output depends on hash/set order, provider arrival order, race, locale, host,
or environment.

## Anti-hindsight requirements

Projection may consume only:

- one existing immutable candidate version;
- that version's exact evidence and limitations;
- the original approved analysis boundary;
- an explicit Explanation Layer decision;
- an approved projection policy.

It MUST NOT consume future evidence, outcomes, learning feedback, historical
similarity, later Timeline entries, later candidate versions, or current
defaults substituted for historical policy. It MUST NOT reinterpret an old
projection automatically after any later change.

## Failure model

Future immutable `ProjectionFailure` categories:

- `UNKNOWN_CANDIDATE`;
- `VERSION_MISMATCH`;
- `POLICY_MISMATCH`;
- `INVALID_EVIDENCE_REFERENCE`;
- `INVALID_DISPOSITION_MAPPING`;
- `TREE_CONTEXT_CONFLICT`.

Failure MUST preserve category, concise reason, projection attempt reference,
candidate/projection/policy versions, and relevant sanitized IDs. It MUST
create no partial projection or assembly candidate and mutate no prior record.

## Acceptance criteria for future implementation

1. Candidate and projection IDs remain distinct and traceable.
2. Same normalized projection identity material produces the same projection
   ID; different context produces a different ID.
3. Multiple projections of one candidate can coexist without tree-ID collision.
4. Candidate status never maps automatically to disposition.
5. Evidence and limitations exactly match the selected candidate version.
6. Projection creates no evidence, role, disposition, placement, confidence,
   metric, rank, classification, severity, or truth decision.
7. Assembly-facing candidate and tree references use projection IDs and agree.
8. Candidate, projection, and tree versions are independent and immutable.
9. Canonical primitive serialization is deterministic and round-trippable.
10. No persistence, provider, Telegram, production, learning, Hostinger, or
    Outcome Analysis dependency exists.

## Alternatives

### Direct identity equivalence

Rejected because candidate lineage and explanation/tree-node identity would
collapse.

### Replace hypotheses with `RootCauseCandidate`

Rejected because explanation state and tree placement would contaminate the
hypothesis lifecycle.

### Dedicated projection boundary

Selected because it preserves all ownership and version boundaries while
supporting the approved assembly contract.

## Future boundary

After a separately reviewed runtime projection contract, Step 7H may consume
immutable projections, evidence references, and explanation structures. It
must not create/mutate candidates, alter evidence, rewrite projection history,
or infer unavailable values.

## Verification for this task

```bash
git diff --check
git diff --stat
git diff --name-status
git status --short
```

Only this specification, its ADR, and its report may be added. No runtime,
contract, classification, metric, ranking, confidence, persistence, learning,
production, Telegram, Hostinger, or Outcome Analysis file may change.
