from dataclasses import dataclass
from datetime import datetime, timezone

from .enums import (
    AssociationReferenceVersion,
    CandidateAssociationType,
)


@dataclass(frozen=True)
class CandidateSituationAssociation:
    """Immutable link between candidate and situation event."""

    candidate_id: str
    situation_event_id: str
    association_type: CandidateAssociationType
    reference_version: AssociationReferenceVersion
    created_at: datetime

    def __post_init__(self) -> None:
        candidate_id = self.candidate_id.strip()
        situation_event_id = self.situation_event_id.strip()

        if not candidate_id:
            raise ValueError(
                "candidate_id must not be empty"
            )

        if not situation_event_id:
            raise ValueError(
                "situation_event_id must not be empty"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )

        object.__setattr__(
            self,
            "candidate_id",
            candidate_id,
        )

        object.__setattr__(
            self,
            "situation_event_id",
            situation_event_id,
        )

        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(
                timezone.utc
            ),
        )
