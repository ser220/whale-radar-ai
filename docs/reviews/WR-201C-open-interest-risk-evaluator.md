# WR-201C — Open Interest Risk Evaluator

## Purpose

Add one isolated deterministic Open Interest risk evaluator that returns the
shared WR-201A `RiskComponent`.

## Input contract

`OpenInterestRiskInput` is a frozen, hashable value object containing exactly:

- `source: str`
- `symbol: str`
- `open_interest: float`
- `previous_open_interest: float`
- `observed_at: datetime`

Source and symbol must be strings, are stripped, and must remain non-empty.
Open Interest values must be finite real numbers and reject booleans.
`open_interest` must be non-negative and `previous_open_interest` must be
strictly positive. Integer values are accepted and normalized to floats.
The timestamp must be a datetime, must be timezone-aware, and is normalized to
UTC while preserving the represented instant.

## Policy contract

`OpenInterestRiskPolicy` is a frozen, hashable value object containing exactly:

- `extreme_change_percent: float`
- `medium_score_threshold: float`
- `high_score_threshold: float`
- `extreme_score_threshold: float`

All values must be finite real numbers and reject booleans.
`extreme_change_percent` must be strictly positive. Thresholds satisfy exactly:

```text
0 <= medium < high < extreme <= 100
```

The policy has no defaults and must be supplied by the caller.

## Change and score formulas

Signed change:

```text
(open_interest - previous_open_interest)
    / previous_open_interest
    * 100
```

Magnitude score:

```text
min(100, abs(change_percent) / extreme_change_percent * 100)
```

## Level boundaries

- Below the medium threshold: `RiskLevel.LOW`
- At medium and below high: `RiskLevel.MEDIUM`
- At high and below extreme: `RiskLevel.HIGH`
- At or above extreme: `RiskLevel.EXTREME`

Exact threshold values therefore map upward.

## Reason codes

Only the signed OI change selects the reason:

- positive: `OI_INCREASE`
- negative: `OI_DECREASE`
- zero, including negative zero: `OI_UNCHANGED`

The result always uses `RiskFactor.OPEN_INTEREST`.

## Architecture exclusions

WR-201C adds no aggregation, `RiskScore` population, Funding integration,
CVD or liquidity logic, exchange adapter, live API, persistence, CLI, alert,
AI behavior, trading behavior, directional prediction, squeeze
interpretation, price/OI combined logic, hidden policy default, metadata, or
shared evaluator/validation abstraction.

Existing WR-200, WR-201A, and WR-201B behavior remains unchanged.

## Compatibility

The implementation uses only Python 3.9-compatible standard-library APIs and
existing `app.risk` contracts. It imports neither Intelligence nor Decision.
