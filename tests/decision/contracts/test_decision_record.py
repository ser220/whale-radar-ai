from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from app.decision.contracts import (
    DecisionContractVersion,
    DecisionPolicy,
    DecisionRecord,
    DecisionState,
    DecisionType,
)


def build_record(
    **overrides,
) -> DecisionRecord:
    values = {
        "decision_id": "decision-001",
        "candidate_id": "candidate-001",
        "situation_id": "situation-001",
        "decision_type": DecisionType.LONG,
        "decision_state": DecisionState.CREATED,
        "confidence": 0.75,
        "created_at": datetime.now(
            timezone.utc
        ),
        "contract_version": (
            DecisionContractVersion.V1
        ),
    }

    values.update(overrides)

    return DecisionRecord(**values)


def test_valid_decision_record():
    record = build_record()

    assert record.decision_id == "decision-001"
    assert record.confidence == 0.75
    assert (
        DecisionPolicy.validate(record)
        is record
    )


def test_decision_record_is_immutable():
    record = build_record()

    with pytest.raises(FrozenInstanceError):
        record.confidence = 0.9


def test_empty_decision_id_is_rejected():
    with pytest.raises(
        ValueError,
        match="decision_id is required",
    ):
        build_record(
            decision_id="",
        )


def test_confidence_below_zero_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "confidence must be between 0 and 1"
        ),
    ):
        build_record(
            confidence=-0.1,
        )


def test_confidence_above_one_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "confidence must be between 0 and 1"
        ),
    ):
        build_record(
            confidence=1.5,
        )


def test_invalid_decision_type_is_rejected():
    with pytest.raises(
        TypeError,
        match=(
            "decision_type must be DecisionType"
        ),
    ):
        build_record(
            decision_type="long",
        )


def test_naive_created_at_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "created_at must be timezone aware"
        ),
    ):
        build_record(
            created_at=datetime.now(),
        )


def test_policy_rejects_invalid_record():
    with pytest.raises(
        TypeError,
        match="record must be DecisionRecord",
    ):
        DecisionPolicy.validate(
            "not-a-record"
        )
