# Trend Expert — Phase 1

## Purpose

`TrendExpert` is the first independent Whale Radar AI Expert. It evaluates one
immutable `TrendObservation` and one immutable `StructureObservation`, then
returns one immutable `ExpertOpinion`. It is deterministic, synchronous, and
contains no source access, production integration, or trading instructions.

## Architecture position

```text
Raw Data
→ Observation Builders
→ TrendObservation + StructureObservation
→ TrendExpert
→ ExpertOpinion
→ MarketStateEngine
```

WR-026B implements only the Trend Expert. Observation Builders and production
orchestration remain separate future work.

## Public API

```python
TrendExpert(policy=None).evaluate(
    trend,
    structure,
    *,
    timestamp=None,
) -> ExpertOpinion
```

The public name is `"trend"`. `TrendExpertPolicy` is a frozen configuration
object. Phase 1 accepts only version 1 observations.

## Full example

```python
from datetime import datetime, timezone

from app.intelligence.experts.trend import TrendExpert
from app.intelligence.observations import (
    StructureBreak,
    StructureObservation,
    TrendBias,
    TrendObservation,
)

observed_at = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

trend = TrendObservation(
    observation_id="trend-btc-4h-001",
    asset="BTC",
    source="normalized-candles",
    timeframe="4h",
    quality=92,
    observed_at=observed_at,
    price_change_pct=5,
    higher_high=True,
    higher_low=True,
    lower_high=False,
    lower_low=False,
    trend_bias=TrendBias.BULLISH,
    trend_strength=84,
    distance_from_range_pct=2.2,
    moving_average_alignment=TrendBias.BULLISH,
    slope=1.0,
)

structure = StructureObservation(
    observation_id="structure-btc-4h-001",
    asset="BTC",
    source="normalized-structure",
    timeframe="4h",
    quality=90,
    observed_at=observed_at,
    structure_break=StructureBreak.BULLISH_BOS,
    higher_timeframe_bias=TrendBias.BULLISH,
    structure_quality=88,
    swing_high=110,
    swing_low=90,
    range_high=108,
    range_low=92,
    current_price=105,
)

opinion = TrendExpert().evaluate(
    trend,
    structure,
    timestamp=datetime(2026, 7, 14, 12, 5, tzinfo=timezone.utc),
)
```

Representative output:

```python
{
    "expert_name": "trend",
    "direction": "BULLISH",
    "state": "TREND",
    "score": 86.0,          # exact value follows the documented formula
    "confidence": 90.0,    # exact value follows the documented formula
    "quality": 91.2,
    "reasons": ["..."],
    "warnings": [],
    "metadata": {
        "timeframe": "4h",
        "trend_observation_id": "trend-btc-4h-001",
        "structure_observation_id": "structure-btc-4h-001",
        "policy_version": "1.0",
    },
}
```

The abbreviated numeric values above illustrate shape, not a stable serialized
fixture. Tests and the specification contain the exact formulas.

## Direction versus state

Direction answers which side has a material evidence lead: `BULLISH`,
`BEARISH`, or `NEUTRAL`. State independently classifies the evidence as
`TREND`, `CORRECTION`, `REVERSAL`, `RANGE`, or `UNKNOWN`. A bullish short-term
direction may therefore coexist with `CORRECTION` inside a bearish
higher-timeframe context.

## Score, confidence, and quality

- `score` is trend conviction/classification strength, not profit probability.
  It combines 45% directional evidence, 30% normalized trend strength, and 25%
  structure support. For neutral/range results, balanced evidence contributes
  classification strength rather than directional force.
- `confidence` is robustness of the conclusion. It combines evidence agreement,
  effective quality, structure clarity, and timestamp coherence. Contradictions
  and stale inputs reduce it.
- `quality` describes inputs only: 60% TrendObservation quality and 40%
  StructureObservation quality. It is not conclusion confidence.

## Phase 1 limitations

- Only observation version 1 is supported; no migrations are performed.
- Rules and thresholds are transparent baselines, not empirically calibrated.
- Timeframe recognition accepts simple duration tokens such as `15m`, `4h`,
  `1d`, and `1w`; other normalized strings remain valid but produce a warning.
- `StructureObservation` has one `structure_break` value. It cannot represent
  CHOCH and subsequent BOS simultaneously, so Phase 1 reversal confidence is
  capped and warns that separate BOS confirmation is unavailable.
- The Expert has no history, raw candles, multi-timeframe builder, live data,
  Funding/OI/Liquidity Experts, or production orchestration.
- It never emits BUY/SELL, LONG/SHORT, entry, target, stop, READY/ACTION, ETA,
  lifecycle, or execution decisions.

## Forbidden dependencies

The Trend Expert must not depend on Telegram, FastAPI, database, repositories,
persistence, pipelines, Arkham, funding services, exchange clients, networking,
pandas, NumPy, TA libraries, `MarketStateEngine` internals, another Expert, ML,
or LLM calls.
