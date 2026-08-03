from datetime import datetime, timezone

from app.decision.application import (
    DecisionApplicationService,
)

from app.decision.contracts import (
    DecisionType,
)

from app.decision.external_contract import (
    DecisionResponse,
)

from app.decision.governance import (
    DecisionGovernance,
)

from app.decision.query import (
    DecisionQueryService,
)

from app.decision.repository import (
    DecisionRepository,
)

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)

from app.intelligence.candidate_decision_input.early_bird_mapper import (
    EarlyBirdDecisionInputMapper,
)


def build_candidate() -> EarlyBirdCandidate:
    return EarlyBirdCandidate(
        candidate_id="candidate-001",
        asset="BTC",
        observed_at=datetime.now(
            timezone.utc
        ),
        source="early_bird_test",
        quality=80,
        whale_activity_score=70,
        open_interest_change_score=60,
        funding_divergence_score=50,
        volume_expansion_score=75,
        relative_strength_score=65,
        liquidity_event_score=40,
        structure_event_score=55,
        momentum_shift_score=70,
        freshness_score=90,
        data_completeness_score=95,
        fast_event_ids=("event-001",),
        observation_ids=("obs-001",),
        metadata={},
    )


def build_service() -> DecisionApplicationService:
    repository = DecisionRepository()

    governance = DecisionGovernance(
        repository=repository,
    )

    query_service = DecisionQueryService(
        repository=repository,
    )

    return DecisionApplicationService(
        governance=governance,
        query_service=query_service,
    )


def test_early_bird_candidate_creates_decision():

    candidate = build_candidate()

    projection = (
        EarlyBirdDecisionInputMapper()
        .from_candidate(candidate)
    )

    service = build_service()

    response = service.create_decision(
        projection=projection,
        decision_type=DecisionType.LONG,
        confidence=0.85,
    )

    assert isinstance(
        response,
        DecisionResponse,
    )

    assert (
        response.decision_id
        is not None
    )

    assert (
        response.confidence
        == 0.85
    )
