from dataclasses import dataclass
from datetime import datetime, timezone

from .enums import (
    CandidateEnvelopeStatus,
    CandidateEnvelopeVersion,
)


@dataclass(frozen=True)
class CandidateIntelligenceEnvelope:
    """Immutable external envelope for candidate projection."""

    envelope_id: str
    candidate_id: str
    projection_reference: str
    status: CandidateEnvelopeStatus
    version: CandidateEnvelopeVersion
    created_at: datetime

    def __post_init__(self) -> None:
        envelope_id = self.envelope_id.strip()
        candidate_id = self.candidate_id.strip()
        projection_reference = (
            self.projection_reference.strip()
        )

        if not envelope_id:
            raise ValueError(
                "envelope_id must not be empty"
            )

        if not candidate_id:
            raise ValueError(
                "candidate_id must not be empty"
            )

        if not projection_reference:
            raise ValueError(
                "projection_reference must not be empty"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )

        object.__setattr__(
            self,
            "envelope_id",
            envelope_id,
        )

        object.__setattr__(
            self,
            "candidate_id",
            candidate_id,
        )

        object.__setattr__(
            self,
            "projection_reference",
            projection_reference,
        )

        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(
                timezone.utc
            ),
        )
