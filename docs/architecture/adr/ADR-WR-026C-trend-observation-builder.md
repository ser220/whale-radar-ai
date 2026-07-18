# ADR-WR-026C: Trend Observation Builder

## Status

Proposed — pending Architecture Review.

## Context

WR-026A established immutable normalized observations and WR-026B established a
Trend Expert that consumes them. The repository did not yet have a pure way to
convert a chronological OHLCV series into those observation contracts. Passing
raw exchange candles directly to an expert would couple collection, data
normalization, fact calculation, and interpretation.

## Decision

Add a standard-library-only `app.intelligence.builders` layer. It owns an
immutable normalized `Candle`, a frozen versioned policy, and a deterministic
`TrendObservationBuilder`. The builder returns exactly one `TrendObservation`
and one `StructureObservation` and is not integrated with production services.

### Why normalized Candle exists

The candle contract removes exchange payload names, symbols, transport details,
and numeric ambiguity before calculation. It enforces finite positive OHLC,
non-negative volume, valid OHLC ordering, chronological UTC timestamps, and
lossless primitive serialization. Builders can therefore operate on facts that
have already crossed a stable validation boundary.

### Why the Builder is separate from the Expert

The builder calculates facts such as SMA alignment, normalized slope, swing
comparisons, ranges, and structure breaks. `TrendExpert` interprets those facts
into `ExpertOpinion`. Keeping them separate prevents a data-preparation change
from silently redefining expert confidence or market lifecycle semantics and
allows future builders to be tested without expert policy.

### Why deterministic standard-library calculations

Index-based OLS, arithmetic means, extrema, median intervals, and explicit
weighted formulas are sufficient for Phase 1. They are reproducible under the
project's Python 3.9.6 runtime, easy to audit, and introduce no runtime or
deployment dependency.

## Alternatives considered

### Expert consumes raw candles

Rejected because it mixes normalization and calculation with interpretation,
couples the expert to candle shape, and makes reuse by other consumers harder.

### pandas or TA-library builder

Rejected for Phase 1. It would add a third-party dependency and obscure simple
formulas behind library behavior without providing a necessary capability.

### Exchange-specific builder

Rejected because exchange payload schemas and transport concerns would leak
into the domain layer. Exchange adapters may later create normalized candles.

### Normalized pure builder

Selected. It gives the observation layer a deterministic upstream producer
while preserving infrastructure boundaries and backward compatibility.

## Phase 1 algorithms

The analysis price change uses the latest `long_window` candles. SMA alignment
uses relative short/long separation. Slope is an ordinary least-squares close
slope normalized by mean close and expressed in percent per candle.

Swing flags compare two adjacent blocks of `swing_lookback` candles. The high
and low extrema of the current block are compared with the preceding block
using a relative tolerance. Phase 1 deliberately does not discover pivots.

BOS/CHOCH uses the latest close against a reference range excluding that latest
candle. Opposing prior bias takes precedence and yields CHOCH; aligned prior
bias yields BOS; neutral prior bias yields BOS only with sufficiently clear
current directional evidence. Exactly one enum value is returned.

## BOS/CHOCH limitations

Block extrema are not discretionary market-structure pivots. The minimum 20
candles provide 19 preceding candles to the reference range; larger inputs use
at most `range_lookback` preceding candles. A single closing break is not a
multi-candle confirmation and the result is a normalized fact, not a trade
signal or reversal probability.

## Higher-timeframe limitation

Phase 1 receives one timeframe. `higher_timeframe_bias` is therefore always
`NEUTRAL`, and metadata explicitly records that HTF bias is unavailable. The
current timeframe is never copied into the HTF field.

## Consequences

Positive consequences:

- deterministic, immutable, serializable inputs and outputs;
- no new dependency and Python 3.9 compatibility;
- testable boundary between normalization, fact building, and interpretation;
- deterministic observation identity without database coordination;
- future exchange adapters can normalize without changing expert contracts.

Trade-offs:

- simple block swings are less expressive than pivot algorithms;
- fixed normalizers require later empirical review;
- timestamp regularity is inferred from observations, not timeframe parsing;
- inclusive range distance is normally zero because the latest candle
  participates in its range;
- policy carries weak/strong thresholds but Phase 1 emits no categorical label.

## Dependency boundaries

Builder production code may import only the Python standard library,
WR-026A observation contracts, and local builder modules. It must not import
Telegram, FastAPI, database, repositories, persistence, pipeline, Arkham,
funding services, exchange/network clients, pandas, NumPy, TA packages,
`TrendExpert`, `MarketStateEngine`, or another expert.

## Future compatibility

A future multi-timeframe builder can supply genuine HTF facts while retaining
the v1 single-timeframe behavior. Future WR-026D work can consume the stable
observation contracts but must not be started or inferred from this decision.
