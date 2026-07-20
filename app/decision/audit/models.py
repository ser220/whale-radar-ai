from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .enums import DecisionAuditEventType


@dataclass(frozen=True)
class DecisionAuditEvent:
    """
    Immutable audit event for Decision Domain.
    """

    event_id: str
    decision_id: str
    event_type: DecisionAuditEventType
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError(
                "event_id is required"
            )

        if not self.decision_id:
            raise ValueError(
                "decision_id is required"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )

        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(
                timezone.utc
            ),
        )
