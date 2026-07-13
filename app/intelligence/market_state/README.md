# Market State Engine — Phase 1

## Purpose

`MarketStateEngine` is a pure domain orchestrator. It receives already-produced
`ExpertOpinion` values and deterministically synthesizes a `MarketState`. It is
not a signal generator, execution engine, source adapter, or production
integration.

## Public API

```python
MarketStateEngine.synthesize(
    opinions,
    *,
    weights=None,
    timestamp=None,
) -> MarketState
```

`SynthesisPolicy` exposes the documented Phase 1 thresholds and output caps.

## Example

```python
from datetime import datetime, timezone

from app.intelligence.contracts import Direction, ExpertOpinion
from app.intelligence.market_state import MarketStateEngine

trend = ExpertOpinion(
    expert_name="Trend",
    direction=Direction.BEARISH,
    state="TREND",
    score=82,
    confidence=84,
    quality=91,
    reasons=["Bearish structure remains intact"],
)
flow = ExpertOpinion(
    expert_name="Flow",
    direction=Direction.BEARISH,
    state="CORRECTION",
    score=76,
    confidence=78,
    quality=86,
    reasons=["Exchange inflow remains elevated"],
)

state = MarketStateEngine().synthesize(
    [trend, flow],
    weights={"Trend": 1.25, "Flow": 1.0},
    timestamp=datetime(2026, 7, 13, tzinfo=timezone.utc),
)
```

## Weights

Effective contribution is:

```text
configured weight × confidence/100 × quality/100
```

The default configured weight is `1.0`. Weights must be finite and non-negative.
A zero weight excludes that Expert from aggregation. Valid weights for unknown
Expert names are ignored and produce a warning.

## Probabilities

Continuation, correction, and reversal probabilities are weighted support
scores against total effective contribution. They are independent reporting
fields and are not required to sum to 100 because `RANGE` and `UNKNOWN` support
may also be present.

## Forbidden dependencies

This package must not depend on Telegram, FastAPI, Pydantic, databases,
repositories, persistence, the production pipeline, Arkham, funding or source
adapters, networking clients, or delivery infrastructure.

## Phase 1 limitations

- The engine aggregates opinions; it does not execute Experts.
- Market maturity is a provisional synthesis proxy, not market-cycle completion.
- The policy is deterministic and does not use ML, LLM calls, or randomness.
- No Timeline, ETA, Trade Readiness, lifecycle transition, persistence, API, or
  Telegram integration is included.
