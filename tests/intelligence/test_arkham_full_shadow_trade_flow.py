from datetime import datetime, timezone

from app.intelligence.arkham.enums import (
    ArkhamChain,
    ArkhamEventType,
    ArkhamFlowDirection,
)

from app.intelligence.arkham.models import (
    ArkhamWhaleEvent,
)

from app.intelligence.arkham.early_bird_mapper import (
    ArkhamEarlyBirdMapper,
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


def build_event():

    return ArkhamWhaleEvent(
        event_id="arkham-whale-001",
        chain=ArkhamChain.ETHEREUM,
        event_type=ArkhamEventType.CEX_WITHDRAWAL,
        direction=ArkhamFlowDirection.OUTFLOW,
        asset="ETH",
        amount_usd=25000000,
        source_entity="Binance",
        destination_entity="Whale Wallet",
        observed_at=datetime.now(
            timezone.utc
        ),
    )


def test_arkham_full_shadow_trade_flow():

    candidate = (
        ArkhamEarlyBirdMapper()
        .map(
            build_event()
        )
    )

    projection = (
        EarlyBirdDecisionInputMapper()
        .from_candidate(
            candidate
        )
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

    record = service.get_record(
        approved.decision_id
    )

    executor = PaperDecisionExecutor()

    trade = executor.execute(
        decision=record,
        symbol="ETHUSDT",
        price=3200.0,
        quantity=1.0,
    )

    lifecycle = PaperTradeLifecycleService()

    result = lifecycle.close_trade(
        trade,
        exit_price=3400.0,
    )

    tracker = PaperPerformanceTracker()

    report = tracker.calculate(
        [result]
    )

    assert report.total_trades == 1
    assert report.total_pnl > 0
