from datetime import datetime, timezone

from app.decision.audit import (
    DecisionAudit,
)
from app.decision.contracts import (
    DecisionState,
    DecisionType,
)
from app.decision.governance import (
    DecisionGovernance,
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
        created_at=datetime.now(timezone.utc),
    )


def test_create_and_get_decision():
    audit = DecisionAudit()

    governance = DecisionGovernance(
        audit=audit,
    )

    record = governance.create(
        projection=build_projection(),
        decision_type=DecisionType.LONG,
        confidence=0.90,
    )

    loaded = governance.get(
        record.decision_id
    )

    assert loaded is record

    assert (
        loaded.decision_state
        == DecisionState.CREATED
    )

    events = audit.list_for_decision(
        record.decision_id
    )

    assert len(events) == 1


def test_approve_decision():
    audit = DecisionAudit()

    governance = DecisionGovernance(
        audit=audit,
    )

    record = governance.create(
        projection=build_projection(),
        decision_type=DecisionType.LONG,
        confidence=0.90,
    )

    approved = governance.approve(
        record.decision_id
    )

    assert (
        approved.decision_state
        == DecisionState.APPROVED
    )

    events = audit.list_for_decision(
        record.decision_id
    )

    assert len(events) == 2


def test_reject_decision():
    audit = DecisionAudit()

    governance = DecisionGovernance(
        audit=audit,
    )

    record = governance.create(
        projection=build_projection(),
        decision_type=DecisionType.SHORT,
        confidence=0.70,
    )

    rejected = governance.reject(
        record.decision_id
    )

    assert (
        rejected.decision_state
        == DecisionState.REJECTED
    )

    events = audit.list_for_decision(
        record.decision_id
    )

    assert len(events) == 2


def test_missing_decision_rejected():
    governance = DecisionGovernance()

    try:
        governance.approve(
            "unknown-decision"
        )
    except ValueError as error:
        assert (
            str(error)
            == "decision not found"
        )
    else:
        assert False, (
            "ValueError was not raised"
        )
