# Reality Gap contracts

## Purpose and architecture position

This package is the immutable domain boundary between historical Expectation
Evaluation facts and a future Reality Gap analyzer. It records what an analyzer
declared, which primitive snapshots and references it used, and which policy
versions produced that record. PS-4 Step 7C contains **no evidence extraction,
classification, scoring, severity calculation, causal inference, persistence,
learning, Outcome Analysis, provider access, or production integration**.

## Public contracts

The package exports all Reality Gap enums plus `AnalysisProvenance`,
`AnalysisCapabilities`, `RealityGapEvidenceReference`,
`ObservabilityGapRecord`, `ExplanationGapRecord`, `RootCauseCandidate`,
`RootCauseTree`, `RealityGapDecisionTrace`, and `RealityGapAnalysis`. Pure
helpers validate tree integrity and analysis revisions, while
`canonical_json_bytes()` provides reproducible UTF-8 JSON serialization.

All records are frozen dataclasses. Timestamps are UTC-aware, mappings are
deeply frozen, numeric scores reject booleans and remain within `0..100`, and
`to_dict()`/`from_dict()` preserve enum and timestamp meaning.

## Provenance and capabilities

```python
from app.intelligence.reality_gap import AnalysisCapabilities, AnalysisProvenance

provenance = AnalysisProvenance(
    analysis_engine_version="engine-v1",
    classification_policy_version="classification-v1",
    candidate_policy_version="candidate-v1",
    metric_policy_version=None,
    severity_policy_version=None,
    tree_policy_version="tree-v1",
    trace_policy_version="trace-v1",
    taxonomy_version="taxonomy-v1",
    serialization_version="json-v1",
    created_by="reality_gap_engine",
    metadata={},
)
capabilities = AnalysisCapabilities(
    supports_market_gap=True,
    supports_intelligence_gap=True,
    supports_observability_gap=True,
    supports_explanation_gap=True,
    supports_root_cause_candidates=True,
    supports_root_cause_tree=False,
    supports_knowledge_gap_metric=False,
    supports_explanation_confidence_metric=False,
    supports_severity=False,
    supports_decision_trace=True,
    metadata={},
)
```

A false capability means that engine version did not support the output. It
does not mean that the corresponding gap was absent. Unsupported optional
outputs must remain `None`.

## Complete analysis and multi-dimensional gaps

A complete `RealityGapAnalysis` is assembled only from declared primitive
snapshots, evidence references, candidates, an optional validated tree, a
decision trace, provenance, and capability declarations. For example,
`dimensions=(RealityGapDimension.MARKET,
RealityGapDimension.OBSERVABILITY, RealityGapDimension.EXPLANATION)` records a
multi-dimensional gap without calculating it. `UNKNOWN` must be used alone.
The focused test fixture in `test_reality_gap_contracts.py` is the canonical
full-construction example and demonstrates complete round-trip restoration.

## Root-cause tree

```python
tree = RootCauseTree(
    tree_id="tree-1", tree_version="tree-v1",
    candidate_ids=("volume", "funding", "coverage"),
    root_candidate_ids=("volume", "coverage"),
    accepted_candidate_ids=("volume", "funding"),
    rejected_candidate_ids=(), unresolved_candidate_ids=("coverage",),
    edges=(("volume", "funding"),), maximum_depth=2, metadata={},
)
validate_root_cause_tree(tree, candidates)
```

Multiple roots are supported. Edges are deterministically ordered; cycles,
self-edges, duplicate edges, multiple parents, unresolved references, and
depth violations are rejected. Candidates remain hypotheses with explicit
dispositions, never proven causal truth.

## Observability and Explanation gaps

An `ObservabilityGapRecord` keeps unsupported, missing, stale, and provider
error facts distinct; unavailable input is never encoded as measured zero.
An `ExplanationGapRecord` can preserve an explicitly supplied residual,
uncovered criteria, and limitations. Neither record performs calculation or
asserts causality.

## Version lineage

`gap_id` identifies a lineage and `analysis_version` identifies one immutable
revision. Version 1 may omit `revision_reason`; later versions require it.
`validate_analysis_revision(previous, current)` requires stable expectation,
evaluation, Timeline, and asset identity, a one-step version increment, and an
unchanged eligible evidence boundary. It never modifies or merges records.

## Reproducibility

```python
payload = analysis.to_dict()
restored = RealityGapAnalysis.from_dict(payload)
assert restored == analysis
assert canonical_json_bytes(restored) == canonical_json_bytes(analysis)
```

Serialization uses sorted JSON keys and fixed separators. Contracts generate
no IDs or timestamps and do not depend on hash order, locale, process time,
host, environment, network, or external services.
