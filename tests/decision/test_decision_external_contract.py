from datetime import datetime, timezone

import pytest

from app.decision.contracts import (
    DecisionContractVersion,
    DecisionRecord,
    DecisionState,
    DecisionType,
)
from app.decision.external_contract import (
    DecisionResponseMapper,
)


def build_record() -> DecisionRecord:
    return DecisionRecord(
        decision_id="decision-001",
        candidate_reference="candidate-001",
        intelligence_reference="intel-001",
        decision_type=DecisionType.LONG,
        decision_state=DecisionState.CREATED,
        confidence=0.90,
        created_at=datetime.now(
            timezone.utc
        ),
        contract_version=DecisionContractVersion.V1,
    )


def test_maps_record_to_external_contract():
    record = build_record()

    response = (
        DecisionResponseMapper
        .from_record(record)
    )

    assert (
        response.decision_id
        == "decision-001"
    )

    assert (
        response.decision_type
        == DecisionType.LONG
    )

    assert (
        response.decision_state
        == DecisionState.CREATED
    )

    assert (
        response.confidence
        == 0.90
    )


def test_external_contract_does_not_change_domain():
    record = build_record()

    response = (
        DecisionResponseMapper
        .from_record(record)
    )

    assert (
        record.decision_state
        == DecisionState.CREATED
    )

    assert (
        response.decision_state
        == DecisionState.CREATED
    )


def test_invalid_record_type_rejected():
    with pytest.raises(TypeError):
        DecisionResponseMapper.from_record(
            "invalid"
        )
