# PS-4 Step 7E — Reality Gap Orchestration and Stable Identity Specification

## Objective

Define the future orchestration boundary that coordinates deterministic
identity, lifecycle order, immutable version lineage, validation, and approved
Reality Gap assembly. This specification is documentation-only and introduces
no runtime contract or service.

## Scope

This specification defines:

- separation of preparation, orchestration, and assembly;
- canonical lifecycle and artifact ownership;
- ownership and semantic material for stable IDs;
- version and correction rules;
- conceptual orchestration request/result/trace contracts;
- creation and anti-mutation boundaries;
- anti-hindsight requirements;
- deterministic failure categories;
- boundaries for later Steps 7F through 7I.

## Out of scope

- runtime implementation of an orchestrator or ID generator;
- selection of a hash, encoding, cryptographic primitive, or ID length;
- evidence discovery or extraction;
- Root Cause Candidate generation or merging;
- Reality Gap classification;
- Surprise, Knowledge Gap, Explanation Confidence, residual, severity, or any
  metric calculation;
- Timeline, Expectation, or Evaluation mutation;
- persistence, database schema, cache, repository, or deployment;
- learning, historical pattern matching, Outcome Analysis, Telegram,
  production decisions, notifications, or Hostinger changes.

## Normative terminology

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` describe requirements for a future
implementation. No such implementation is part of Step 7E.

## Responsibility separation

### Preparation

Preparation MUST create approved primitive snapshots and immutable evidence
references. It MUST own `evidence_id`. It MUST NOT orchestrate the full
lifecycle, invoke providers through orchestration, classify gaps, create
candidates, or calculate metrics as an implicit side effect.

### Orchestration

The future `RealityGapOrchestrator` MUST:

1. receive already-prepared primitive inputs;
2. validate lifecycle stage and identity material;
3. create deterministic `gap_id` and `trace_id` under explicit policy versions;
4. validate IDs owned by preparation, candidate, and tree layers;
5. validate capability and version coherence before assembly;
6. construct one `RealityGapAssemblyInput` without mutating inputs;
7. invoke `RealityGapAssembler` once per successful attempt;
8. return the immutable analysis plus structured orchestration facts.

It MUST NOT discover evidence, interpret the market, create Root Cause
Candidates, classify gaps, calculate metrics/severity, learn, persist, notify,
or modify production decisions.

### Assembly

`RealityGapAssembler` remains the sole creator of the
`RealityGapAnalysis` aggregate. It MUST NOT generate identifiers or own
lifecycle coordination. Its approved Step 7D behavior remains unchanged.

No component may combine all three responsibilities.

## Canonical lifecycle

```text
Observation
  -> Expectation
  -> Evaluation
  -> Reality Gap Preparation
  -> Reality Gap Orchestration
  -> Reality Gap Assembly
  -> Immutable RealityGapAnalysis
  -> Future Learning Consumption
```

Each transition MUST reference an existing immutable predecessor artifact.
Later stages MUST NOT mutate earlier artifacts. A successful analysis is
append-only. A correction MUST create `analysis_version + 1` and pass existing
revision validation. Future learning MUST consume completed records only and
MUST NOT influence their historical creation.

## Identity ownership matrix

| Field | Owner | Orchestrator action | Assembler action |
|---|---|---|---|
| `gap_id` | Orchestrator | Generate and validate | Validate/preserve |
| `trace_id` | Orchestrator | Generate and validate | Validate/preserve |
| `evidence_id` | Preparation | Validate uniqueness/preserve | Validate references/preserve |
| `candidate_id` | Future Candidate layer | Validate uniqueness/preserve | Validate references/preserve |
| `tree_id` | Future Explanation/Tree layer | Validate/preserve | Validate tree/preserve |
| analysis aggregate | Assembler | Invoke and return | Construct exactly once |

The orchestrator MUST NOT replace or rewrite an ID owned by another layer.

## Stable ID policy

Every stable identity MUST be:

- deterministic for identical normalized semantic material;
- reproducible without process state;
- independent of host, environment, deployment, locale, database sequence,
  random UUID, and current timestamp;
- scoped by an explicit artifact namespace;
- tied to an identity-policy version;
- generated from a fixed ordered field sequence with unambiguous boundaries.

Canonicalization MUST reject missing required identity material and ambiguous
or duplicate fields. It MUST NOT silently trim, reorder, substitute, or infer
semantic values unless that normalization is explicitly part of the policy.
The future implementation MUST test byte-for-byte canonical material before it
selects an ID algorithm.

Step 7E deliberately does not prescribe a cryptographic implementation.

## `gap_id` policy

`gap_id` identifies one Reality Gap lineage, not one revision. Required
conceptual material, in fixed policy order:

1. identity-policy version;
2. analysis-lineage namespace;
3. `expectation_id`;
4. `evaluation_id`;
5. `timeline_id`;
6. normalized uppercase asset.

The same semantic material MUST produce the same ID. A changed expectation or
evaluation identity MUST produce a different lineage. `analysis_version`,
creation time, process, host, and current policy execution time MUST NOT be
part of `gap_id` material.

## `trace_id` policy

`trace_id` identifies one deterministic orchestration/assembly path. Required
conceptual material:

1. identity-policy version;
2. `gap_id`;
3. trace-policy version;
4. orchestration-context version.

It MUST NOT identify the market situation or replace `timeline_id`. A changed
orchestration/trace policy MAY create a new trace ID without changing the gap
lineage.

## Evidence identity policy

Preparation owns `evidence_id`. It MUST assign the ID before orchestration.
The orchestrator and assembler MUST preserve it exactly. Duplicate evidence IDs
MUST fail validation. The same immutable evidence reference reused within a
later analysis revision SHOULD retain its ID. Orchestration MUST NOT discover,
clone, merge, or synthesize evidence.

## Candidate identity policy

The future Candidate layer owns `candidate_id`. It MUST assign identity before
orchestration. The orchestrator and assembler validate uniqueness and
references only. Neither MAY create, combine, deduplicate semantically, or
rewrite candidates. Candidate policy/version changes that alter candidate
meaning require a new analysis revision.

## Tree identity policy

The future Explanation/Tree layer owns `tree_id`. One tree ID/version pair
identifies one immutable explanatory structure. A changed structure MUST create
the identity/version prescribed by the future tree policy. Previous structures
remain readable and immutable. Orchestration validates the declared tree
identity/version; assembly validates structure and references.

## Version ownership and lineage

| Version/identity | Meaning |
|---|---|
| `gap_id` | Stable lineage identity |
| `analysis_version` | Immutable revision number |
| identity-policy version | Canonical identity meaning |
| orchestration version | Lifecycle coordination contract |
| policy versions | Rules used to prepare/classify/validate supplied facts |
| `trace_version` | Audit record format |
| `taxonomy_version` | Category meanings |
| `tree_version` | Explanatory structure format/version |

No version field may silently change meaning. A semantically relevant version
change MUST create a new analysis revision. Historical versions MUST remain
readable. Analysis version 1 creates a lineage record; later versions retain
the same gap/expectation/evaluation/Timeline/asset identity and use the existing
anti-hindsight revision validator.

## Conceptual orchestration contracts

### `RealityGapOrchestrationRequest`

Contains:

- prepared primitive assembly material or a fully prepared assembly input
  payload without orchestrator-owned IDs finalized;
- analysis-lineage namespace;
- identity-policy version;
- orchestration version;
- declared policy, trace, taxonomy, and tree versions;
- caller-supplied timestamps already bounded by the evaluation window;
- primitive immutable orchestration metadata.

It MUST NOT contain provider clients, database sessions, mutable Timeline,
Expectation or Evaluation runtime objects, outcome facts, learning state,
notification clients, or secrets.

### `RealityGapOrchestrationResult`

Contains:

- immutable `RealityGapAnalysis`;
- generated `gap_id` and `trace_id`;
- immutable orchestration trace;
- validation summary;
- orchestration version and identity-policy version.

The result MUST be deterministic for identical normalized request material and
versions.

### `RealityGapOrchestrationTrace`

Contains structured fields for:

- `orchestration_id` and orchestration version;
- lifecycle stage reached;
- identity decisions and identity-policy version;
- validation checks/results;
- assembly invocation status/result reference;
- caller-supplied UTC timestamps;
- deterministic warnings;
- failure category/reason when unsuccessful.

The trace MUST contain concise audit facts only. It MUST NOT contain private
reasoning, chain of thought, market interpretation, or newly inferred facts.

## Creation order

A future successful orchestration attempt MUST use this order:

1. validate request shape and primitive-only boundary;
2. validate predecessor identity and lifecycle stage;
3. validate anti-hindsight evidence/Timeline boundary;
4. canonicalize documented gap identity material;
5. create/validate `gap_id`;
6. canonicalize documented trace identity material;
7. create/validate `trace_id`;
8. validate caller-owned evidence/candidate/tree IDs and uniqueness;
9. validate all policy/version declarations;
10. construct immutable `RealityGapAssemblyInput`;
11. invoke `RealityGapAssembler` exactly once;
12. return immutable result and successful orchestration trace.

An unsuccessful attempt stops at the failing step and creates no partial
analysis.

## Creation and anti-mutation boundary

### Before analysis construction

Allowed:

- preparation of approved primitive values;
- deterministic creation of orchestrator-owned IDs;
- validation of references, lifecycle, capabilities, and versions;
- construction of immutable assembly input.

### After analysis construction

Forbidden:

- modifying evidence or eligibility;
- changing candidates, dispositions, or tree;
- changing classification, dimensions, metrics, severity, trace, versions,
  provenance, capabilities, or source snapshots;
- adding outcome, learning, or future evidence.

Allowed: create a new immutable `analysis_version + 1` from inputs within the
original evidence boundary and validate it against the prior analysis.

## Anti-hindsight requirements

1. Orchestration sees only approved preparation inputs.
2. Evidence later than the eligible evaluation boundary is forbidden.
3. Timeline versions and entries beyond the approved source boundary are
   forbidden.
4. Outcome information is forbidden.
5. Historical pattern matching is forbidden during creation.
6. Learning feedback is forbidden during creation.
7. Earlier artifacts and completed analyses are immutable.
8. A correction cannot expand the prior evaluated evidence boundary.

## Failure model

Future orchestration uses exactly these initial categories:

- `INVALID_IDENTITY`: required identity material is absent, ambiguous, or
  inconsistent;
- `DUPLICATE_REFERENCE`: an owned ID or reference is duplicated;
- `VERSION_CONFLICT`: version declarations disagree or revision order is
  invalid;
- `CAPABILITY_CONFLICT`: requested outputs exceed declared capabilities;
- `ASSEMBLY_REJECTION`: the approved assembler rejects the complete input;
- `INVALID_INPUT`: primitive shape, timestamp, ordering, or contract validation
  fails before a more specific category applies.

A failure MUST preserve category, lifecycle stage, concise reason, relevant
validation name, and versions. It MUST create no partial analysis and MUST NOT
alter any previous analysis. A failed attempt MAY emit an immutable audit trace
only.

## Determinism and validation acceptance criteria

A future implementation is acceptable only when:

1. identical normalized identity material produces identical canonical bytes
   and IDs;
2. changed expectation/evaluation identity produces a new `gap_id`;
3. changed `analysis_version` alone preserves `gap_id`;
4. changed orchestration context can change `trace_id` without changing
   `gap_id`;
5. no ID depends on UUID randomness, current time, host, environment, locale,
   network, or database state;
6. duplicate caller-owned IDs fail without repair;
7. orchestration invokes assembly at most once and returns no partial analysis;
8. all inputs remain unchanged;
9. anti-hindsight and revision boundaries remain enforced;
10. no provider, Telegram, database, persistence, production, learning, or
    Outcome dependency exists in the orchestration domain.

## Alternatives

- Assembler-generated IDs: rejected because construction and identity become
  coupled.
- Random UUIDs: rejected because semantic reconstruction is not reproducible.
- Database-generated IDs: rejected because identity gains persistence and
  environment dependencies.
- Orchestrator-owned deterministic identity: selected because it preserves
  separation, reproducibility, and append-only lineage.

## Future phases

- Step 7F defines evidence preparation.
- Step 7G defines Root Cause Candidate generation.
- Step 7H defines classification and metrics.
- Step 7I defines Memory/Learning consumption.

This specification does not implement or authorize those phases.

## Verification for Step 7E

```bash
git diff --check
git diff --stat
git diff --name-status
git status --short
```

The Step 7E branch must add only the ADR, this specification, and the report.
No Python/runtime, production, Telegram, Hostinger, persistence, learning, or
Outcome Analysis file may change.
