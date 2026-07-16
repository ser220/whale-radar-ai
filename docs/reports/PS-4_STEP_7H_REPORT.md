# PS-4 Step 7H Classification and Metrics Architecture Report

## Summary

This documentation-only task defines independent read-only boundaries for
Classification and Metrics consumers after `RootCauseCandidate` mapping.
Classification categorizes an already represented Reality Gap. Metrics describe
its measurable, observable, and explainable properties. Neither owns or creates
causal explanation.

## Documents

- [ADR](../architecture/adr/ADR-PS-4-classification-metrics-boundary.md)
- [Specification](../specs/PS-4-classification-metrics-boundary.md)
- this implementation report

## Classification boundary

Allowed inputs are immutable RootCauseCandidate lineage, Reality Gap context,
approved evidence references, and an approved policy version. The conceptual
`RealityGapClassification` preserves classification identity/policy, analysis
reference, ordered dimensions/categories, aware UTC timestamp, trace reference,
and immutable metadata.

The layer preserves existing `MARKET`, `INTELLIGENCE`, `OBSERVABILITY`, and
`EXPLANATION` dimensions and may combine them under a versioned policy. It does
not generate explanations, candidates, trees, metrics, severity, confidence,
or ranks.

## Metrics boundary

The conceptual `RealityGapMetricSet` preserves metric-set identity/policy,
ordered input references and metric results, aware UTC timestamp, trace
reference, and immutable metadata. Approved policies may measure availability,
coverage, observability, explanation completeness, and evidence-quality
indicators.

Missing, stale, unsupported, and failed measurements remain distinct from a
measured zero. Metrics make no truth, causal, certainty, severity, confidence,
ranking, or trading claim.

## Independence and ownership

Classification and Metrics own separate policies, outputs, versions, traces,
and failures. They do not consume each other's result. Explanation remains
owned by Candidate/RootCause layers. Evidence Preparation, Projection, Mapping,
Tree, and Assembly ownership remain unchanged.

## Trace and failures

Conceptual `ClassificationTrace` and `MetricTrace` expose exact input/policy and
produced-record references, validation facts, and warnings without hidden
reasoning. Typed failures produce no partial result.

Classification failures: `INVALID_INPUT_REFERENCE`, `POLICY_MISMATCH`,
`UNSUPPORTED_DIMENSION`, `VERSION_CONFLICT`.

Metrics failures: `INVALID_INPUT_REFERENCE`, `UNSUPPORTED_METRIC`,
`POLICY_MISMATCH`, `VERSION_CONFLICT`.

## Anti-hindsight and versioning

Consumers bind to exact historical input/policy versions and a caller-supplied
UTC boundary. Later Timeline entries, outcomes, future evidence, learning, and
current defaults substituted for historical policy are forbidden. Input,
analysis, classification-policy/result/trace, and metric-policy/set/trace
versions evolve independently. Changes create new immutable records.

## Alternatives

- Classification inside Explanation Layer: rejected because categorization and
  causal explanation would be coupled.
- Metrics inside Assembly: rejected because construction and measurement would
  be coupled.
- Independent read-only consumers: selected to preserve ownership, provenance,
  deterministic versioning, and optional capability boundaries.

## Repository impact

Only the Step 7H ADR, specification, and report are added. There is no runtime
classification or metric consumer, algorithm, formula, score, ranking,
confidence, severity, persistence, learning, Outcome Analysis, production,
Telegram, Hostinger, Candidate, Projection, Mapping, Evidence Preparation,
Reality Gap, Assembly, or dependency change.

## Open questions

- What canonical category vocabulary belongs to classification policy v1?
- What immutable per-metric availability/value contract should metric policy
  v1 use?
- What ID encoding and collision policy should classification, metric-set, and
  trace records adopt?
- Which existing RealityGapAnalysis optional fields should consume future
  metric records, if any, without duplicating ownership?
- Should Assembly attach full records or only stable references in a future
  separately reviewed contract change?

## Recommended next step

Submit this design for Architecture Review. Do not implement Step 7H contracts
or consumers until separately approved.
