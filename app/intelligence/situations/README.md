# Market Situation runtime contracts

## Purpose

`app.intelligence.situations` defines the Phase 1 runtime identity for one
market story. A `MarketSituation` preserves references to intelligence
artifacts, its explicit lifecycle and health, confidence history, expectations,
and an audit timeline. It is a domain contract, not a signal, decision engine,
repository, lifecycle controller, or learning algorithm.

## Architecture position

```text
Fast events / Observations / Expert opinions / Correlations / Market states
                                |
                       string references only
                                v
                        MarketSituation vN
                                |
                 future orchestrator and repository
```

No producer, Expert, UI, provider, or repository owns the whole situation.
Future orchestration may assemble a replacement version, but this package does
not fetch, evaluate, persist, or present anything.

## Public API

```python
from app.intelligence.situations import (
    ConfidencePoint,
    ExpectationRecord,
    ExpectationStatus,
    ExpectationViolationType,
    MarketSituation,
    SituationHealth,
    SituationStage,
    SituationTimelineEntry,
    TimelineEventType,
)
```

All models are frozen dataclasses. All timestamps must be timezone-aware and
are normalized to UTC. Percentage-like fields reject booleans, NaN, infinity,
and values outside `0..100`. Mutable metadata is defensively deep-frozen.

## Complete example

```python
from datetime import datetime, timedelta, timezone

from app.intelligence.situations import (
    ConfidencePoint,
    ExpectationRecord,
    ExpectationStatus,
    ExpectationViolationType,
    MarketSituation,
    SituationHealth,
    SituationStage,
    SituationTimelineEntry,
    TimelineEventType,
)

now = datetime.now(timezone.utc)

timeline_entry = SituationTimelineEntry(
    entry_id="timeline-001",
    event_type=TimelineEventType.DETECTION,
    occurred_at=now,
    summary="Fast structure event detected",
    artifact_ids=("fast-event-001",),
    metadata={"source_family": "fast"},
)

confidence = ConfidencePoint(
    recorded_at=now,
    value=42.0,
    source="shadow_intelligence",
    reason="Only early evidence is available",
    metadata={"experts": []},
)

expectation = ExpectationRecord(
    expectation_id="expectation-001",
    created_at=now,
    window_start=now,
    window_end=now + timedelta(minutes=30),
    description="Volume expansion should follow the structure event",
    basis_artifact_ids=("fast-event-001",),
    status=ExpectationStatus.PENDING,
    expected_event_type="VOLUME_EXPANSION",
    observed_event_ids=(),
    violation_type=ExpectationViolationType.NONE,
    gap_severity=0,
    learning_conclusion=None,
    metadata={"timeframe": "5m"},
)

situation = MarketSituation(
    situation_id="situation-btc-001",
    asset="btcusdt",
    created_at=now,
    updated_at=now,
    stage=SituationStage.DETECTED,
    health=SituationHealth.UNKNOWN,
    version=1,
    fast_event_ids=("fast-event-001",),
    observation_ids=(),
    expert_opinion_ids=(),
    expert_names=(),
    correlation_ids=(),
    market_state_ids=(),
    decision_context_ids=(),
    outcome_ids=(),
    learning_record_ids=(),
    memory_reference_ids=(),
    timeline=(timeline_entry,),
    confidence_history=(confidence,),
    expectation_history=(expectation,),
    metadata={"origin": "fast_detection"},
)

serialized = situation.to_dict()
restored = MarketSituation.from_dict(serialized)
assert restored == situation
assert restored.asset == "BTCUSDT"
```

Only stable IDs are attached. Raw `FastObservation`, `Observation`,
`ExpertOpinion`, `EventCorrelation`, and `MarketState` objects are deliberately
not embedded.

## Expectation example

Expectation evaluation is supplied explicitly by a future approved component.
The model records, but never infers, the answer.

```python
unexpected = ExpectationRecord(
    expectation_id="expectation-002",
    created_at=now,
    window_start=now,
    window_end=now + timedelta(minutes=30),
    description="Price should remain above the broken range",
    basis_artifact_ids=("observation-007",),
    status=ExpectationStatus.CONTRADICTED,
    expected_event_type="RANGE_HOLD",
    observed_event_ids=("event-returned-below-range",),
    violation_type=ExpectationViolationType.UNEXPECTED_EVENT,
    gap_severity=85,
    learning_conclusion="The apparent break failed inside the expectation window",
    metadata={},
)
```

- **What happened that should not have happened?** Represent it with
  `UNEXPECTED_EVENT` and reference the supplied event IDs.
- **What did not happen that should have happened?** Represent it with
  `MISSING_EXPECTED_EVENT` and the fixed `expected_event_type`.
- If both occurred, use `BOTH`.
- No observed event does not automatically mean `MISSING`; a record can remain
  `PENDING`, and missing input data is not an evaluation outcome.

The expected event and its basis are fixed in the immutable record before an
outcome. A changed or evaluated expectation belongs in a later situation
version; no post-hoc expectation is invented by these models.

## Versioning example

Phase 1 uses explicit constructor-only replacement. There are no mutation or
transition helpers.

```python
next_payload = situation.to_dict()
next_payload["version"] = situation.version + 1
next_payload["updated_at"] = (now + timedelta(minutes=5)).isoformat()
next_payload["stage"] = SituationStage.OBSERVED.value
next_situation = MarketSituation.from_dict(next_payload)

assert situation.version == 1
assert situation.stage is SituationStage.DETECTED
assert next_situation.version == 2
assert next_situation.stage is SituationStage.OBSERVED
```

Callers must carry all prior timeline, confidence, and expectation history into
the replacement. Late evidence creates a new version; it does not rewrite the
knowledge captured by a prior version. Version storage and enforcement across
versions belong to a future repository/orchestrator boundary.

## Phase 1 limitations

- no deterministic situation ID policy;
- no repository, database schema, persistence, or orchestration;
- no automatic lifecycle progression or health/confidence calculation;
- no expectation evaluation engine;
- no merge/split behavior;
- no Early Bird scanner, event producer, outcome collector, Decision Stability,
  Market DNA, similarity, memory, or learning engine;
- no Telegram, API, production pipeline, provider, or deployment integration.
