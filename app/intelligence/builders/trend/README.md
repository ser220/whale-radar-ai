# Trend Observation Builder

## Purpose

`TrendObservationBuilder` converts chronological normalized OHLCV candles into
one `TrendObservation` and one `StructureObservation`. It calculates market
facts only. Directional interpretation remains the responsibility of
`TrendExpert`.

## Architecture position

```text
normalized Candle values
    -> TrendObservationBuilder
    -> TrendObservation + StructureObservation
    -> TrendExpert
    -> ExpertOpinion
```

The builder is not connected to the production webhook pipeline and does not
collect candles.

## Public API

- `Candle`
- `TrendObservationBuilderPolicy`
- `TrendObservationBuilder`
- `TrendObservationBuilder.policy`
- `TrendObservationBuilder.build(...)`

These names are exported from `app.intelligence.builders`.

## Candle example

```python
from datetime import datetime, timedelta, timezone

from app.intelligence.builders import Candle

opened = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
candle = Candle(
    open_time=opened,
    open=100.0,
    high=102.0,
    low=99.0,
    close=101.0,
    volume=250.0,
    close_time=opened + timedelta(minutes=59),
)
```

`Candle` is immutable, exchange-independent, and serializes with `to_dict()`.
Both timestamps must be timezone-aware and are normalized to UTC.

## Builder example

```python
from datetime import datetime, timedelta, timezone

from app.intelligence.builders import Candle, TrendObservationBuilder

start = datetime(2026, 7, 13, tzinfo=timezone.utc)
candles = tuple(
    Candle(
        open_time=start + timedelta(hours=index),
        open=100.0 + index,
        high=100.4 + index,
        low=99.6 + index,
        close=100.0 + index,
        volume=10.0,
    )
    for index in range(25)
)

trend, structure = TrendObservationBuilder().build(
    candles,
    asset="btc",
    source="normalized-feed",
    timeframe="1h",
)
```

An abbreviated output is:

```python
trend.trend_bias                 # TrendBias.BULLISH
trend.moving_average_alignment   # TrendBias.BULLISH
trend.observed_at                # latest Candle.open_time
structure.structure_break        # StructureBreak.BULLISH_BOS
structure.higher_timeframe_bias  # TrendBias.NEUTRAL
```

IDs are deterministic:

```text
BTC:1h:trend:v1:2026-07-14T00:00:00+00:00
BTC:1h:structure:v1:2026-07-14T00:00:00+00:00
```

## TrendExpert integration

Integration is explicit and outside the builder:

```python
from app.intelligence.experts.trend import TrendExpert

opinion = TrendExpert().evaluate(
    trend,
    structure,
    timestamp=trend.observed_at,
)
```

## Calculations

- Price change uses the latest `long_window` closes.
- SMAs use the latest `short_window` and `long_window` closes.
- Slope is an OLS close slope divided by mean close and expressed as percent
  per candle.
- Swing flags compare the preceding and current `swing_lookback` blocks with
  `break_tolerance_pct` relative tolerance.
- Trend bias compares five bullish points with five mirrored bearish points:
  price change, slope, SMA alignment, and two swing flags. A lead of two points
  is required.
- Trend strength is 30% absolute price change, 25% absolute slope, 20% SMA
  separation, and 25% swing consistency. Normalizers are 5%, 1% per candle,
  and 2% respectively.
- Inclusive range high/low include the latest candle. Consequently a valid
  candle close normally has zero signed distance from that range.
- Structure breaks use a separate reference range that excludes the latest
  candle. With exactly 20 inputs, all 19 available preceding candles are used;
  otherwise at most `range_lookback` preceding candles are used.

## BOS versus CHOCH

A close must clear the prior reference boundary by `break_tolerance_pct`.
Opposing prior trend evidence has first priority and creates CHOCH. Aligned
prior evidence creates BOS. When prior evidence is neutral, BOS is emitted only
if current trend bias or SMA alignment clearly agrees with the break. A break is
never classified as both BOS and CHOCH.

## Quality

Trend observation quality combines count sufficiency (30%), timestamp
regularity (25%), positive-volume availability (15%), non-flat candle
availability (15%), and required-window coverage (15%). Structure observation
quality uses 25%, 30%, 10%, 15%, and 20%. `structure_quality` separately combines
count sufficiency (20%), swing clarity (25%), range validity (20%), break clarity
(15%), and timestamp regularity (20%). All quality values are bounded to 0..100.

## Phase 1 limitations

- No pivot-search or discretionary swing detection.
- The reference range may contain 19 candles at the minimum input size.
- No multi-timeframe input exists. `higher_timeframe_bias` is always `NEUTRAL`,
  and metadata contains `higher_timeframe_bias_available=False`.
- The builder does not assign trend lifecycle states, trading actions,
  confidence, probability, entries, targets, stops, or ETA.
- `weak_trend_threshold` and `strong_trend_threshold` are versioned policy
  boundaries reserved for consumers; Phase 1 does not emit a strength label.

## Forbidden dependencies

Production builder modules must not import Telegram, FastAPI, databases,
repositories, persistence, pipelines, Arkham, funding services, exchange
clients, networking, pandas, NumPy, TA libraries, experts, or
`MarketStateEngine`.
