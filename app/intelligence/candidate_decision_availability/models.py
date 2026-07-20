from dataclasses import dataclass
from datetime import datetime, timezone

from .enums import (
    CandidateDecisionInputAvailabilityStatus,
    CandidateDecisionInputAvailabilityVersion,
)


@dataclass(frozen=True)
class CandidateDecisionInputAvailabilityRecord:
    """Immutable availability record for decision input."""

    input_reference: str
    status: CandidateDecisionInputAvailabilityStatus
    version: CandidateDecisionInputAvailabilityVersion
    checked_at: datetime

    def __post_init__(self) -> None:
        input_reference = self.input_reference.strip()

        if not input_reference:
            raise ValueError(
                "input_reference must not be empty"
            )

        if self.checked_at.tzinfo is None:
            raise ValueError(
                "checked_at must be timezone-aware"
            )

        object.__setattr__(
            self,
            "input_reference",
            input_reference,
        )

        object.__setattr__(
            self,
            "checked_at",
            self.checked_at.astimezone(
                timezone.utc
            ),
        )
