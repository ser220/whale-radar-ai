# PS-4 Projection to RootCauseCandidate Mapping Specification

## Objective

Define a deterministic immutable boundary that materializes an approved
`RootCauseCandidate` from an existing `CandidateProjection` plus explicit
Explanation Layer inputs, without implementing a runtime mapper or analytical
logic.

## Scope

This specification defines:

- layer ownership;
- conceptual request, mapping, and failure records;
- exact field mapping;
- identity and lineage rules;
- role/disposition handling;
- evidence and tree-placement validation boundaries;
- independent version behavior;
- anti-hindsight guarantees;
- future Step 7H consumption constraints.

## Out of scope

- runtime mapper or new Python contracts;
- CandidateProjection, RootCauseCandidate, Evidence Preparation, Assembler,
  orchestration, or RootCauseTree changes;
- candidate generation, classification, severity, metric, confidence, ranking,
  causal inference, or truth assignment;
- tree/edge/placement generation;
- persistence, learning, Outcome Analysis, providers, networking, production,
  Telegram, Hostinger, or deployment.

## Normative terminology

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` describe requirements for a future
separately reviewed implementation. This task adds documentation only.

## Core rule: projection alone is not a total mapping input

The real `CandidateProjection` contract supplies category, role, disposition,
lineage, contexts, and evidence/limitation refs. It does not supply target
`subject`, target `description`, stable hypothesis reference,
`independent_support_count`, rejection reason, or tree placement.

A mapper MUST NOT fabricate these fields or read them implicitly from arbitrary
metadata. A future request therefore MUST include the projection plus explicit
immutable descriptor, decision, placement, and historical evidence-catalog
snapshots. Mapping without those required inputs fails.

## Ownership

### Candidate Layer

Owns CandidateHypothesis and candidate ID/version.

### Projection Layer

Owns CandidateProjection and projection ID/version.

### Mapping Layer

Owns mapping ID/version, mapping policy, input/lineage validation,
deterministic materialization, and mapping failures. It owns no source or
explanation decision values.

### Explanation Layer

Owns descriptor text/reference, role, disposition, rejection reason,
independent-support declaration/provenance, and tree placement.

### Assembler

Owns final validation/construction of RealityGapAnalysis from already mapped
candidates and an already-created tree.

## Conceptual `RootCauseCandidateMappingRequest`

Required immutable fields:

- request ID and mapping-policy version;
- selected `CandidateProjection` snapshot/reference;
- `ExplanationDescriptorSnapshot`;
- `ExplanationDecisionSnapshot`;
- `TreePlacementSnapshot`;
- historical immutable evidence-catalog reference/view;
- caller-supplied aware UTC creation timestamp;
- primitive immutable metadata.

The request MUST preserve source object identity/version and cannot substitute
current defaults for historical values.

## Conceptual `ExplanationDescriptorSnapshot`

Fields:

- source candidate ID/version;
- `subject`;
- `description`;
- `hypothesis_reference`;
- descriptor-policy version;
- caller-supplied aware UTC timestamp;
- primitive immutable metadata.

All fields are explicit. Descriptor data is presentation/context material, not
a causal or classification decision.

## Conceptual `ExplanationDecisionSnapshot`

Fields:

- projection ID/version;
- role;
- disposition;
- decision reference;
- explicit `independent_support_count`;
- independent-support provenance reference;
- optional rejection reason;
- decision-policy version;
- caller-supplied aware UTC timestamp;
- primitive immutable metadata.

The mapping validates that role/disposition exactly match the selected
projection. It does not choose or transform them. Independent-support count is
an explicit input; the mapper does not infer evidence independence or calculate
the count.

In the current public enums, `UNRESOLVED` is a disposition. There is no
`UNRESOLVED` role. A request MUST use an existing non-rejected role with
unresolved disposition.

## Conceptual `TreePlacementSnapshot`

Fields:

- tree-context reference and tree version;
- target projection ID;
- optional parent projection ID;
- ordered child projection IDs;
- ordered alternative projection IDs;
- placement-policy version;
- caller-supplied aware UTC timestamp;
- primitive immutable metadata.

The snapshot is authored by Explanation Layer. The mapper validates/copies it;
it does not select placement or create a tree. Placement-neutral mapping uses
no parent, children, or alternatives.

## Conceptual `RootCauseCandidateMapping`

Fields:

- `mapping_id`;
- positive `mapping_version`;
- `mapping_policy_version`;
- source candidate ID/version;
- source projection ID/version;
- analysis-context ID;
- tree-context reference/version;
- target RootCauseCandidate ID;
- conceptual positive RootCauseCandidate version;
- request/descriptor/decision/placement snapshot references;
- immutable `RootCauseCandidate` output snapshot;
- ordered validation facts and warnings;
- caller-supplied aware UTC `created_at`;
- primitive immutable metadata.

It MUST be immutable, deterministically ordered, primitive-serializable,
round-trippable, and independent of host, runtime, database, UUID, current
clock, locale, network, and hash iteration order.

## Identity policy

- Candidate identity is source hypothesis ID/version.
- Projection identity is source representation ID/version.
- Mapping identity is one materialization lineage under one mapping context.
- RootCauseCandidate tree-facing identity is
  `RootCauseCandidate.candidate_id = CandidateProjection.projection_id`.
- Tree identity is external and preserved by context/version reference.

Conceptual mapping identity material, in fixed order:

1. mapping identity-policy version;
2. mapping namespace;
3. source projection ID;
4. analysis-context ID;
5. stable mapping-slot/context reference.

Digest/encoding is deferred. Candidate identity is preserved in mapping/target
metadata and is never replaced by the tree-facing identity.

## Exact field mapping

| RootCauseCandidate field | Mapping source |
| --- | --- |
| `candidate_id` | projection ID |
| `category` | projection category |
| `subject` | descriptor snapshot |
| `description` | descriptor snapshot |
| `role` | explicit decision; must equal projection role |
| `disposition` | explicit decision; must equal projection disposition |
| `confidence` | `None` |
| `temporal_precedence` | `None` |
| `direct_relevance` | `None` |
| `evidence_coverage` | `None` |
| `independent_support_count` | explicit decision input |
| `supporting_evidence_refs` | projection evidence snapshot |
| `contradicting_evidence_refs` | projection evidence snapshot |
| `parent_candidate_id` | placement snapshot |
| `child_candidate_ids` | placement snapshot |
| `limitations` | projection limitation snapshot |
| `alternative_candidate_ids` | placement snapshot |
| `rejection_reason` | explicit decision input |
| `policy_version` | mapping-policy version |
| `metadata` | primitive candidate/projection/mapping/target lineage |

`hypothesis_reference` is preserved in primitive target/mapping provenance
because the current RootCauseCandidate has no dedicated field.

## Required target metadata lineage

At minimum, target metadata MUST preserve:

- source candidate ID/version;
- source projection ID/version;
- mapping ID/version and mapping-policy version;
- conceptual RootCauseCandidate version;
- analysis and tree-context references/versions;
- hypothesis reference;
- descriptor, decision, and placement snapshot references.

Metadata MUST NOT contain source objects, secrets, provider payloads, clients,
or mutable runtime state.

## Role and disposition validation

There is no CandidateStatus mapping. Mapping MUST validate only explicit
Explanation Layer decisions already reflected by the projection:

- role and disposition equal projection values;
- rejected disposition requires rejected-candidate role and rejection reason;
- rejected-candidate role requires rejected disposition;
- non-rejected disposition forbids rejection reason;
- unresolved is a disposition, not a role.

Failure is `INVALID_EXPLANATION_DECISION`; the mapper does not repair values.

## Evidence requirements

Mapping MUST copy exactly the projection's supporting, contradicting, and
limitation references. It MUST validate each evidence ID against the historical
immutable catalog view and preserve eligibility. It MUST NOT add, remove,
replace, upgrade, downgrade, or reinterpret evidence.

Snapshot mismatch or unresolved reference is `INVALID_EVIDENCE_REFERENCE`.
The catalog remains owned by Evidence Preparation; mapping is read-only.

## Tree relationship

Mapping does not create RootCauseTree, roots, edges, or placement. It validates
an explicit placement snapshot:

- all placement refs use projection IDs;
- every ref resolves inside the same tree context/version;
- no self-reference or duplicate reference exists;
- parent/child/alternative relationships do not conflict with the supplied
  context snapshot;
- later RootCauseTree validation remains authoritative for complete structure.

## Versioning and lineage

Five versions are independent:

1. candidate version;
2. projection version;
3. mapping-policy/mapping version;
4. conceptual RootCauseCandidate version;
5. tree version.

Mapping-policy or mapped-input changes create a new mapping version and new
immutable target snapshot. Old mappings remain readable. Source changes never
mutate mappings. Tree changes never mutate candidate/projection lineage.

The current target contract has no explicit version field. Until a separately
approved change, conceptual RootCauseCandidate version lives in the mapping
record and target primitive metadata. Mapping MUST reject version regressions,
skips outside approved policy, and metadata disagreement.

## Deterministic behavior

A future mapper MUST:

- accept immutable inputs only;
- preserve canonical evidence order;
- canonicalize placement refs by approved policy;
- emit target fields in stable contract order;
- serialize mapping and output deterministically;
- produce byte-identical canonical serialization for equal inputs;
- never use current time or random identity implicitly.

## Anti-hindsight

Mapping may use only the selected existing projection version, exact evidence
snapshot/catalog view, explicit descriptor/decision/placement snapshots, and
historical mapping policy. Future evidence, later Timeline/projection data,
outcomes, learning feedback, historical similarity, and automatic
reinterpretation are forbidden.

## Failure model

Conceptual immutable `MappingFailure` values:

- `UNKNOWN_PROJECTION`;
- `VERSION_MISMATCH`;
- `INVALID_LINEAGE`;
- `INVALID_EVIDENCE_REFERENCE`;
- `POLICY_CONFLICT`;
- `INVALID_EXPLANATION_DECISION`.

Failure records request/mapping reference, source IDs/versions, policy version,
stage, and concise reason. Failure produces no partial mapping or target and
mutates no previous object.

## Acceptance criteria for a future implementation

1. Mapping with `CandidateProjection` alone is rejected as incomplete.
2. Every target field has an explicit source; no hidden default is used.
3. Source candidate/projection identity and versions remain traceable.
4. Target candidate ID equals projection ID without overwriting source lineage.
5. Role/disposition are validated, never selected or converted.
6. Metric/confidence/severity fields remain `None` in this boundary.
7. Independent-support count is explicit and not calculated.
8. Evidence refs exactly match projection and historical catalog eligibility.
9. Placement is explicit and no tree is generated.
10. Equal immutable inputs create byte-identical mapping/target serialization.
11. Previous mappings/targets remain unchanged and readable.
12. No provider, persistence, learning, production, Telegram, Hostinger, or
    Outcome Analysis dependency exists.

## Alternatives

### Projection equals RootCauseCandidate

Rejected because projection and explanation/tree identity would collapse and
missing target fields would leak into projection.

### Assembler creates RootCauseCandidate

Rejected because pure construction would gain explanation and mapping policy.

### Dedicated mapping boundary

Selected because ownership, explicit inputs, evidence, and lineage remain
auditable.

## Future boundary

After separately reviewed immutable request/result/failure contracts and a pure
mapper exist, Step 7H may consume mapped RootCauseCandidates, projection
lineage, and evidence references. It must not create candidates, modify
projections/evidence, or rewrite mapping history.

## Verification for this task

```bash
git diff --check
git diff --stat
git diff --name-status
git status --short
```

Only this specification, its ADR, and its report may be added. No runtime,
contract, classification, metric, confidence, ranking, severity, tree,
persistence, learning, production, Telegram, Hostinger, or Outcome Analysis
file may change.
