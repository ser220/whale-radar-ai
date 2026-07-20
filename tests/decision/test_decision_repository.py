from datetime import datetime, timezone

from app.decision.contracts import (
    DecisionContractVersion,
    DecisionRecord,
    DecisionState,
    DecisionType,
)
from app.decision.repository import (
    DecisionRepository,
)


def build_record() -> DecisionRecord:
    return DecisionRecord(
        decision_id="decision-001",
        candidate_reference="candidate-001",
        intelligence_reference="intel-001",
        decision_type=DecisionType.LONG,
        decision_state=DecisionState.CREATED,
        confidence=0.85,
        created_at=datetime.now(timezone.utc),
        contract_version=DecisionContractVersion.V1,
    )


def test_save_and_get_record():
    repository = DecisionRepository()

    record = build_record()

    saved = repository.save(record)

    loaded = repository.get(
        "decision-001"
    )

    assert saved is record
    assert loaded is record


def test_repository_checks_existence():
    repository = DecisionRepository()

    record = build_record()

    assert (
        repository.exists(
            "decision-001"
        )
        is False
    )

    repository.save(record)

    assert (
        repository.exists(
            "decision-001"
        )
        is True
    )


def test_repository_rejects_invalid_record():
    repository = DecisionRepository()

    try:
        repository.save(
            "not-a-decision-record"
        )
    except TypeError as error:
        assert (
            str(error)
            == "record must be DecisionRecord"
        )
    else:
        assert False, (
            "TypeError was not raised"
        )
