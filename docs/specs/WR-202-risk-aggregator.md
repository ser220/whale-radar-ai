# WR-202 — Risk Aggregator

## Purpose

Define the deterministic aggregation boundary that combines independent
`RiskComponent` values into one immutable aggregate risk result.

WR-202 must remain independent from market-data collection, individual risk
evaluators, Intelligence, Decision, Backtest, persistence, alerts, AI, and
trading execution.

## Input boundary

`RiskAggregator` accepts an immutable collection of existing shared
`RiskComponent` values.

The aggregator receives already evaluated risk components. It must not:

- calculate Funding, Open Interest, CVD, Liquidations, Liquidity, Whale, Flow,
  or Volatility metrics;
- accept raw exchange or market data;
- invoke individual evaluators;
- interpret evaluator-specific reason codes;
- depend on component ordering.

## Aggregation policy

Aggregation behavior is supplied explicitly through an immutable
`RiskAggregationPolicy`.

The policy contains:

- one explicit weight for every supported `RiskFactor`;
- `medium_score_threshold`;
- `high_score_threshold`;
- `extreme_score_threshold`.

The policy has no hidden defaults.

All weights must be finite real numbers greater than or equal to zero.

At least one weight must be greater than zero.

Score thresholds must satisfy:

```text
0 <= medium_score_threshold
  < high_score_threshold
  < extreme_score_threshold
  <= 100
```

## Component validation

Every supplied value must be a `RiskComponent`.

Each component score must be a finite real number within:

```text
0 <= score <= 100
```

Boolean values are not accepted as numeric scores.

Each `RiskFactor` may appear at most once.

Duplicate factors are rejected because silently replacing, averaging, or
selecting one duplicate would make aggregation ambiguous.

An empty component collection is rejected.

## Missing factors

A policy may define weights for factors that are absent from the current
component collection.

Absent factors do not contribute to either:

- the weighted numerator;
- the active weight denominator.

This prevents missing data from being interpreted as zero risk.

The aggregate score is calculated only from supplied factors whose configured
weight is greater than zero.

If all supplied factors have zero configured weight, aggregation is rejected.

## Formula

For every supplied component with a positive configured weight:

```text
weighted_score =
    component.score * factor_weight
```

The aggregate score is:

```text
total_score =
    sum(weighted_score)
    / sum(active_factor_weights)
```

The result always remains within `0..100` because every component score is
validated within `0..100` and all active weights are non-negative.

No additional score capping is required.

## Aggregate risk level

The aggregate `RiskLevel` is derived only from `total_score`.

Exact boundaries map upward:

```text
score < medium threshold       -> LOW
score < high threshold         -> MEDIUM
score < extreme threshold      -> HIGH
otherwise                      -> EXTREME
```

Individual component levels do not override the aggregate level.

WR-202 introduces no veto, escalation, maximum-level, emergency, or
single-factor override rule.

## Output contract

WR-202 introduces an immutable aggregate result contract named
`AggregatedRiskScore`.

It contains exactly:

- `total_score`;
- `level`;
- `components`.

`components` is stored as an immutable tuple ordered by
`RiskFactor.value`.

The original `RiskComponent` values are preserved unchanged.

The aggregate output contains no metadata dictionary, diagnostics,
timestamps, evaluator inputs, policy snapshot, or generic payload.

## Existing RiskScore

The existing WR-200 `RiskScore` contract remains unchanged.

WR-202 does not retrofit the old fixed category fields because they no longer
represent all supported factors.

Migration or replacement of `RiskScore` is outside the scope of WR-202.

## Public API

New package:

```text
app/risk/aggregation
```

Public exports:

- `AggregatedRiskScore`
- `RiskAggregationPolicy`
- `RiskAggregator`

The top-level `app.risk` package may re-export these contracts.

## Determinism

Equivalent inputs and the same aggregation policy must always produce an
identical result regardless of input ordering.

The implementation must not depend on:

- system time;
- randomness;
- external state;
- mutable cache;
- environment variables;
- network calls;
- persistence.

## Statelessness

`RiskAggregator` is completely stateless.

Repeated evaluations must never retain, merge, or compare components from
previous calls.

## Architecture exclusions

WR-202 adds no market-data evaluation, orchestration engine, historical state,
rolling windows, confidence calculation, correlation adjustment, directional
prediction, cascade prediction, persistence, CLI, alerts, AI behaviour,
Decision integration, Intelligence integration, Backtest integration, or
trading execution.

Existing WR-200 and WR-201A through WR-201E contracts remain unchanged.

## Compatibility

Implementation must use only Python 3.9-compatible standard-library APIs and
existing `app.risk` contracts.
