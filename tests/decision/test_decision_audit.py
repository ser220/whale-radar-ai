import pytest

from app.decision.audit import (
    DecisionAudit,
    DecisionAuditEventType,
)


def test_record_audit_event():
    audit = DecisionAudit()

    event = audit.record(
        decision_id="decision-001",
        event_type=(
            DecisionAuditEventType.DECISION_CREATED
        ),
    )

    assert (
        event.decision_id
        == "decision-001"
    )

    assert (
        event.event_type
        == DecisionAuditEventType.DECISION_CREATED
    )


def test_get_audit_event():
    audit = DecisionAudit()

    event = audit.record(
        decision_id="decision-001",
        event_type=(
            DecisionAuditEventType.DECISION_APPROVED
        ),
    )

    loaded = audit.get(
        event.event_id
    )

    assert loaded is event


def test_list_events_for_decision():
    audit = DecisionAudit()

    audit.record(
        decision_id="decision-001",
        event_type=(
            DecisionAuditEventType.DECISION_CREATED
        ),
    )

    audit.record(
        decision_id="decision-002",
        event_type=(
            DecisionAuditEventType.DECISION_CREATED
        ),
    )

    events = audit.list_for_decision(
        "decision-001"
    )

    assert len(events) == 1


def test_invalid_event_type_rejected():
    audit = DecisionAudit()

    with pytest.raises(TypeError):
        audit.record(
            decision_id="decision-001",
            event_type="created",
        )
