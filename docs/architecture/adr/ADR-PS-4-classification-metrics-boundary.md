# ADR: PS-4 Classification and Metrics Consumer Boundary

## Status

Proposed; awaiting Architecture Review.

## Context

Whale Radar AI now preserves an immutable reasoning chain from prepared
evidence through `CandidateHypothesis`, `CandidateProjection`, and mapped
`RootCauseCandidate` records. The next architecture boundary must describe how
an already-formed Reality Gap is categorized and measured without moving
causal explanation, evidence ownership, or candidate lifecycle into a new
engine.

The existing Reality Gap contracts preserve the dimensions `MARKET`,
`INTELLIGENCE`, `OBSERVABILITY`, and `EXPLANATION`, policy/version provenance,
decision trace data, and capability-gated optional metrics. They do not define
independent runtime classification or metric consumers. Adding such consumers
inside Explanation, Mapping, or Assembly would blur ownership and permit
construction code to reinterpret historical facts.

## Decision

Define two independent, immutable, read-only consumer boundaries:

```text
Evidence
   |
   v
CandidateHypothesis
   |
   v
CandidateProjection
   |
   v
RootCauseCandidate
   |
   +--------------------+
   |                    |
   v                    v
Classification       Metrics
   |                    |
   +---------+----------+
             |
             v
      RealityGapAnalysis
```

Classification answers **what type of Reality Gap is represented**. Metrics
answer **how measurable, observable, and explainable that gap is**. Neither
answers why the situation occurred. Candidate and RootCause layers remain the
owners of explanation.

The two consumers are independent. A classification result cannot imply a
metric value, and a metric result cannot create or alter a classification.
They may consume the same approved historical references under independently
versioned policies.

This task defines architecture only. It does not add contracts or runtime
consumers.

## Classification ownership

The Classification Layer owns:

- classification policy and policy version;
- immutable classification result;
- classification record version;
- structured classification trace.

It does not own candidates, causal explanations, evidence, projections,
mappings, tree generation, metrics, outcomes, or learning. It cannot mutate or
replace any input record.

Allowed inputs are existing `RootCauseCandidate` snapshots, an immutable
Reality Gap context/reference, exact approved evidence references, and an
approved classification-policy version. Later Timeline entries, outcomes,
learning feedback, future evidence, implicit provider assumptions, and current
defaults substituted for historical policy are forbidden.

## Conceptual `RealityGapClassification`

The future immutable record contains:

- `classification_id`;
- `classification_policy_version`;
- `analysis_reference`;
- ordered `dimensions`;
- ordered `categories`;
- caller-supplied aware UTC `created_at`;
- `trace_reference`;
- deeply immutable primitive metadata.

It must be deterministic, versioned, serializable, round-trippable, and
lineage preserving. Dimensions preserve the existing vocabulary:
`MARKET`, `INTELLIGENCE`, `OBSERVABILITY`, and `EXPLANATION`. Multiple
dimensions may coexist. Categories are policy-defined labels whose vocabulary
and ordering are part of the classification-policy version.

Classification groups an already represented gap. It does not generate a
candidate, assign causal truth, calculate severity, rank causes, or create a
causal explanation.

## Metrics ownership

The Metrics Layer owns:

- metric policy and formula definitions;
- metric-policy version;
- immutable metric result;
- metric-set version;
- structured metric trace.

It does not own explanation decisions, candidate lifecycle, Evidence
Preparation, classification, tree structure, assembly, outcomes, or learning.
It cannot mutate or replace inputs.

Metrics may describe availability, coverage, observability, explanation
completeness, and evidence-quality indicators. A metric must identify its
definition, units/domain, required inputs, missing-input behavior, and policy
version. Metrics must not claim truth, causality, certainty, severity, trade
quality, or actionability.

## Conceptual `RealityGapMetricSet`

The future immutable record contains:

- `metric_set_id`;
- `metric_policy_version`;
- ordered `input_references`;
- an ordered immutable `metrics` collection;
- caller-supplied aware UTC `created_at`;
- `trace_reference`;
- deeply immutable primitive metadata.

It must be deterministic, versioned, serializable, round-trippable, and
lineage preserving. Missing, stale, unsupported, or failed measurement is
explicit; it is not silently converted to zero. Metric formulas and canonical
ordering belong to the metric-policy version.

## Independent relationship

Classification and Metrics may run in either order or in parallel when their
inputs are available. Neither consumes the other's output unless a future ADR
defines a new derived consumer. In particular, an `OBSERVABILITY` classification
does not automatically mean a low metric, and a low coverage metric does not
automatically add the `OBSERVABILITY` dimension.

Assembly may receive already-produced records and validate their references,
versions, and capabilities. It must not calculate them.

## Trace model

Future `ClassificationTrace` and `MetricTrace` records contain structured
facts only:

- trace identity/version;
- exact input identities and versions;
- policy identity/version;
- produced record identity/version;
- ordered validation facts;
- ordered warnings;
- caller-supplied aware UTC timestamp;
- immutable primitive metadata.

Trace records expose reproducible inputs and policy selection. They contain no
hidden chain-of-thought, provider clients, mutable objects, future facts, or
post-outcome interpretation.

## Failure boundary

Classification failures are:

- `INVALID_INPUT_REFERENCE`;
- `POLICY_MISMATCH`;
- `UNSUPPORTED_DIMENSION`;
- `VERSION_CONFLICT`.

Metric failures are:

- `INVALID_INPUT_REFERENCE`;
- `UNSUPPORTED_METRIC`;
- `POLICY_MISMATCH`;
- `VERSION_CONFLICT`.

A failure produces one immutable typed failure record and no partial
classification or metric set. Consumers do not repair, downgrade, or infer
missing inputs.

## Anti-hindsight

Each result is bound to the exact immutable input identities/versions and
policy version available at its caller-supplied creation boundary. Consumers
must reject later Timeline entries, market outcomes, future evidence, learning
feedback, or a newer policy masquerading as the historical policy. A policy
change creates a new immutable result; it never rewrites an old record.

## Versioning

The following versions evolve independently:

- source candidate, projection, mapping, and RootCauseCandidate lineage;
- Reality Gap analysis/context version;
- classification-policy and classification-record versions;
- metric-policy and metric-set versions;
- classification-trace and metric-trace versions.

Any changed input or policy creates a new immutable output identity/version.
Historical outputs remain readable and are never reinterpreted in place.

## Dependency boundary

Future consumers are pure domain services. They may depend on immutable local
contracts and Python standard-library primitives. They must not import or call
Telegram, databases, repositories, providers, exchange clients, networking,
production pipelines, deployment code, persistence, learning, or Outcome
Analysis.

## Alternatives considered

### A. Classification inside Explanation Layer

Rejected. It mixes causal explanation with categorization, allows category
policy to influence cause construction, and weakens independent versioning.

### B. Metrics inside Assembly

Rejected. It mixes construction/validation with measurement and makes
assembly results dependent on hidden formulas or unavailable inputs.

### C. Independent read-only consumers

Selected. It preserves ownership, supports independent policies and traces,
prevents implicit causal claims, and allows capabilities to remain explicit.

## Consequences

Positive consequences:

- explanation and measurement remain separate;
- policies and outputs are independently versioned and auditable;
- anti-hindsight and provenance can be enforced at both boundaries;
- classification and metrics can evolve without changing source contracts.

Trade-offs:

- callers must carry exact references and versions;
- two policies and two trace families must be maintained;
- Assembly requires explicit capability/version validation for optional
  outputs;
- no useful result is returned when a required reference or policy is invalid.

## Future implementation

After Architecture Review, a separate implementation task may add immutable
classification contracts, immutable metric contracts, and pure read-only
consumers. Learning, persistence, automatic causality, ranking, confidence,
severity, provider access, production integration, and Outcome Analysis remain
out of scope until separately approved.
