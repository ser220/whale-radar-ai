from datetime import datetime, timezone

from app.intelligence.arkham.models import (
    ArkhamWhaleEvent,
)

from app.intelligence.arkham.enums import (
    ArkhamChain,
    ArkhamEventType,
    ArkhamFlowDirection,
)

from app.intelligence.arkham.early_bird_candidate_builder import (
    ArkhamEarlyBirdCandidateBuilder,
)

from app.intelligence.candidate_decision_input.early_bird_mapper import (
    EarlyBirdDecisionInputMapper,
)

from app.decision.application import (
    DecisionApplicationService,
)

from app.decision.contracts import (
    DecisionType,
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


def build_whale_event():

    return ArkhamWhaleEvent(
        event_id="arkham-e2e-001",
        chain=ArkhamChain.ETHEREUM,
        event_type=ArkhamEventType.CEX_WITHDRAWAL,
        direction=ArkhamFlowDirection.OUTFLOW,
        asset="ETH",
        amount_usd=50000000,
        source_entity="Binance",
        destination_entity="Whale Wallet",
        observed_at=datetime.now(
            timezone.utc
        ),
    )


def test_arkham_full_shadow_trade_flow():

    event = build_whale_event()

    candidate = (
        ArkhamEarlyBirdCandidateBuilder()
        .build(event)
    )

    projection = (
        EarlyBirdDecisionInputMapper()
        .from_candidate(candidate)
    )

    decision_service = (
        DecisionApplicationService()
    )

    decision = (
        decision_service
        .create_decision(
            projection=projection,
            decision_type=DecisionType.LONG,
            confidence=0.90,
        )
    )

    approved = (
        decision_service
        .approve_decision(
            decision.decision_id
        )
    )

    record = (
        decision_service
        .get_record(
            approved.decision_id
        )
    )

    executor = PaperDecisionExecutor()

    trade = (
        executor.execute(
            decision=record,
            symbol="ETHUSDT",
            price=3000.0,
            quantity=1.0,
        )
    )

    lifecycle = PaperTradeLifecycleService()

    result = (
        lifecycle.close_trade(
            trade,
            exit_price=3300.0,
        )
    )

    tracker = PaperPerformanceTracker()

    report = (
        tracker.calculate(
            [result]
        )
    )

    assert (
        approved.decision_state.value
        == "approved"
    )

    assert (
        report.total_trades
        == 1
    )

    assert (
        report.total_pnl
        > 0
    )
