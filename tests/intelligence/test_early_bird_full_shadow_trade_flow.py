from datetime import datetime, timezone

from app.intelligence.early_bird import (
    EarlyBirdCandidate,
    EarlyBirdDecisionInputMapper,
)

from app.decision.application import (
    DecisionApplicationService,
)

from app.decision.contracts import (
    DecisionType,
)

from app.decision.lifecycle import (
    DecisionLifecycle,
)

from app.execution.paper import (
    PaperDecisionExecutor,
)

from app.execution.paper_lifecycle import (
    PaperTradeLifecycleService,
)

from app.performance import (
    PaperPerformanceTracker,
)


def build_candidate():

    return EarlyBirdCandidate(
        candidate_id="early-bird-BTC-001",
        asset="BTC",
        observed_at=datetime.now(
            timezone.utc
        ),
        source="early_bird_test",
        quality=90,
        whale_activity_score=80,
        open_interest_change_score=70,
        funding_divergence_score=60,
        volume_expansion_score=85,
        relative_strength_score=75,
        liquidity_event_score=50,
        structure_event_score=70,
        momentum_shift_score=80,
        freshness_score=95,
        data_completeness_score=95,
        fast_event_ids=("whale-001",),
        observation_ids=("obs-001",),
        metadata={},
    )


def test_early_bird_full_shadow_trade_flow():

    candidate = build_candidate()

    projection = (
        EarlyBirdDecisionInputMapper()
        .from_candidate(candidate)
    )

    service = DecisionApplicationService()

    decision = service.create_decision(
        projection=projection,
        decision_type=DecisionType.LONG,
        confidence=0.90,
    )

    approved = (
        service.approve_decision(
            decision.decision_id
        )
    )

    assert (
        approved.decision_state.value
        == "approved"
    )

    record = (
        service.get_record(
            decision.decision_id
        )
    )

    assert record is not None

    executor = PaperDecisionExecutor()

    trade = executor.execute(
        decision=record,
        symbol="BTCUSDT",
        price=65000.0,
        quantity=0.01,
    )

    assert trade.status == "OPEN"

    lifecycle = PaperTradeLifecycleService()

    result = lifecycle.close_trade(
        trade,
        exit_price=67000.0,
    )

    tracker = PaperPerformanceTracker()

    report = tracker.calculate(
        [result]
    )

    assert report.total_trades == 1
    assert report.total_pnl > 0
