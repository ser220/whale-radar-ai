# Observation Contracts

## Purpose

Observation contracts are immutable, normalized market facts that form the
common input language for future independent Experts. They contain no trading
signal, probability, lifecycle, execution, or source-access logic.

## Architecture position

```text
Raw Data
→ Observation Builders
→ Observation Contracts
→ Independent Experts
→ ExpertOpinion
→ MarketStateEngine
```

WR-026A implements only the Observation Contracts step. Builders and Experts
are separate future tasks.

## Public API

- Abstract common `Observation` contract
- `StructureBreak`, `TrendBias`, `FundingBias`, `LiquiditySide`, `DataTrend`
- `TrendObservation`
- `MomentumObservation`
- `StructureObservation`
- `FundingObservation`
- `OpenInterestObservation`
- `LiquidityObservation`

All concrete observations are frozen dataclasses with `to_dict()` and
`from_dict()` round-trip serialization.

## Trend example

```python
from datetime import datetime, timezone

from app.intelligence.observations import TrendBias, TrendObservation

trend = TrendObservation(
    observation_id="trend-btc-4h-001",
    asset="btc",
    source="normalized-candles",
    timeframe="4h",
    quality=92,
    observed_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
    price_change_pct=3.4,
    higher_high=True,
    higher_low=True,
    lower_high=False,
    lower_low=False,
    trend_bias=TrendBias.BULLISH,
    trend_strength=81,
    distance_from_range_pct=1.2,
    moving_average_alignment=TrendBias.BULLISH,
    slope=0.42,
)
```

The flags may contradict each other. The contract records those facts without
deciding whether a trend continues or reverses.

## Funding example

```python
from app.intelligence.observations import DataTrend, FundingBias, FundingObservation

funding = FundingObservation(
    observation_id="funding-btc-001",
    asset="BTC",
    source="normalized-funding",
    timeframe="8h",
    quality=88,
    observed_at=datetime(2026, 7, 14, tzinfo=timezone.utc),
    funding_rate=0.0003,
    annualized_funding_pct=32.85,
    funding_bias=FundingBias.LONG_CROWDED,
    funding_trend=DataTrend.RISING,
    exchange_count=4,
    spread_pct=0.012,
)
```

This describes funding facts; it does not predict a squeeze or trade direction.

## Versioning

Every observation defaults to `version=1`. Versions below 1 are invalid and
serialization preserves the version. Migrations are intentionally absent in
Phase 1. Future builders and Experts must explicitly declare which versions
they support.

## Observation versus ExpertOpinion

An Observation states normalized evidence such as price change, structure,
funding, open interest, or liquidity. An `ExpertOpinion` is a later analytical
interpretation with direction, score, confidence, reasons, and warnings.
Observation contracts never produce an `ExpertOpinion` themselves.

## Forbidden dependencies

This package must not depend on Telegram, FastAPI, pipelines, Arkham, exchange
clients, funding services, databases, repositories, persistence, HTTP or other
networking, `MarketStateEngine`, Expert registries, or concrete Experts.

## Phase 1 limitations

- No Observation Builder or raw payload parsing.
- No live data collection or multi-timeframe aggregation.
- No Expert, decision, probability, lifecycle, ETA, or trade-readiness logic.
- No persistence, API, Telegram, ML, or LLM integration.
- The package provides typed facts and per-type loading, not a global
  polymorphic factory or schema migration framework.
