# ADR: PS-4 Reality Gap Orchestration and Stable Identity Policy

## Status

Proposed; awaiting Architecture Review.

## Context

PS-4 Steps 7A through 7D established the Reality Gap architecture, immutable
contracts, validation rules, and deterministic assembly boundary. The current
flow begins only after interpretation has already happened:

```text
Prepared Inputs
      |
      v
RealityGapAssembler
      |
      v
Immutable RealityGapAnalysis
```

The assembler deliberately does not discover evidence, create candidates,
classify a gap, calculate metrics, or invent identifiers. A boundary is now
required to coordinate artifact identity, lifecycle order, version lineage,
validation, and assembly without collapsing those responsibilities back into
one component.

Without an explicit policy, callers could use random or host-dependent IDs,
silently change the meaning of version fields, re-create different lineages
for equivalent inputs, mutate earlier artifacts, or give the assembler
responsibilities that its approved contract excludes.

## Decision

Adopt a future conceptual `RealityGapOrchestrator` between preparation and
assembly. Reality Gap creation is divided into three non-overlapping roles:

1. **Preparation** creates already-approved primitive snapshots and evidence
   references. It owns evidence identity but performs no orchestration.
2. **Orchestration** owns deterministic lineage and trace identity, validates
   lifecycle order and versions, constructs `RealityGapAssemblyInput`, invokes
   the assembler, and returns the immutable analysis plus structured
   orchestration facts.
3. **Assembly** validates the prepared contract graph and creates exactly one
   immutable `RealityGapAnalysis`. It creates no identifiers.

No component may own all three responsibilities.

## Canonical lifecycle

```text
Observation
    |
    v
Expectation
    |
    v
Evaluation
    |
    v
Reality Gap Preparation
    |
    v
Reality Gap Orchestration
    |
    v
Reality Gap Assembly
    |
    v
Immutable RealityGapAnalysis
    |
    v
Future Learning Consumption
```

Each stage owns only the artifacts it creates. A later stage may reference an
earlier immutable artifact but may not mutate or reinterpret it in place.
Analysis creation is append-only. A correction produces
`analysis_version + 1`; it never overwrites an earlier version.

Future learning is a downstream consumer and cannot feed information back into
the creation of the historical analysis being learned from.

## Ownership decision

| Identity | Owner | Meaning |
|---|---|---|
| `gap_id` | Reality Gap Orchestrator | One immutable analysis lineage |
| `trace_id` | Reality Gap Orchestrator | One deterministic orchestration/assembly path |
| `evidence_id` | Preparation layer | One prepared immutable evidence reference |
| `candidate_id` | Future Candidate layer | One immutable root-cause hypothesis |
| `tree_id` | Future Explanation/Tree layer | One immutable explanatory structure |
| `RealityGapAnalysis` construction | Assembler | Validated aggregate creation only |

The orchestrator validates IDs owned elsewhere but does not invent evidence,
candidates, or trees. The assembler validates all supplied IDs and references
but creates none.

## Stable identity policy

Identifiers must be deterministic, reproducible, and derived from a documented
ordered identity material. They must be independent of process identity, host,
environment, locale, random UUIDs, database sequence state, and the current
timestamp. The policy is versioned so an identity algorithm can evolve without
silently changing historical meaning.

Conceptually, the owner:

1. selects the fields defined by the identity policy;
2. normalizes text and version values using a documented canonical form;
3. serializes fields in fixed order with explicit boundaries;
4. applies the identity algorithm named by the policy version;
5. prefixes or namespaces the result by artifact kind.

Step 7E defines material and ownership only. It selects no hash, encoding,
length, or cryptographic implementation.

### Gap identity

`gap_id` identifies one Reality Gap lineage. Its conceptual input material is:

- identity-policy version and analysis-lineage namespace;
- `expectation_id`;
- `evaluation_id`;
- `timeline_id`;
- normalized uppercase asset.

The same normalized semantic material produces the same `gap_id`. Changing
expectation or evaluation identity creates a different lineage. Changing
`analysis_version` does not change `gap_id`.

### Trace identity

`trace_id` identifies one deterministic orchestration/assembly path, not the
market situation. Its conceptual material is:

- `gap_id`;
- trace-policy version;
- orchestration-context version.

A materially different orchestration policy may produce a different trace
identity while the gap lineage remains unchanged.

### Evidence, candidate, and tree identity

The preparation layer owns `evidence_id`. The same evidence reference reused in
a later analysis revision retains its identity. Duplicate IDs are rejected;
the orchestrator and assembler never modify them.

The future Candidate layer owns `candidate_id`. Orchestration and assembly
validate only. There is no automatic candidate creation or candidate merging.

The future Explanation/Tree layer owns `tree_id`. A tree ID identifies one
immutable explanatory structure. A changed structure produces a new tree
identity or version according to the future tree policy; the previous tree
remains immutable.

## Version ownership

- `gap_id` identifies the lineage and is stable across revisions.
- `analysis_version` is the append-only immutable revision number.
- policy versions identify the rules used to create or validate artifacts.
- `trace_version` identifies the audit contract format.
- `taxonomy_version` identifies category meanings.
- `tree_version` identifies the explanatory structure format/version.
- orchestration and identity-policy versions identify coordination and ID
  semantics.

No version may silently change meaning. A changed version that affects the
record requires a new analysis revision. Historical analyses and their version
interpretations remain readable.

## Creation boundary

Before `RealityGapAnalysis` creation, orchestration may prepare primitive data,
create orchestrator-owned IDs, validate caller-owned IDs and references,
validate lifecycle order, capabilities, and versions, and construct an
assembly input.

After creation it is forbidden to change evidence, candidates, classification,
metrics, severity, trace, provenance, capabilities, or source snapshots. The
only correction path is a new `analysis_version` validated against the prior
immutable record.

## Conceptual orchestration contracts

`RealityGapOrchestrationRequest` contains the prepared assembly material,
identity namespace, identity/policy versions, and orchestration version. It
contains no provider clients, mutable runtime artifacts, outcome data, or
learning state.

`RealityGapOrchestrationResult` contains the immutable analysis, generated
orchestrator-owned IDs, structured orchestration trace, and validation summary.

`RealityGapOrchestrationTrace` contains orchestration identity/version,
lifecycle stage, identity decisions, validation results, assembly invocation
result, supplied timestamps, and warnings. It records concise structured facts
only and contains no private reasoning or hidden chain of thought.

These are architecture contracts. Step 7E adds no runtime models.

## Anti-hindsight decision

The orchestrator may see only approved preparation inputs within the original
evaluation boundary. It cannot access future evidence, later Timeline versions,
outcome information, historical pattern matching, or learning feedback during
creation. It may not mutate any earlier artifact or completed analysis.

## Failure handling

Use the following future failure categories:

- `INVALID_IDENTITY`
- `DUPLICATE_REFERENCE`
- `VERSION_CONFLICT`
- `CAPABILITY_CONFLICT`
- `ASSEMBLY_REJECTION`
- `INVALID_INPUT`

A failure preserves a structured category and concise reason. It creates no
partial `RealityGapAnalysis` and cannot alter previous analyses. A failed
attempt may produce an immutable audit trace only; that trace is not an
analysis and contains no analytical conclusion.

## Alternatives considered

### A. Assembler creates all identifiers

Rejected. This mixes identity/lifecycle ownership with aggregate construction,
weakens the approved assembly boundary, and makes the assembler stateful.

### B. Random UUID identifiers

Rejected. Random values are not reproducible from identical semantic inputs and
make deterministic reconstruction and comparison harder.

### C. Database-generated identifiers

Rejected. Database sequences introduce persistence, ordering, availability,
and environment dependencies into a pure intelligence-domain boundary.

### D. Orchestrator-owned deterministic identity

Accepted. It keeps coordination separate from preparation and assembly,
supports reproducible lineage, and allows validation without persistence.

## Consequences

### Positive

- one stable lineage exists across immutable analysis revisions;
- responsibilities remain isolated and independently testable;
- identical normalized identity material can be reconstructed deterministically;
- assembly remains pure and unaware of ID-generation mechanisms;
- failures cannot create partial analyses;
- anti-hindsight and append-only rules have one coordination owner;
- future persistence can store identities without owning their meaning.

### Negative and trade-offs

- a future canonicalization and identity algorithm must be specified and
  versioned before runtime orchestration;
- orchestration adds another explicit boundary and validation step;
- cross-version ID migration requires careful compatibility policy;
- callers must provide all prepared inputs and owner-generated IDs rather than
  relying on convenient implicit behavior.

## Future phase boundary

- Step 7F: evidence preparation pipeline;
- Step 7G: candidate generation;
- Step 7H: gap classification and metrics;
- Step 7I: Memory/Learning consumption.

This ADR does not implement or authorize any of those phases.
