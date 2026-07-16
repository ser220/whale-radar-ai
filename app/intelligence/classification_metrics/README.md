# Classification and Metrics contracts

This package defines immutable, deterministic output records for future
Reality Gap Classification and Metrics consumers.

Public contracts:

- `RealityGapClassification`
- `RealityGapMetricSet`
- `RealityGapMetricValue`
- `MetricAvailability`
- categorized validation errors and failure enums

The package performs no classification, calculation, formula evaluation,
scoring, ranking, confidence, severity, persistence, or learning. Metric
availability is explicit: a missing, stale, unsupported, unavailable, or
errored metric has no measured value and is never serialized as zero.

Runtime dependencies are limited to the Python standard library and the
existing `RealityGapDimension` domain enum. Telegram, providers, databases,
repositories, networking, pipelines, Candidate, Projection, Mapping, and
Evidence Preparation are outside this package.
