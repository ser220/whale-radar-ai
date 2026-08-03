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

from app.intelligence.early_bird.decision_input_mapper import (
    EarlyBirdDecisionInputMapper,
)

from app.decision.application import (
    DecisionApplicationService,
)

from app.decision.contracts import (
    DecisionType,
)


def build_event():

    return ArkhamWhaleEvent(
        event_id="whale-decision-001",
        chain=ArkhamChain.ETHEREUM,
        event_type=ArkhamEventType.CEX_WITHDRAWAL,
        direction=ArkhamFlowDirection.OUTFLOW,
        asset="ETH",
        amount_usd=30000000,
        source_entity="Binance",
        destination_entity="Whale Wallet",
        observed_at=datetime.now(
            timezone.utc
        ),
    )


def test_arkham_candidate_to_decision_flow():

    event = build_event()

    candidate = (
        ArkhamEarlyBirdCandidateBuilder()
        .build(event)
    )

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

    assert (
        decision.decision_type
        == DecisionType.LONG
    )

    assert (
        decision.confidence
        == 0.90
    )
