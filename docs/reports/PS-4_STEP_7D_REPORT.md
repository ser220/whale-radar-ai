# PS-4 Step 7D Report — Deterministic Reality Gap Assembly

## Assembler responsibility

Step 7D introduces an isolated deterministic assembly boundary for
already-classified and already-prepared Reality Gap inputs. It validates source
identity, reference integrity, deterministic ordering, candidate dispositions,
Root Cause Tree structure, Decision Trace consistency, capability/output
consistency, provenance and version agreement. It constructs exactly one
immutable `RealityGapAnalysis` and verifies its canonical serialization.

## Explicit non-responsibilities

The assembler does not extract Timeline evidence, generate stable IDs or Root
Cause Candidates, classify a Reality Gap, judge evidence relevance, or
calculate Surprise, Knowledge Gap, Explanation Confidence, residual, severity,
or any other metric. It has no provider, networking, Telegram, database,
repository, production pipeline, Decision Engine, Trade Readiness,
MarketStateEngine, Expert, persistence, learning, or Outcome Analysis behavior.

## Contracts created

- `RealityGapAssemblyInput`: frozen input contract containing primitive
  snapshots and approved Reality Gap contract objects only;
- `RealityGapAssemblyResult`: frozen result with the assembled analysis,
  eligibility/disposition groups, non-analytical warnings, and an auditable
  assembly trace;
- `RealityGapAssembler`: stateless assembly and revision-assembly service.

All contracts normalize aware timestamps to UTC, deeply freeze mappings and
collections, reject invalid score values, and round-trip deterministically.

## Complete evidence preservation decision

The assembly input uses one complete evidence collection. Eligible and
ineligible evidence are both preserved in
`RealityGapAnalysis.supporting_evidence`; eligibility remains authoritative on
each reference. This retains rejected evidence required for auditability.

Accepted and partially supported candidates require at least one eligible
supporting reference, and all their supporting references must be eligible.
Contradicting evidence may retain either eligibility. Rejected candidates keep
their declared references and rejection reason. An unresolved candidate with
no eligible supporting evidence must declare a limitation. The assembler never
determines relevance.

## Candidate disposition grouping

Candidate groups are derived only from supplied immutable dispositions:

- `ACCEPTED` and `PARTIALLY_SUPPORTED` become the accepted group;
- `REJECTED` becomes the rejected group;
- `UNRESOLVED` becomes the unresolved group.

Groups are sorted by candidate ID. No supplied candidate is reclassified.

## Capability and optional-output consistency

Unsupported market, intelligence, observability, explanation, candidate, and
tree capabilities forbid those representations in the assembled record.
Unsupported optional metrics and severity must remain `None`. Populated
optional metrics require `metric_version`; a tree requires `tree_version`; a
populated severity requires a provenance severity-policy version. A false
capability describes the engine version, not the real-world absence of a gap.

## Decision Trace consistency

Considered and rejected evidence references must resolve and remain disjoint.
Ineligible evidence cannot be considered. Supplied trace severity and metric
outputs must agree with matching top-level outputs, and overlapping policy
version names must agree with provenance/top-level versions. Missing values are
not calculated or filled.

## Deterministic ordering and reproducibility

Evidence is ordered by `evidence_id`; candidates by `candidate_id`;
observability records by gap-type value and subject; disposition groups by
candidate ID. Caller event order and Timeline lineage order are preserved and
duplicates rejected by contracts. Tree edge ordering remains owned by the
approved tree contract. Warnings follow a fixed policy order with lexical
tie-breaking.

The assembler performs a `to_dict()`/`from_dict()` equality check and compares
canonical UTF-8 JSON bytes. It reads no clock, randomness, host, environment,
locale, network, or provider state and generates no identifier.

## Revision assembly

`assemble_revision(previous, assembly_input)` performs normal assembly and then
calls `validate_analysis_revision`. It requires the caller's version and reason,
preserves identity and evidence boundaries, rejects version jumps and later
Timeline evidence, and never mutates or merges revisions.

## Warnings and assembly trace

Warnings report only contract limitations such as absent eligible evidence,
supported-but-omitted candidates/tree, intentionally unavailable optional
metrics, observability-only evidence, omitted explanation gap, or retained
ineligible audit evidence. Warnings never modify classification.

The assembly trace records concise validation milestones and counts. It contains
no hidden reasoning or analytical explanation.

## Tests and verification

Focused standard-library `unittest` coverage includes immutable input/result
round trips, non-mutation, caller-owned IDs, evidence/candidate ordering,
eligible/ineligible preservation, duplicate/reference rejection, candidate
rules and grouping, tree validation, capability/output constraints, Decision
Trace agreement, deterministic warnings/trace/JSON, valid revisions,
anti-hindsight boundaries, and dependency/analytical-method audits. Approved
Reality Gap, Expectation/Evaluation, Timeline/Evolution/Identity, Early Bird,
intelligence, and safe local smoke suites are run before commit.

## Production impact

None. Approved Reality Gap model files and all production, Telegram, Hostinger,
database, requirements, deployment, persistence, learning, and Outcome Analysis
paths remain unchanged. No third-party dependency is added.

## Open questions

- Which future orchestration component owns deterministic gap, evidence,
  candidate, tree, and trace ID generation?
- Should a future orchestration contract require every ineligible evidence ID
  to appear in the Decision Trace rejected group, rather than retaining the
  current explicit warning?
- Which reviewed policy artifact will define names for trace metric and policy
  output keys across engine versions?

## Recommended Step 7E

Define the orchestration and deterministic stable-ID policy that prepares
primitive assembly inputs. Keep evidence extraction, classification, metric
calculation, persistence, and production integration out of scope unless each
is separately designed and approved.
