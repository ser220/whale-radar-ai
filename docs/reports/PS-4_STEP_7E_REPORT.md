# PS-4 Step 7E Report — Reality Gap Orchestration & Stable Identity Policy

## Summary

Step 7E defines the documentation-only boundary that will coordinate prepared
Reality Gap inputs and the approved deterministic assembler. It assigns stable
identity ownership, fixes lifecycle/creation order, preserves immutable
analysis lineage, defines anti-mutation and anti-hindsight rules, and documents
future conceptual orchestration contracts and failure handling.

## Orchestration boundary

Reality Gap creation is split into three responsibilities:

```text
Preparation -> Orchestration -> Assembly -> Immutable RealityGapAnalysis
```

Preparation creates approved primitive inputs and evidence references.
Orchestration coordinates identity, lifecycle, versions, validation, and one
assembly invocation. Assembly creates the immutable aggregate. No component
owns all three responsibilities.

The future orchestrator has no evidence discovery, market interpretation,
candidate generation, gap classification, metric/severity calculation,
learning, persistence, notifications, or production-decision role.

## Identity ownership

- Orchestrator: `gap_id`, `trace_id`.
- Preparation layer: `evidence_id`.
- Future Candidate layer: `candidate_id`.
- Future Explanation/Tree layer: `tree_id`.
- Assembler: `RealityGapAnalysis` construction only.

The orchestrator validates external-owner IDs; the assembler validates and
preserves all IDs. Neither silently rewrites them.

## Stable ID policy

IDs are derived from documented, fixed-order, normalized semantic material
under a versioned identity policy. They are independent of current timestamps,
random UUIDs, database sequences, process, host, environment, locale, and
network state. Step 7E defines material and ownership but intentionally does
not select a hash, encoding, cryptographic primitive, or ID length.

`gap_id` uses the identity-policy version, lineage namespace,
expectation/evaluation/Timeline identity, and uppercase asset. It remains stable
across `analysis_version` revisions.

`trace_id` uses `gap_id`, trace-policy version, and orchestration-context
version. It identifies an orchestration/assembly path rather than a market
situation.

## Lifecycle and version lineage

The canonical lifecycle is Observation, Expectation, Evaluation, Reality Gap
Preparation, Orchestration, Assembly, immutable analysis, and future downstream
learning consumption. Every stage owns only its artifacts; later stages cannot
mutate earlier ones.

Analysis creation is append-only. A correction produces exactly the next
analysis version while retaining lineage identity and the original eligible
evidence boundary. Policy, trace, taxonomy, tree, orchestration, and identity
versions retain explicit meanings and cannot silently change.

## Creation boundary

Before construction, orchestration may prepare primitive values, create its own
deterministic IDs, validate references/capabilities/versions, and construct an
assembly input. After construction, evidence, candidates, classification,
metrics, severity, trace, provenance, capabilities, and source snapshots are
immutable. Only a validated new revision is allowed.

## Conceptual contracts

- `RealityGapOrchestrationRequest`: prepared material, namespace, identity and
  policy versions, orchestration version, bounded timestamps, and primitive
  metadata.
- `RealityGapOrchestrationResult`: immutable analysis, orchestrator-generated
  IDs, orchestration trace, and validation summary.
- `RealityGapOrchestrationTrace`: structured identity decisions, validation
  results, lifecycle stage, assembly status, timestamps, warnings, and optional
  failure facts—never hidden reasoning.

No runtime class was added.

## Failure handling

Initial categories are `INVALID_IDENTITY`, `DUPLICATE_REFERENCE`,
`VERSION_CONFLICT`, `CAPABILITY_CONFLICT`, `ASSEMBLY_REJECTION`, and
`INVALID_INPUT`. Failure preserves a concise structured reason and may emit an
audit trace, but creates no partial analysis and cannot alter prior analyses.

## Anti-hindsight

Orchestration may access only approved preparation inputs inside the original
evaluation and Timeline boundary. Future evidence, outcome facts, historical
pattern matching, learning feedback, boundary expansion, and mutation are
forbidden during creation.

## Alternatives

- assembler-created IDs: rejected because identity and construction mix;
- random UUIDs: rejected because reproduction is impossible;
- database IDs: rejected because identity gains persistence/environment state;
- orchestrator-owned deterministic identity: selected.

## Future phase boundary

- Step 7F: evidence preparation pipeline;
- Step 7G: candidate generation;
- Step 7H: classification and metrics;
- Step 7I: Memory/Learning consumption.

None is implemented or authorized by Step 7E.

## Production impact

None. Step 7E adds documentation only. No Python/runtime contract, production
pipeline, Telegram, Hostinger, persistence, learning, Outcome Analysis,
dependency, deployment, or existing Reality Gap contract changes.

## Open questions

- Which canonical text normalization and field-boundary encoding should the
  future identity policy select?
- Which deterministic digest/encoding and collision-handling policy should be
  adopted after security and interoperability review?
- Does `trace_id` remain stable across a pure analysis revision when trace and
  orchestration context versions are unchanged, or should the future trace
  material include `analysis_version`?
- Which component will own durable orchestration audit traces once persistence
  is separately designed?

## Recommended Step 7F

Design the evidence preparation pipeline and its immutable input/output
contracts, including evidence ID material, eligibility boundary, duplicate
semantics, and provenance. Do not yet implement candidate generation,
classification, metrics, persistence, learning, or production integration.
