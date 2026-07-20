from datetime import datetime, timezone

import pytest

from app.decision.contracts import (
    DecisionContractVersion,
    DecisionRecord,
    DecisionState,
    DecisionType,
)
from app.decision.read_model import (
    DecisionReadModelMapper,
)


def build_record() -> DecisionRecord:
    return DecisionRecord(
        decision_id="decision-001",
        candidate_reference="candidate-001",
        intelligence_reference="intel-001",
        decision_type=DecisionType.LONG,
        decision_state=DecisionState.CREATED,
        confidence=0.85,
        created_at=datetime.now(
            timezone.utc
        ),
        contract_version=DecisionContractVersion.V1,
    )


def test_maps_record_to_read_model():
    record = build_record()

    read_model = (
        DecisionReadModelMapper.from_record(
            record
        )
    )

    assert (
        read_model.decision_id
        == "decision-001"
    )

    assert (
        read_model.decision_type
        == DecisionType.LONG
    )

    assert (
        read_model.decision_state
        == DecisionState.CREATED
    )

    assert (
        read_model.confidence
        == 0.85
    )


def test_read_model_does_not_change_record():
    record = build_record()

    read_model = (
        DecisionReadModelMapper.from_record(
            record
        )
    )

    assert (
        record.decision_state
        == DecisionState.CREATED
    )

    assert (
        read_model.decision_state
        == DecisionState.CREATED
    )


def test_invalid_record_type_rejected():
    with pytest.raises(TypeError):
        DecisionReadModelMapper.from_record(
            "not-a-record"
        )
