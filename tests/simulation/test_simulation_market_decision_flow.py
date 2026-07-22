from datetime import datetime, timezone

from app.simulation import (
    SimulationSnapshot,
    SimulationMarketAdapter,
)

from app.intelligence.market_mapper import (
    MarketDecisionInputMapper,
)

from app.intelligence.candidate_decision_input import (
    CandidateDecisionInputProjection,
)


def test_simulation_market_to_decision_input_flow():

    simulation_snapshot = SimulationSnapshot(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.03,
        timestamp=datetime.now(
            timezone.utc
        ),
    )

    market_snapshot = (
        SimulationMarketAdapter
        .to_market_snapshot(
            simulation_snapshot
        )
    )

    projection = (
        MarketDecisionInputMapper
        .from_snapshot(
            market_snapshot
        )
    )

    assert isinstance(
        projection,
        CandidateDecisionInputProjection,
    )

    assert (
        projection.candidate_reference
        ==
        "BTCUSDT-candidate"
    )

    assert (
        projection.intelligence_reference
        ==
        "BTCUSDT-market"
    )
