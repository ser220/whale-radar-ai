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
from app.intelligence.candidate_decision_input.enums import (
    CandidateDecisionInputStatus,
    CandidateDecisionInputVersion,
)
from app.intelligence.candidate_decision_input.models import (
    CandidateDecisionInputProjection,
)


def build_projection() -> CandidateDecisionInputProjection:
    return CandidateDecisionInputProjection(
        candidate_reference="candidate-001",
        intelligence_reference="intel-001",
        status=CandidateDecisionInputStatus.AVAILABLE,
        version=CandidateDecisionInputVersion.V1,
        created_at=datetime.now(
            timezone.utc
        ),
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


def test_create_returns_external_contract():
    service = build_service()

    response = service.create_decision(
        projection=build_projection(),
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


def test_get_returns_external_contract():
    service = build_service()

    created = service.create_decision(
        projection=build_projection(),
        decision_type=DecisionType.LONG,
        confidence=0.85,
    )

    loaded = service.get_decision(
        created.decision_id
    )

    assert isinstance(
        loaded,
        DecisionResponse,
    )

    assert (
        loaded.decision_id
        == created.decision_id
    )


def test_approve_through_application_boundary():
    service = build_service()

    created = service.create_decision(
        projection=build_projection(),
        decision_type=DecisionType.LONG,
        confidence=0.85,
    )

    approved = service.approve_decision(
        created.decision_id
    )

    assert (
        approved.decision_state.value
        == "approved"
    )


def test_unknown_decision_returns_none():
    service = build_service()

    result = service.get_decision(
        "unknown"
    )

    assert result is None
