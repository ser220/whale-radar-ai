from dataclasses import dataclass
from datetime import datetime, timezone

from .enums import (
    CandidateDecisionInputStatus,
    CandidateDecisionInputVersion,
)


@dataclass(frozen=True)
class CandidateDecisionInputProjection:
    """Immutable decision input projection."""

    candidate_reference: str
    intelligence_reference: str
    status: CandidateDecisionInputStatus
    version: CandidateDecisionInputVersion
    created_at: datetime

    def __post_init__(self) -> None:
        candidate_reference = (
            self.candidate_reference.strip()
        )

        intelligence_reference = (
            self.intelligence_reference.strip()
        )

        if not candidate_reference:
            raise ValueError(
                "candidate_reference must not be empty"
            )

        if not intelligence_reference:
            raise ValueError(
                "intelligence_reference must not be empty"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )

        object.__setattr__(
            self,
            "candidate_reference",
            candidate_reference,
        )

        object.__setattr__(
            self,
            "intelligence_reference",
            intelligence_reference,
        )

        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(
                timezone.utc
            ),
        )
