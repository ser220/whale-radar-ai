# Early Bird Foundation

## Purpose

Early Bird is Whale Radar AI's provider-neutral **Opportunity Hunter**. It
accepts already normalized candidate facts for multiple assets and returns a
deterministic, explainable attention ranking.

It answers which assets deserve attention, why they are interesting, how
urgent deeper analysis is, and how far the observable situation has developed.

**Early Bird is not a trade signal.** It never produces market direction,
BUY/SELL, LONG/SHORT, entry, target, stop-loss, execution, or position advice.

## Architecture position

```text
future normalized candidate builders
                |
                v
       EarlyBirdCandidate[]
                |
                v
         EarlyBirdEngine
                |
                v
 ranked EarlyBirdAssessment[]
                |
                v
 future MarketSituation orchestrator (stable IDs only)
```

Phase 1 has no provider calls, scanning, scheduling, persistence,
MarketSituation creation, Telegram output, or production integration.

## Public API

```python
from app.intelligence.early_bird import (
    EarlyBirdAssessment,
    EarlyBirdCandidate,
    EarlyBirdEngine,
    EarlyBirdFactor,
    EarlyBirdPolicy,
)
```

Contracts and policy are frozen dataclasses. Timestamps must be aware and are
normalized to UTC. All scores are finite values in `0..100`; booleans are
rejected as numeric values. Collections are defensively frozen and all
attached artifacts are stable string references.

## Opportunity, Priority, and Maturity

- **Opportunity** measures the strength of provider-neutral interesting facts,
  then degrades that strength for low quality or incomplete data. Missing data
  lowers reliability; it never becomes bullish or bearish evidence.
- **Priority** measures analysis urgency using opportunity, freshness, urgent
  whale/liquidity/structure events, and effective data quality.
- **Maturity** measures how far observable development has progressed through
  structure, momentum, volume, OI, and reduced freshness. It is not readiness,
  confidence, probability of profit, correction completion, or market-cycle
  maturity.

A high-opportunity, low-maturity result is an early developing case. A
high-opportunity, very-high-maturity result remains visible but receives an
over-mature warning.

## Complete three-candidate example

```python
from datetime import datetime, timezone

from app.intelligence.early_bird import EarlyBirdCandidate, EarlyBirdEngine

now = datetime.now(timezone.utc)


def candidate(candidate_id, asset, **scores):
    values = {
        "candidate_id": candidate_id,
        "asset": asset,
        "observed_at": now,
        "source": "normalized_candidate_builder",
        "quality": 90,
        "whale_activity_score": 0,
        "open_interest_change_score": 0,
        "funding_divergence_score": 0,
        "volume_expansion_score": 0,
        "relative_strength_score": 0,
        "liquidity_event_score": 0,
        "structure_event_score": 0,
        "momentum_shift_score": 0,
        "freshness_score": 90,
        "data_completeness_score": 90,
        "fast_event_ids": (),
        "observation_ids": (),
        "metadata": {"missing_sources": []},
    }
    values.update(scores)
    return EarlyBirdCandidate(**values)


candidates = [
    candidate(
        "candidate-btc-1",
        "BTCUSDT",
        whale_activity_score=100,
        liquidity_event_score=70,
        funding_divergence_score=50,
        relative_strength_score=45,
        structure_event_score=10,
        momentum_shift_score=10,
        fast_event_ids=("fast-whale-btc-1",),
    ),
    candidate(
        "candidate-eth-1",
        "ETHUSDT",
        open_interest_change_score=90,
        volume_expansion_score=85,
        relative_strength_score=80,
        funding_divergence_score=60,
        observation_ids=("oi-eth-1", "volume-eth-1"),
    ),
    candidate(
        "candidate-sol-1",
        "SOLUSDT",
        whale_activity_score=75,
        open_interest_change_score=95,
        volume_expansion_score=100,
        relative_strength_score=90,
        structure_event_score=100,
        momentum_shift_score=100,
        freshness_score=5,
        metadata={"overextension_score": 95},
    ),
]

ranked = EarlyBirdEngine().rank_candidates(candidates, timestamp=now)
for assessment in ranked:
    print(
        assessment.rank,
        assessment.asset,
        assessment.opportunity_score,
        assessment.priority_score,
        assessment.maturity_score,
        assessment.reasons,
        assessment.warnings,
    )
```

### Early whale-led opportunity

The BTC candidate is whale-led, fresh, and lightly developed. Whale and
liquidity facts raise Opportunity and Priority, while limited structure and
momentum keep Maturity low. This means “investigate early,” not “open a trade.”

### High-opportunity but over-mature case

The SOL candidate has many elevated factors, but its structure, momentum,
volume, OI, reduced freshness, and explicit overextension proxy produce high
Maturity. It receives an over-mature warning. The engine does not discard it or
turn the warning into a trading instruction.

## Scoring summary

Opportunity factor weights are whale `25%`, OI `15%`, funding divergence
`10%`, volume `15%`, relative strength `15%`, liquidity `10%`, structure `5%`,
and momentum `5%`. Reliability is the geometric mean of quality and
completeness ratios.

Priority is `45%` Opportunity, `25%` freshness, `20%` event urgency, and `10%`
effective quality. Event urgency is `50%` whale, `30%` liquidity, and `20%`
structure.

Maturity is `30%` structure, `25%` momentum, `20%` volume, `15%` OI, and `10%`
age proxy (`100 - freshness`). If normalized metadata explicitly supplies
`overextension_score`, the age component uses the average of age and that
proxy. Full exact formulas and thresholds are in the WR-036 specification.

## Ranking behavior

Results sort by priority descending, opportunity descending, maturity
ascending, asset, and candidate ID. Lower maturity therefore wins only after
priority and opportunity ties. Distinct candidate IDs for the same asset are
allowed and independently assessed; this supports separate timeframes or event
windows. Duplicate candidate IDs are rejected.

## Phase 1 limitations

- no market-wide live scanner or scheduled polling;
- no Arkham, CoinGlass, Nansen, exchange, or network adapter;
- no provider weighting calibration;
- no EarlyState, Expert, MarketStateEngine, or Decision Engine call;
- no MarketSituation creation, repository, database write, or persistence;
- no Telegram command or preview;
- no outcomes, learning, or production pipeline integration.
