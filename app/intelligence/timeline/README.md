# Market Situation Timeline

## Purpose

This package preserves the lifecycle history of one Market Situation. Each
entry is an immutable point-in-time record of what the system knew. A later
observation produces a replacement timeline with one additional entry; it never
rewrites an earlier entry.

The Timeline is not a trading journal, signal history, stage classifier,
prediction evaluator, persistence layer, or Decision Engine.

## Public API

- `SituationDNA`: normalized point-in-time factor and score snapshot.
- `MarketSituationTimelineEntry`: lifecycle stage, evidence, expectations, and
  provenance captured at one instant.
- `MarketSituationTimeline`: immutable ordered timeline version.
- `append_timeline_entry()`: pure append-only replacement operation.

`EmergingStage` is reused from `app.intelligence.early_bird`; Timeline records
the supplied stage without inferring whether it is correct.

## Example: SEED → EMERGING → BUILDING

```python
from datetime import datetime, timedelta, timezone

from app.intelligence.early_bird import EmergingStage
from app.intelligence.timeline import (
    MarketSituationTimeline,
    MarketSituationTimelineEntry,
    SituationDNA,
    append_timeline_entry,
)

now = datetime.now(timezone.utc)

dna = SituationDNA(
    whale_activity=None,              # unavailable, not measured zero
    funding_divergence=62,
    volume_expansion=74,
    structure_event=41,
    momentum_shift=35,
    relative_strength=55,
    open_interest_change=None,
    liquidity_event=None,
    completeness=62.5,
    quality=78,
    freshness=91,
    opportunity=66,
    priority=73,
    maturity=24,
    emergence=81,
    horizon=88,
    detection_confidence=76,
    factor_availability={
        "funding_divergence": "AVAILABLE",
        "whale_activity": "MISSING",
    },
    metadata={"timeframe": "15m"},
)

seed = MarketSituationTimelineEntry(
    entry_id="entry-seed",
    timeline_id="timeline-link-1",
    created_at=now,
    stage=EmergingStage.SEED,
    dna=dna,
    supporting_factors=("volume_expansion",),
    limiting_factors=("whale_activity_missing",),
    expected_events=("volume_remains_expanded",),
    observed_events=(),
    missing_expected_events=(),
    unexpected_events=(),
    transition_reason="Initial evidence recorded",
    source_assessment_id="assessment-1",
    source_candidate_id="candidate-1",
    source_situation_id=None,
    metadata={},
)

timeline_v1 = MarketSituationTimeline(
    timeline_id="timeline-link-1",
    asset="LINK",
    created_at=now,
    updated_at=now,
    entries=(seed,),
    current_stage=EmergingStage.SEED,
    version=1,
    metadata={},
)

emerging = MarketSituationTimelineEntry.from_dict({
    **seed.to_dict(),
    "entry_id": "entry-emerging",
    "created_at": (now + timedelta(minutes=15)).isoformat(),
    "stage": "EMERGING",
    "observed_events": ["volume_remains_expanded"],
    "transition_reason": "Emerging stage supplied by upstream analysis",
})
timeline_v2 = append_timeline_entry(
    timeline_v1,
    emerging,
    updated_at=emerging.created_at,
)

building = MarketSituationTimelineEntry.from_dict({
    **emerging.to_dict(),
    "entry_id": "entry-building",
    "created_at": (now + timedelta(minutes=30)).isoformat(),
    "stage": "BUILDING",
    "transition_reason": "Building stage supplied by upstream analysis",
})
timeline_v3 = append_timeline_entry(
    timeline_v2,
    building,
    updated_at=building.created_at,
)

assert timeline_v1.current_stage is EmergingStage.SEED
assert timeline_v2.current_stage is EmergingStage.EMERGING
assert timeline_v3.current_stage is EmergingStage.BUILDING
assert len(timeline_v1.entries) == 1  # older history remains unchanged
```

Expectation facts answer both architecture questions without evaluating them:

- “What happened that should not have happened?” is stored explicitly in
  `unexpected_events`, for example `("liquidity_sweep",)`.
- “What did not happen that should have happened?” is stored explicitly in
  `missing_expected_events`, for example `("expected_follow_through",)`.

An empty `observed_events` collection never populates either category
automatically.

## Dependencies and boundaries

Runtime code uses the Python standard library, local timeline modules, and the
public Early Bird `EmergingStage`. It has no provider, exchange, Telegram,
FastAPI, database, repository, pipeline, Decision Engine, Trade Readiness,
MarketStateEngine, Expert, scanner, or networking dependency.

## Phase 1 limitations

The package is memory-only. It does not discover timelines, persist versions,
attach them to `MarketSituation`, calculate transitions, evaluate outcomes,
compare DNA, learn, schedule work, or integrate with production.
