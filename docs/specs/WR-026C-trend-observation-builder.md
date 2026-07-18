# WR-026C — Trend Observation Builder Specification

## Objective

Convert a normalized chronological OHLCV candle series deterministically into
one v1 `TrendObservation` and one v1 `StructureObservation`.

## Inputs

`build(candles, *, asset, source, timeframe, observation_id_prefix=None)`
accepts a list, tuple, or safely materializable iterable of `Candle` values.
The iterable is materialized exactly once. Input order is authoritative and is
never silently sorted.

## Outputs

The method returns `Tuple[TrendObservation, StructureObservation]`. Both use the
latest candle's `open_time` as `observed_at`, share normalized identity fields,
and use observation version 1.

## Candle contract

`Candle` is a frozen dataclass with `open_time`, `open`, `high`, `low`, `close`,
`volume`, and optional `close_time`. Timestamps must be aware and normalize to
UTC. OHLC values must be finite and greater than zero. Volume must be finite and
non-negative. Booleans are not numeric inputs. Low must not exceed open, close,
or high; high must not be below open or close. Close time cannot precede open
time. `to_dict()` uses ISO-8601 timestamps and `from_dict()` reconstructs them.

## Public API

```python
TrendObservationBuilder(
    policy: Optional[TrendObservationBuilderPolicy] = None
)

TrendObservationBuilder.build(
    candles,
    *,
    asset: str,
    source: str,
    timeframe: str,
    observation_id_prefix: Optional[str] = None,
) -> Tuple[TrendObservation, StructureObservation]
```

`Candle`, `TrendObservationBuilderPolicy`, and `TrendObservationBuilder` are
exported from `app.intelligence.builders`. The builder exposes a read-only
`policy` property.

## Policy and thresholds

Defaults are:

| Field | Default |
| --- | ---: |
| `minimum_candles` | 20 |
| `short_window` | 5 |
| `long_window` | 20 |
| `slope_window` | 10 |
| `swing_lookback` | 5 |
| `range_lookback` | 20 |
| `break_tolerance_pct` | 0.10 |
| `flat_slope_threshold` | 0.05 |
| `weak_trend_threshold` | 35 |
| `strong_trend_threshold` | 70 |
| `policy_version` | `1.0` |
| `observation_version` | 1 |

All windows are integers at least two. Long window covers short window,
minimum count covers long window, two swing blocks, and range lookback, and
slope window cannot exceed the minimum. Thresholds are finite and
non-negative; weak/strong thresholds are bounded 0..100 and ordered. Version 1
is the only supported observation version. Weak/strong thresholds are reserved
policy boundaries; no strength label is emitted in Phase 1.

## Formulas

### Price change

The analysis window is the latest `min(candle_count, long_window)` candles:

```text
price_change_pct = 100 * (latest_close - analysis_first_close)
                         / analysis_first_close
```

### Simple moving averages

```text
short_sma = mean(latest short_window closes)
long_sma  = mean(latest long_window closes)
ma_separation_pct = 100 * (short_sma - long_sma) / long_sma
```

Alignment is `BULLISH` above `+flat_slope_threshold`, `BEARISH` below its
negative, otherwise `NEUTRAL`. A prior series shorter than `long_window` has
neutral alignment.

### Normalized slope

For the latest `slope_window` closes, with index `x=0..n-1`:

```text
raw_slope = sum((x-mean_x)*(close-mean_close)) / sum((x-mean_x)^2)
slope = 100 * raw_slope / mean_close
```

The result is percent change per candle.

### Swing flags

The latest `2 * swing_lookback` candles are divided into preceding and current
blocks. Each block supplies maximum high and minimum low. With
`t = break_tolerance_pct / 100`, current high above `previous_high*(1+t)` is
higher-high and below `previous_high*(1-t)` is lower-high. The same comparison
creates higher-low/lower-low. Values inside tolerance create neither flag.
`swing_high` and `swing_low` are the current-block extrema.

### Trend bias

Bullish points are awarded for price change above `flat_slope_threshold`, slope
above it, bullish SMA alignment, higher-high, and higher-low. Five mirrored
conditions award bearish points. A lead of at least two yields `BULLISH` or
`BEARISH`; otherwise the result is `NEUTRAL`. Structure breaks are excluded.

### Trend strength

```text
price_component = min(abs(price_change_pct) / 5 * 100, 100)
slope_component = min(abs(slope) / 1 * 100, 100)
ma_component = min(abs(ma_separation_pct) / 2 * 100, 100)
swing_component = 100 for consistent HH+HL or LH+LL,
                   50 for exactly one directional swing flag,
                    0 for mixed or absent flags
trend_strength = 0.30*price + 0.25*slope + 0.20*ma + 0.25*swing
```

The result is bounded 0..100 and is not confidence or probability.

### Ranges and distance

Inclusive `range_high` and `range_low` are extrema over the latest
`range_lookback` candles, including the latest. Signed distance is zero inside,
`100*(close-range_high)/range_high` above, and
`-100*(range_low-close)/range_low` below. A valid latest candle normally makes
this zero because its high/low enclose its close.

The structure reference range excludes the latest candle and uses at most the
preceding `range_lookback` candles. At the minimum 20-candle input, 19 preceding
candles are available and all are used.

### BOS and CHOCH

A bullish break requires `close > reference_high*(1+t)`; a bearish break
requires `close < reference_low*(1-t)`. Prior trend evidence is recalculated
from candles excluding the last candle. Precedence is:

1. opposing prior bias -> CHOCH;
2. aligned prior bias -> BOS;
3. neutral prior bias -> BOS only when current trend bias or SMA alignment
   agrees with the break;
4. otherwise -> `NONE`.

The branches are mutually exclusive, so a break receives one classification.

### Timestamp regularity

Intervals are differences between adjacent open times. Median interval is
recorded. An interval is irregular when its relative distance from the median
exceeds 10%. `irregular_interval_ratio` is irregular count divided by interval
count. Irregularity reduces quality but is not rejected.

## Quality formulas

```text
count_score = min(100, 70 + 30*(count-minimum_candles)/minimum_candles)
regularity_score = 100*(1-irregular_interval_ratio)
volume_score = 100*positive_volume_candles/count
activity_score = 100*nonzero_high_low_range_candles/count
coverage_score = mean(min(100, 100*count/window))
```

Coverage windows are short, long, slope, two swing blocks, and range.

```text
trend quality = 30% count + 25% regularity + 15% volume
                + 15% activity + 15% coverage
structure observation quality = 25% count + 30% regularity + 10% volume
                                + 15% activity + 20% coverage
structure_quality = 20% count + 25% swing clarity + 20% range validity
                    + 15% break clarity + 20% regularity
```

Swing clarity uses the trend-strength swing component. Range validity is 100
for nonzero range and 0 otherwise. Break clarity is 100 for a classified break
or a close clearly within the tolerance-adjusted reference range, otherwise 50.
Every result is bounded to 0..100.

## Observation identity

Default IDs are:

```text
{ASSET}:{timeframe}:trend:v1:{latest_open_time_iso}
{ASSET}:{timeframe}:structure:v1:{latest_open_time_iso}
```

When supplied, a validated deterministic custom prefix replaces
`{ASSET}:{timeframe}`. No random or database identity is used.

## Metadata

Both observations include candle count, first/latest ISO open times, median
interval seconds, irregular ratio, both SMAs, reference range high/low, policy
version, and calculation-window length. Structure metadata additionally has
`higher_timeframe_bias_available=False`. Raw candles are never stored.

## Validation and versioning

Candles cannot be empty or fewer than policy minimum. Every item must be exactly
a `Candle`; timestamps must strictly increase and duplicates are rejected.
Asset, source, and timeframe are required non-empty strings; asset is uppercased.
Inputs are not sorted, dropped, or mutated. Phase 1 emits only version 1.

## Forbidden dependencies

Production builder code may use only the Python standard library, observation
contracts, and local builder modules. Infrastructure, networking, exchanges,
third-party numerical/TA packages, experts, and MarketStateEngine are forbidden.

## Out of scope

Collection, exchange APIs, websockets, Telegram, deployment, production
integration, database/persistence, multi-timeframe analysis, real HTF bias,
other experts/builders, readiness, decision/lifecycle state, alerts, execution,
machine learning, and LLM calls are out of scope. WR-026D is not part of this
task.

## Acceptance criteria

- immutable normalized candle and policy;
- deterministic validated observations and IDs;
- documented formulas, precedence, quality, and metadata;
- 64 focused behaviors including Expert and Engine compatibility;
- Python 3.9 compilation and all required regressions pass;
- dependency audit and clean diff confirm no production integration or new
  dependency.

## Verification commands

```bash
PYTHONPYCACHEPREFIX=/tmp/whale_radar_pycache ./venv/bin/python -m py_compile <WR-026C and intelligence files>
./venv/bin/python -m unittest -v test_trend_observation_builder.py
./venv/bin/python -m unittest -v test_trend_expert.py
./venv/bin/python -m unittest -v test_observation_contracts.py
./venv/bin/python -m unittest -v test_intelligence_contracts.py
./venv/bin/python -m unittest -v test_market_state_engine.py
./venv/bin/python test_core.py
./venv/bin/python test_filter.py
./venv/bin/python test_parser.py
git diff --check
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
```
