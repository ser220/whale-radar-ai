from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

from .enums import (
    CandidateProjectionStatus,
    CandidateProjectionVersion,
)


@dataclass(frozen=True)
class CandidateIntelligenceProjection:
    """Immutable read-only candidate intelligence projection."""

    candidate_id: str
    lifecycle_state: str
    resolution_state: str
    completeness_state: str
    evidence_reference_ids: Tuple[str, ...]
    attachment_reference_ids: Tuple[str, ...]
    status: CandidateProjectionStatus
    version: CandidateProjectionVersion
    created_at: datetime

    def __post_init__(self) -> None:
        candidate_id = self.candidate_id.strip()

        if not candidate_id:
            raise ValueError(
                "candidate_id must not be empty"
            )

        if self.created_at.tzinfo is None:
            raise ValueError(
                "created_at must be timezone-aware"
            )

        if not isinstance(
            self.evidence_reference_ids,
            tuple,
        ):
            raise TypeError(
                "evidence_reference_ids must be tuple"
            )

        if not isinstance(
            self.attachment_reference_ids,
            tuple,
        ):
            raise TypeError(
                "attachment_reference_ids must be tuple"
            )

        object.__setattr__(
            self,
            "candidate_id",
            candidate_id,
        )

        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(
                timezone.utc
            ),
        )
