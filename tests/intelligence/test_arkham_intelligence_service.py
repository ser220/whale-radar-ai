from datetime import datetime, timezone

from app.intelligence.arkham import (
    ArkhamWhaleEvent,
    ArkhamChain,
    ArkhamEventType,
    ArkhamFlowDirection,
)

from app.intelligence.arkham.service import (
    ArkhamIntelligenceService,
)


def test_build_candidates():

    event = ArkhamWhaleEvent(
        event_id="arkham-service-001",
        chain=ArkhamChain.ETHEREUM,
        event_type=ArkhamEventType.CEX_WITHDRAWAL,
        direction=ArkhamFlowDirection.OUTFLOW,
        asset="ETH",
        amount_usd=30_000_000,
        source_entity="Binance",
        destination_entity="Unknown Wallet",
        observed_at=datetime.now(
            timezone.utc
        ),
    )

    service = ArkhamIntelligenceService()

    candidates = (
        service.build_candidates(
            [event]
        )
    )

    assert len(candidates) == 1

    candidate = candidates[0]

    assert (
        candidate.asset
        == "ETH"
    )

    assert (
        candidate.source
        == "arkham"
    )

    assert (
        candidate.metadata["amount_usd"]
        == 30_000_000
    )
