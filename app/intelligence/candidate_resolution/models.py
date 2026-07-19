from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

from app.intelligence.candidate_resolution.enums import (
    CandidateResolutionType,
    CandidateResolutionReason,
)


@dataclass(frozen=True)
class CandidateResolutionRecord:
    canonical_candidate_id: str
    merged_candidate_ids: Tuple[str, ...]
    resolution_type: CandidateResolutionType
    reason: CandidateResolutionReason
    resolved_at: datetime

    def __post_init__(self):
        if not self.canonical_candidate_id:
            raise ValueError(
                "canonical_candidate_id is required"
            )

        if self.resolved_at.tzinfo is None:
            raise ValueError(
                "resolved_at must be timezone aware"
            )

        if (
            self.resolved_at.utcoffset()
            != timezone.utc.utcoffset(
                self.resolved_at
            )
        ):
            object.__setattr__(
                self,
                "resolved_at",
                self.resolved_at.astimezone(
                    timezone.utc
                ),
            )

        if not isinstance(
            self.merged_candidate_ids,
            tuple,
        ):
            raise TypeError(
                "merged_candidate_ids must be tuple"
            )
