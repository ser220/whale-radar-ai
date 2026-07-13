# Intelligence contracts

## Purpose

`app.intelligence.contracts` defines immutable domain values shared by future
Experts and `MarketStateEngine`. It deliberately has no dependency on the
current production pipeline.

## Public API

- `Direction`, `TrendState`, and `LifecycleState`
- `ExpertOpinion`, `MarketState`, and `DecisionState`
- `ExpertRegistry`

All percentage-like values are validated in the inclusive `0..100` range.
Models serialize through `to_dict()` and restore through `from_dict()`.
Timestamps are stored as timezone-aware UTC datetimes. The registry accepts
objects that expose a non-empty `expert_name` attribute and requires
`replace=True` to overwrite an existing name.

## Dependencies

The package uses only the Python 3.9 standard library. It does not require
Pydantic or any new project dependency.

## Forbidden dependencies

Contracts must not import Telegram, FastAPI, database or repository modules,
the production pipeline, Arkham or other source adapters, or networking code.

## Basic usage

```python
from app.intelligence.contracts import Direction, ExpertOpinion

opinion = ExpertOpinion(
    expert_name="Trend",
    direction=Direction.BEARISH,
    state="CORRECTION",
    score=82,
    confidence=84,
    quality=91,
    reasons=["Bearish structure remains intact"],
)

payload = opinion.to_dict()
restored = ExpertOpinion.from_dict(payload)
```
