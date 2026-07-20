from datetime import datetime, timezone

import pytest

from app.decision.contracts import (
    DecisionContractVersion,
    DecisionRecord,
    DecisionState,
    DecisionType,
)
from app.decision.lifecycle import (
    DecisionLifecycle,
)


def build_record(
    state: DecisionState = DecisionState.CREATED,
) -> DecisionRecord:
    return DecisionRecord(
        decision_id="decision-001",
        candidate_reference="candidate-001",
        intelligence_reference="intel-001",
        decision_type=DecisionType.LONG,
        decision_state=state,
        confidence=0.85,
        created_at=datetime.now(timezone.utc),
        contract_version=DecisionContractVersion.V1,
    )


def test_created_can_be_approved():
    record = build_record()

    approved = DecisionLifecycle.approve(
        record
    )

    assert (
        approved.decision_state
        == DecisionState.APPROVED
    )

    assert (
        record.decision_state
        == DecisionState.CREATED
    )


def test_created_can_be_rejected():
    record = build_record()

    rejected = DecisionLifecycle.reject(
        record
    )

    assert (
        rejected.decision_state
        == DecisionState.REJECTED
    )


def test_approved_cannot_be_approved_again():
    record = build_record(
        DecisionState.APPROVED
    )

    with pytest.raises(ValueError):
        DecisionLifecycle.approve(
            record
        )


def test_rejected_cannot_be_rejected_again():
    record = build_record(
        DecisionState.REJECTED
    )

    with pytest.raises(ValueError):
        DecisionLifecycle.reject(
            record
        )


def test_lifecycle_rejects_invalid_type():
    with pytest.raises(TypeError):
        DecisionLifecycle.approve(
            "not-a-record"
        )
