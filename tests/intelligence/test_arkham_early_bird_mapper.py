from datetime import datetime, timezone

import pytest

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

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)


def build_event():
    return ArkhamWhaleEvent(
        event_id="whale-001",
        chain=ArkhamChain.ETHEREUM,
        event_type=ArkhamEventType.WHALE_TRANSFER,
        direction=ArkhamFlowDirection.OUTFLOW,
        asset="ETH",
        amount_usd=25000000,
        source_entity="Binance",
        destination_entity="Unknown Wallet",
        observed_at=datetime.now(
            timezone.utc
        ),
    )


def test_arkham_maps_to_early_bird_candidate():

    candidate = (
        ArkhamEarlyBirdMapper()
        .map(build_event())
    )

    assert isinstance(
        candidate,
        EarlyBirdCandidate,
    )

    assert candidate.candidate_id == (
        "arkham:whale-001"
    )

    assert candidate.asset == "ETH"

    assert candidate.source == "arkham"

    assert candidate.whale_activity_score == 25


def test_metadata_preserved():

    candidate = (
        ArkhamEarlyBirdMapper()
        .map(build_event())
    )

    assert (
        candidate.metadata["provider"]
        == "arkham"
    )

    assert (
        candidate.metadata["chain"]
        == "ETHEREUM"
    )


def test_invalid_event():

    with pytest.raises(TypeError):

        ArkhamEarlyBirdMapper().map(
            "bad"
        )
