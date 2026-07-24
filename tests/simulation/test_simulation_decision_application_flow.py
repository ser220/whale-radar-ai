from datetime import datetime, timezone
from inspect import signature
from typing import get_type_hints, Optional

from app.simulation import (
    SimulationSnapshot,
    SimulationMarketAdapter,
    SimulationDecisionAdapter,
)

from app.decision.application import (
    DecisionApplicationService,
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


def test_simulation_decision_adapter_constructor_type_hints_resolve(
) -> None:
    type_hints = get_type_hints(
        SimulationDecisionAdapter.__init__
    )
    parameters = signature(
        SimulationDecisionAdapter.__init__
    ).parameters

    assert type_hints[
        "application_service"
    ] == Optional[
        DecisionApplicationService
    ]
    assert (
        parameters[
            "application_service"
        ].default
        is None
    )
    assert type_hints["return"] is type(None)


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


def test_default_service_retrieves_decision_created_through_adapter(
) -> None:
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

    service = DecisionApplicationService()
    adapter = SimulationDecisionAdapter(
        application_service=service,
    )

    created = adapter.create_decision(
        projection=projection,
        confidence=0.85,
    )
    retrieved = service.get_decision(
        created.decision_id
    )

    assert retrieved is not None
    assert retrieved == created
