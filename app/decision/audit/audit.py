from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from .enums import DecisionAuditEventType
from .models import DecisionAuditEvent


class DecisionAudit:
    """
    Immutable audit event recorder.

    Stores audit events only.
    No decision logic allowed.
    """

    def __init__(self) -> None:
        self._events: Dict[
            str,
            DecisionAuditEvent,
        ] = {}

    def record(
        self,
        decision_id: str,
        event_type: DecisionAuditEventType,
    ) -> DecisionAuditEvent:
        if not isinstance(
            event_type,
            DecisionAuditEventType,
        ):
            raise TypeError(
                "event_type must be DecisionAuditEventType"
            )

        event = DecisionAuditEvent(
            event_id=(
                f"audit-{len(self._events) + 1}"
            ),
            decision_id=decision_id,
            event_type=event_type,
            created_at=datetime.now(
                timezone.utc
            ),
        )

        self._events[
            event.event_id
        ] = event

        return event

    def get(
        self,
        event_id: str,
    ) -> DecisionAuditEvent | None:
        return self._events.get(
            event_id
        )

    def list_for_decision(
        self,
        decision_id: str,
    ) -> List[DecisionAuditEvent]:
        return [
            event
            for event in self._events.values()
            if event.decision_id == decision_id
        ]
