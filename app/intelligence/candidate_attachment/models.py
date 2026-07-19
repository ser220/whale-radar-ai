from dataclasses import dataclass
from datetime import datetime, timezone

from .enums import (
    CandidateAttachmentReferenceVersion,
    CandidateAttachmentType,
)


@dataclass(frozen=True)
class CandidateAttachmentReference:
    """Immutable reference from candidate to external attachment."""

    candidate_id: str
    attachment_id: str
    attachment_type: CandidateAttachmentType
    reference_version: CandidateAttachmentReferenceVersion
    created_at: datetime

    def __post_init__(self) -> None:
        candidate_id = self.candidate_id.strip()
        attachment_id = self.attachment_id.strip()

        if not candidate_id:
            raise ValueError(
                "candidate_id must not be empty"
            )

        if not attachment_id:
            raise ValueError(
                "attachment_id must not be empty"
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
            "attachment_id",
            attachment_id,
        )

        object.__setattr__(
            self,
            "created_at",
            self.created_at.astimezone(
                timezone.utc
            ),
        )
