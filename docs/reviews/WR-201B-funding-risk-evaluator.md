# WR-201B — Funding Risk Evaluator

## Purpose

Add one deterministic funding-risk evaluator that returns the shared
WR-201A `RiskComponent`.

## Input contract

`FundingRiskInput` is a frozen, hashable value object containing exactly:

- `source: str`
- `symbol: str`
- `funding_rate: float`
- `funding_interval_hours: float`
- `observed_at: datetime`

Source and symbol are trimmed and must remain non-empty. Numeric values must be
finite real numbers and reject booleans. The funding interval must be strictly
positive. The funding-rate sign and magnitude are preserved. The timestamp
must be aware and is normalized to UTC.

## Policy contract

`FundingRiskPolicy` is a frozen, hashable value object containing exactly:

- `extreme_annualized_percent: float`
- `medium_score_threshold: float`
- `high_score_threshold: float`
- `extreme_score_threshold: float`

All values must be finite real numbers and reject booleans. The annualized
extreme threshold must be strictly positive. Score thresholds satisfy:

```text
0 <= medium < high < extreme <= 100
```

There is no default production policy.

## Evaluation

The evaluator annualizes funding magnitude:

```text
abs(funding_rate) * (24 / funding_interval_hours) * 365 * 100
```

It scales that magnitude against the caller-supplied extreme threshold and
caps the result at `100.0`. The caller-supplied score thresholds select
`RiskLevel`.

The result always uses `RiskFactor.FUNDING`. Funding sign affects only the
stable reason code:

- positive: `FUNDING_POSITIVE`
- negative: `FUNDING_NEGATIVE`
- zero: `FUNDING_NEUTRAL`

No directional market prediction is produced.

## Architecture boundary

WR-201B adds no Open Interest logic, aggregation, `RiskScore` population,
Intelligence or Decision integration, exchange adapter, live data,
persistence, API, CLI, alert, AI, or trading behavior.

The implementation uses only Python 3.9-compatible standard-library APIs and
the existing `app.risk` contracts.
