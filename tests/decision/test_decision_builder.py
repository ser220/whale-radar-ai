from datetime import datetime, timezone

from app.decision.builder import DecisionBuilder
from app.decision.contracts import (
    DecisionState,
    DecisionType,
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
        candidate_reference="candidate-1",
        intelligence_reference="intel-1",
        status=CandidateDecisionInputStatus.AVAILABLE,
        version=CandidateDecisionInputVersion.V1,
        created_at=datetime.now(timezone.utc),
    )


def test_build_decision_record() -> None:
    builder = DecisionBuilder()

    record = builder.build(
        projection=build_projection(),
        decision_type=DecisionType.LONG,
        confidence=0.80,
    )

    assert record.candidate_reference == "candidate-1"
    assert record.intelligence_reference == "intel-1"
    assert record.decision_state == DecisionState.CREATED
    assert record.decision_type == DecisionType.LONG
    assert record.confidence == 0.80
    assert record.decision_id.startswith("decision-")


def test_builder_is_deterministic() -> None:
    projection = build_projection()
    builder = DecisionBuilder()

    first = builder.build(
        projection=projection,
        decision_type=DecisionType.LONG,
        confidence=0.80,
    )

    second = builder.build(
        projection=projection,
        decision_type=DecisionType.LONG,
        confidence=0.80,
        created_at=first.created_at,
    )

    assert first.decision_id == second.decision_id
