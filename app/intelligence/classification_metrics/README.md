# Classification and Metrics contracts

This package defines immutable, deterministic output records for future
Reality Gap Classification and Metrics consumers.

Public contracts:

- `RealityGapClassification`
- `RealityGapMetricSet`
- `RealityGapMetricValue`
- `MetricAvailability`
- categorized validation errors and failure enums

The package also exposes pure read-only consumers:

- `classify_reality_gap()` applies an explicit, versioned mapping supplied by
  `ClassificationConsumerPolicy`;
- `measure_reality_gap()` calculates only the approved transparent Phase 1
  indicators `reference_coverage` and `evidence_availability_ratio`.

Both consumers require a caller-supplied immutable historical context, use no
clock, UUID, I/O, database, provider, or global state, and preserve a
deterministic trace reference plus structured reproducibility facts. They do
not create causes, predictions, confidence, severity, rankings, or trading
advice. Metric availability is explicit: a missing, stale, unsupported,
unavailable, or errored metric has no measured value and is never serialized
as zero.

Runtime dependencies are limited to the Python standard library and the
existing `RealityGapDimension` domain enum. Telegram, providers, databases,
repositories, networking, pipelines, Candidate, Projection, Mapping, and
Evidence Preparation are outside this package.
