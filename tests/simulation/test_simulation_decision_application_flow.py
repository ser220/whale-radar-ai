from datetime import datetime, timezone

from app.simulation import (
    SimulationSnapshot,
    SimulationMarketAdapter,
    SimulationDecisionAdapter,
)

from app.intelligence.market_mapper import (
    MarketDecisionInputMapper,
)

from app.intelligence.candidate_decision_input import (
    CandidateDecisionInputProjection,
)

from app.decision.contracts import (
    DecisionType,
)

from app.decision.external_contract import (
    DecisionResponse,
)


def test_simulation_to_decision_application_flow():

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

    adapter = SimulationDecisionAdapter()

    response = (
        adapter.create_decision(
            projection=projection,
            confidence=0.85,
        )
    )

    assert isinstance(
        response,
        DecisionResponse,
    )

    assert (
        response.decision_type
        == DecisionType.LONG
    )

    assert (
        response.confidence
        == 0.85
    )
