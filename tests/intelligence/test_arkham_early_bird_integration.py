from datetime import datetime, timezone

from app.intelligence.arkham.enums import (
    ArkhamChain,
    ArkhamEventType,
    ArkhamFlowDirection,
)

from app.intelligence.arkham.models import (
    ArkhamWhaleEvent,
)

from app.intelligence.arkham.early_bird_candidate_builder import (
    ArkhamEarlyBirdCandidateBuilder,
)


def test_arkham_event_to_early_bird_candidate():

    event = ArkhamWhaleEvent(
        event_id="whale-eth-001",
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

    assert (
        candidate.asset
        == "ETH"
    )

    assert (
        candidate.source
        == "arkham"
    )

    assert (
        candidate.whale_activity_score
        > 20
    )

    assert (
        candidate.metadata["amount_usd"]
        == 27_947_700
    )
