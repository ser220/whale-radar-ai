from datetime import datetime, timezone

import pytest

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

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)


def build_event():

    return ArkhamWhaleEvent(
        event_id="whale-001",
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


def test_arkham_event_maps_to_early_bird_candidate():

    candidate = (
        ArkhamEarlyBirdCandidateBuilder()
        .build(
            build_event()
        )
    )

    assert isinstance(
        candidate,
        EarlyBirdCandidate,
    )

    assert (
        candidate.candidate_id
        == "arkham:whale-001"
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
        == 30
    )


def test_invalid_event_rejected():

    with pytest.raises(TypeError):

        ArkhamEarlyBirdCandidateBuilder().build(
            "bad"
        )
