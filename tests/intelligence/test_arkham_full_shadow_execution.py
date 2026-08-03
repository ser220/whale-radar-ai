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

from app.decision.application.service import (
    DecisionApplicationService,
)

from app.decision.contracts import (
    DecisionType,
)

from app.execution.paper import (
    PaperDecisionExecutor,
)


def test_arkham_full_shadow_execution():

    event = ArkhamWhaleEvent(
        event_id="arkham-whale-001",
        chain=ArkhamChain.ETHEREUM,
        event_type=ArkhamEventType.CEX_WITHDRAWAL,
        direction=ArkhamFlowDirection.OUTFLOW,
        asset="ETH",
        amount_usd=27_947_700,
        source_entity="Kraken",
        destination_entity="Unknown Wallet",
        observed_at=datetime.now(
            timezone.utc
        ),
    )

    candidate = (
        ArkhamEarlyBirdCandidateBuilder()
        .build(event)
    )

    projection = (
        EarlyBirdDecisionInputMapper()
        .from_candidate(candidate)
    )

    service = DecisionApplicationService()

    decision = (
        service.create_decision(
            projection=projection,
            decision_type=DecisionType.LONG,
            confidence=0.90,
        )
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
            approved.decision_id
        )
    )

    assert record is not None

    trade = (
        PaperDecisionExecutor()
        .execute(
            decision=record,
            symbol="ETHUSDT",
            price=3500.0,
            quantity=1.0,
        )
    )

    assert (
        trade.symbol
        == "ETHUSDT"
    )

    assert (
        trade.status
        == "OPEN"
    )
