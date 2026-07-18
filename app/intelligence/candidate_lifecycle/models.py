from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.intelligence.candidate_lifecycle.enums import (
    CandidateLifecycleState,
)


@dataclass(frozen=True)
class CandidateLifecycleRecord:
    candidate_id: str
    state: CandidateLifecycleState
    changed_at: datetime
    previous_state: Optional[CandidateLifecycleState] = None
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.candidate_id:
            raise ValueError(
                "candidate_id is required"
            )

        if self.changed_at.tzinfo is None:
            raise ValueError(
                "changed_at must be timezone aware"
            )

        object.__setattr__(
            self,
            "changed_at",
            self.changed_at.astimezone(
                timezone.utc
            ),
        )
