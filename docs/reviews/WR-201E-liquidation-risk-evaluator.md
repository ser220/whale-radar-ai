# WR-201E — Liquidation Risk Evaluator

## Purpose

Add one isolated deterministic evaluator for liquidation pressure during one
observation interval. Pressure is total liquidated notional relative to total
traded notional. The evaluator returns the shared WR-201A `RiskComponent`.

## Input contract

`LiquidationRiskInput` is a frozen, hashable value object containing exactly:

- `source: str`
- `symbol: str`
- `long_liquidation_notional: float`
- `short_liquidation_notional: float`
- `total_traded_notional: float`
- `observed_at: datetime`

Long liquidation notional is the value of long positions liquidated during
the interval. Short liquidation notional is the value of short positions
liquidated during the same interval. Total traded notional covers that same
interval. All three values must use the same currency or quote units.

Source and symbol must be strings, are stripped, and must remain non-empty.
Numeric values must be finite real numbers and reject booleans. Liquidation
notionals must be non-negative, total traded notional must be strictly
positive, and total liquidations cannot exceed total traded notional. Integer
values are accepted and normalized to floats. Positive and negative zero
liquidation values normalize to positive zero.

The timestamp must be a datetime, must be timezone-aware, and is normalized to
UTC while preserving the represented instant.

## Policy contract

`LiquidationRiskPolicy` is a frozen, hashable value object containing exactly:

- `extreme_liquidation_percent: float`
- `balanced_difference_percent: float`
- `medium_score_threshold: float`
- `high_score_threshold: float`
- `extreme_score_threshold: float`

All values must be finite real numbers and reject booleans. Extreme liquidation
percentage satisfies `0 < value <= 100`. Balanced difference percentage
satisfies `0 <= value <= 100`. Score thresholds satisfy exactly:

```text
0 <= medium < high < extreme <= 100
```

The policy has no defaults and must be supplied by the caller.

## Evaluation formulas

```text
total_liquidation_notional =
    long_liquidation_notional + short_liquidation_notional

liquidation_percent =
    total_liquidation_notional / total_traded_notional * 100

score =
    min(
        100,
        liquidation_percent / extreme_liquidation_percent * 100,
    )
```

Dominance difference:

```text
0                                           if total liquidations are zero
abs(long - short) / total_liquidations * 100 otherwise
```

## Level boundaries

- Below medium: `RiskLevel.LOW`
- At medium and below high: `RiskLevel.MEDIUM`
- At high and below extreme: `RiskLevel.HIGH`
- At or above extreme: `RiskLevel.EXTREME`

Exact score threshold values map upward.

## Reason codes

- No liquidation notional: `LIQUIDATIONS_NONE`
- Difference at or below the balanced threshold:
  `LIQUIDATIONS_BALANCED`
- Greater long liquidation notional: `LONG_LIQUIDATIONS_DOMINANT`
- Greater short liquidation notional: `SHORT_LIQUIDATIONS_DOMINANT`

The exact balanced threshold maps to `LIQUIDATIONS_BALANCED`. Dominance affects
only the reason code and never changes score or level. Long dominance means
more long positions were liquidated; short dominance means more short
positions were liquidated. Neither implies a future price direction.

The result always uses `RiskFactor.LIQUIDATIONS`.

## Architecture exclusions

WR-201E adds no event storage, cumulative state, previous-interval comparison,
exchange adapter, websocket, live API, aggregation, `RiskScore` population,
other-factor integration, price interpretation, directional or cascade
prediction, leverage estimation, Open Interest normalization, persistence,
CLI, alert, AI behavior, trading behavior, hidden policy default, metadata,
generic evaluator base, or shared validation abstraction.

Existing WR-200 and WR-201A through WR-201D contracts and behavior remain
unchanged.

## Compatibility

The implementation uses only Python 3.9-compatible standard-library APIs and
existing `app.risk` contracts. It imports neither Intelligence nor Decision.
