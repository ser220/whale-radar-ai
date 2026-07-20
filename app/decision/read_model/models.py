from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.decision.contracts import (
    DecisionState,
    DecisionType,
)


@dataclass(frozen=True)
class DecisionReadModel:
    """
    Immutable external representation of DecisionRecord.
    """

    decision_id: str
    decision_type: DecisionType
    decision_state: DecisionState
    confidence: float
    created_at: datetime

    def __post_init__(self) -> None:
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
