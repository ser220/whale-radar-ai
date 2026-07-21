from datetime import datetime, timezone

import pytest

from app.intelligence.market import (
    MarketSnapshot,
)
from app.intelligence.market_mapper import (
    MarketDecisionInputMapper,
)
from app.intelligence.candidate_decision_input import (
    CandidateDecisionInputStatus,
    CandidateDecisionInputVersion,
)


def build_snapshot() -> MarketSnapshot:
    return MarketSnapshot(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.035,
        captured_at=datetime.now(
            timezone.utc
        ),
    )


def test_market_snapshot_maps_to_candidate_input():
    snapshot = build_snapshot()

    projection = (
        MarketDecisionInputMapper
        .from_snapshot(snapshot)
    )

    assert (
        projection.candidate_reference
        == "BTCUSDT-candidate"
    )

    assert (
        projection.intelligence_reference
        == "BTCUSDT-market"
    )

    assert (
        projection.status
        == CandidateDecisionInputStatus.AVAILABLE
    )

    assert (
        projection.version
        == CandidateDecisionInputVersion.V1
    )


def test_mapper_preserves_timestamp():
    snapshot = build_snapshot()

    projection = (
        MarketDecisionInputMapper
        .from_snapshot(snapshot)
    )

    assert (
        projection.created_at
        == snapshot.captured_at
    )


def test_invalid_snapshot_rejected():
    with pytest.raises(TypeError):
        MarketDecisionInputMapper.from_snapshot(
            "invalid"
        )
