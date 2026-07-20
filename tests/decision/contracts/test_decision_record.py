from datetime import datetime, timezone

import pytest

from app.decision.contracts import (
    DecisionContractVersion,
    DecisionPolicy,
    DecisionRecord,
    DecisionState,
    DecisionType,
)


def build_record(**overrides):
    data = {
        "decision_id": "decision-1",
        "candidate_reference": "candidate-1",
        "intelligence_reference": "intel-1",
        "decision_type": DecisionType.LONG,
        "decision_state": DecisionState.CREATED,
        "confidence": 0.75,
        "created_at": datetime.now(timezone.utc),
        "contract_version": (
            DecisionContractVersion.V1
        ),
    }

    data.update(overrides)

    return DecisionRecord(**data)


def test_create_valid_record():
    record = build_record()

    assert (
        record.decision_id == "decision-1"
    )

    assert (
        record.candidate_reference
        == "candidate-1"
    )

    assert (
        record.intelligence_reference
        == "intel-1"
    )


def test_record_is_frozen():
    record = build_record()

    with pytest.raises(Exception):
        record.confidence = 0.5


def test_empty_candidate_reference():
    with pytest.raises(ValueError):
        build_record(
            candidate_reference=""
        )


def test_confidence_below_zero():
    with pytest.raises(ValueError):
        build_record(confidence=-0.1)


def test_confidence_above_one():
    with pytest.raises(ValueError):
        build_record(confidence=1.1)


def test_invalid_decision_type():
    with pytest.raises(TypeError):
        build_record(
            decision_type="LONG"
        )


def test_naive_datetime():
    with pytest.raises(ValueError):
        build_record(
            created_at=datetime.now()
        )


def test_policy_validation():
    record = build_record()

    validated = (
        DecisionPolicy.validate(record)
    )

    assert validated is record
