# WR-201D — CVD Risk Evaluator

## Purpose

Add one isolated deterministic evaluator for the magnitude of aggressive
buy/sell imbalance during one observation interval. The evaluator returns the
shared WR-201A `RiskComponent`.

## Input contract

`CVDRiskInput` is a frozen, hashable value object containing exactly:

- `source: str`
- `symbol: str`
- `cvd_delta: float`
- `total_volume: float`
- `observed_at: datetime`

`cvd_delta` is the signed aggressive-flow delta for one interval. Positive
values represent net aggressive buying and negative values represent net
aggressive selling. `total_volume` is the total traded volume for that same
interval. Both values must use the same units.

Source and symbol must be strings, are stripped, and must remain non-empty.
Numeric values must be finite real numbers and reject booleans. Total volume
must be strictly positive, and the absolute CVD delta cannot exceed total
volume. Integer values are accepted and normalized to floats.

The timestamp must be a datetime, must be timezone-aware, and is normalized to
UTC while preserving the represented instant.

## Policy contract

`CVDRiskPolicy` is a frozen, hashable value object containing exactly:

- `extreme_imbalance_percent: float`
- `medium_score_threshold: float`
- `high_score_threshold: float`
- `extreme_score_threshold: float`

All values must be finite real numbers and reject booleans.
`extreme_imbalance_percent` must satisfy `0 < value <= 100`. Score thresholds
satisfy exactly:

```text
0 <= medium < high < extreme <= 100
```

The policy has no defaults and must be supplied by the caller.

## Imbalance and score formulas

Signed interval imbalance:

```text
cvd_delta / total_volume * 100
```

Magnitude score:

```text
min(100, abs(imbalance_percent) / extreme_imbalance_percent * 100)
```

## Level boundaries

- Below medium: `RiskLevel.LOW`
- At medium and below high: `RiskLevel.MEDIUM`
- At high and below extreme: `RiskLevel.HIGH`
- At or above extreme: `RiskLevel.EXTREME`

Exact threshold values map upward.

## Reason codes

Only imbalance sign selects the reason:

- positive: `CVD_BUY_DOMINANT`
- negative: `CVD_SELL_DOMINANT`
- positive or negative zero: `CVD_BALANCED`

The result always uses `RiskFactor.CVD`.

## Architecture exclusions

WR-201D adds no cumulative CVD state, previous-CVD comparison, aggregation,
`RiskScore` population, other-factor integration, price/CVD divergence,
trend interpretation, exchange adapter, live API, persistence, CLI, alert,
AI behavior, trading behavior, directional prediction, hidden policy default,
metadata, generic evaluator base, or shared validation abstraction.

Existing WR-200 and WR-201A through WR-201C contracts and behavior remain
unchanged.

## Compatibility

The implementation uses only Python 3.9-compatible standard-library APIs and
existing `app.risk` contracts. It imports neither Intelligence nor Decision.
