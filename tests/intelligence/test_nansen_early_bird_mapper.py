from datetime import datetime, timezone

import pytest

from app.intelligence.nansen.models import (
    SmartMoneyObservation,
)

from app.intelligence.nansen.early_bird_mapper import (
    NansenEarlyBirdMapper,
)

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)


def build_observation():
    return SmartMoneyObservation(
        asset="BNB",
        chain="BSC",
        net_flow_24h_usd=-6400,
        net_flow_7d_usd=310380,
        net_flow_30d_usd=403325,
        trader_count=139,
        market_cap_usd=78_700_000_000,
        observed_at=datetime.now(
            timezone.utc
        ),
    )


def test_nansen_maps_to_early_bird_candidate():

    candidate = (
        NansenEarlyBirdMapper()
        .map(
            build_observation()
        )
    )

    assert isinstance(
        candidate,
        EarlyBirdCandidate,
    )

    assert candidate.asset == "BNB"

    assert candidate.source == "nansen"

    assert (
        candidate.liquidity_event_score
        > 0
    )


def test_metadata_preserved():

    candidate = (
        NansenEarlyBirdMapper()
        .map(
            build_observation()
        )
    )

    assert (
        candidate.metadata["provider"]
        == "nansen"
    )

    assert (
        candidate.metadata["chain"]
        == "bsc"
    )


def test_invalid_observation():

    with pytest.raises(TypeError):

        NansenEarlyBirdMapper().map(
            "bad"
        )
